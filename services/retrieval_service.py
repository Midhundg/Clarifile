"""Hybrid Retrieval Engine combining Dense Semantic Vectors with BM25 Lexical Matching."""

import re
from dataclasses import dataclass
from typing import List, Optional, Any, Dict
from services.embedding_service import EmbeddingService
from services.vector_store import VectorStore
from services.bm25_service import BM25Scorer
from utils.config import Config


@dataclass
class RetrievalResult:
    """Represents a retrieved document chunk with relevance scoring and source metadata."""
    chunk_id: str
    doc_id: str
    file_name: str
    file_type: str
    page_number: Any
    chunk_index: int
    text: str
    score: float  # Hybrid relevance score between 0.0 and 1.0


class RetrievalService:
    """Orchestrates Hybrid (Dense + BM25 Lexical) semantic retrieval with intent boosting."""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        self.vector_store = vector_store or VectorStore()
        self.embedding_service = embedding_service or EmbeddingService.get_instance()

    def retrieve(
        self,
        query: str,
        top_k: int = Config.DEFAULT_TOP_K,
        similarity_threshold: float = Config.SIMILARITY_THRESHOLD,
        doc_id: Optional[str] = None,
    ) -> List[RetrievalResult]:
        """Perform hybrid retrieval combining vector similarity with BM25 keyword matching.

        Args:
            query: The user search question.
            top_k: Maximum number of chunks to return.
            similarity_threshold: Minimum combined score (0.0 to 1.0) to include a chunk.
            doc_id: Optional specific document ID to filter search scope.

        Returns:
            List of RetrievalResult objects sorted by highest relevance.
        """
        clean_query = query.strip() if query else ""
        if not clean_query:
            return []

        # 1. Fetch candidate pool from ChromaDB (all chunks for doc_id or top 50 globally)
        where_filter = {"doc_id": doc_id} if doc_id else None
        try:
            pool = self.vector_store.collection.get(
                where=where_filter,
                include=["documents", "metadatas"],
            )
        except Exception:
            pool = None

        if not pool or not pool["ids"]:
            return []

        all_ids = pool["ids"]
        all_docs = pool["documents"]
        all_metas = pool["metadatas"]
        total_chunks = len(all_ids)

        # 2. Dense Semantic Vector Search
        query_embedding = self.embedding_service.embed_query(clean_query)
        dense_raw = self.vector_store.query(
            query_embedding=query_embedding,
            top_k=min(total_chunks, 50),
            doc_id=doc_id,
        )

        dense_scores: Dict[str, float] = {}
        if dense_raw and dense_raw.get("ids") and dense_raw["ids"][0]:
            d_ids = dense_raw["ids"][0]
            d_distances = dense_raw.get("distances", [[]])[0]
            for c_id, dist in zip(d_ids, d_distances):
                # Cosine distance to similarity: 1 - dist
                dense_scores[c_id] = max(0.0, min(1.0, 1.0 - dist))

        # 3. Sparse BM25 Lexical Search
        bm25 = BM25Scorer(all_docs)
        bm25_raw_scores = bm25.score_query(clean_query)
        max_bm25 = max(bm25_raw_scores) if bm25_raw_scores and max(bm25_raw_scores) > 0 else 0.0

        # 4. Intent & Entity Detection
        q_lower = clean_query.lower()

        # Identity / Name / Who / Author
        is_name_query = any(
            re.search(rf"\b{w}\b", q_lower)
            for w in ["name", "who", "candidate", "person", "author", "creator", "identity", "whose"]
        )

        # Contact / Email / Phone / Location
        is_contact_query = any(
            re.search(rf"\b{w}\b", q_lower)
            for w in ["email", "mail", "phone", "contact", "mobile", "call", "reach", "number", "address", "location"]
        )

        # Skills / Tech Stack
        is_skill_query = any(
            re.search(rf"\b{w}\b", q_lower)
            for w in ["skill", "skills", "technologies", "technology", "programming", "languages", "tools", "stack"]
        )

        # Projects / Work / Experience
        is_project_query = any(
            re.search(rf"\b{w}\b", q_lower)
            for w in ["project", "projects", "built", "developed", "experience", "work", "portfolio", "achievements"]
        )

        # Summary / Overview
        is_overview_query = any(
            re.search(rf"\b{w}\b", q_lower)
            for w in ["summary", "overview", "about", "describe", "introduction", "background"]
        )

        # 5. Hybrid Score Calculation & Reciprocal Fusion
        candidates: List[RetrievalResult] = []

        for i, (chunk_id, doc_text, meta) in enumerate(zip(all_ids, all_docs, all_metas)):
            dense_sim = dense_scores.get(chunk_id, 0.05)
            bm25_norm = (bm25_raw_scores[i] / max_bm25) if max_bm25 > 0 else 0.0

            # Base hybrid weighted combination: 55% Dense Semantic + 45% Sparse BM25
            hybrid_score = (0.55 * dense_sim) + (0.45 * bm25_norm)

            chunk_idx = int(meta.get("chunk_index", 0))

            # Header Chunk Prioritization:
            # Chunk 0 contains document title, author name, contact details, and executive summary
            if chunk_idx == 0:
                if is_name_query:
                    hybrid_score += 0.45
                if is_contact_query:
                    hybrid_score += 0.40
                if is_overview_query:
                    hybrid_score += 0.25

            # Entity feature boosts:
            if is_contact_query:
                # Direct check for email or phone patterns
                if re.search(r"[\w\.-]+@[\w\.-]+\.\w+", doc_text):
                    hybrid_score += 0.30
                if re.search(r"\+?\d[\d -]{8,}\d", doc_text):
                    hybrid_score += 0.25

            if is_skill_query:
                if any(w in doc_text.lower() for w in ["skills", "languages", "technologies", "proficiencies", "tools"]):
                    hybrid_score += 0.25

            if is_project_query:
                if any(w in doc_text.lower() for w in ["project", "developed", "implemented", "built", "github"]):
                    hybrid_score += 0.20

            final_score = min(1.0, max(0.0, round(hybrid_score, 4)))

            if final_score >= similarity_threshold:
                candidates.append(
                    RetrievalResult(
                        chunk_id=chunk_id,
                        doc_id=meta.get("doc_id", ""),
                        file_name=meta.get("file_name", "Unknown"),
                        file_type=meta.get("file_type", ""),
                        page_number=meta.get("page_number", "1"),
                        chunk_index=chunk_idx,
                        text=doc_text,
                        score=final_score,
                    )
                )

        # Sort descending by hybrid relevance score
        candidates.sort(key=lambda r: r.score, reverse=True)
        return candidates[:top_k]
