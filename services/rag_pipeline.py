"""End-to-end RAG (Retrieval-Augmented Generation) Pipeline for Clarifile."""

from dataclasses import dataclass, field
from typing import List, Optional
from services.retrieval_service import RetrievalService, RetrievalResult
from services.llm_service import BaseLLMService, GeminiLLMService, LLMError, MissingAPIKeyError
from utils.config import Config


@dataclass
class RAGResponse:
    """Encapsulates the response from the RAG pipeline."""
    question: str
    answer: str
    sources: List[RetrievalResult] = field(default_factory=list)
    has_context: bool = False
    error: Optional[str] = None

    @property
    def source_documents(self) -> List[str]:
        """Return list of distinct source document names used."""
        return list({s.file_name for s in self.sources})


class RAGPipeline:
    """Coordinates semantic retrieval and LLM generation to produce grounded answers."""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        llm_service: Optional[BaseLLMService] = None,
    ):
        self.retrieval_service = retrieval_service or RetrievalService()
        self.llm_service = llm_service or GeminiLLMService()

    def set_llm_service(self, llm_service: BaseLLMService) -> None:
        """Update or swap the active LLM service instance."""
        self.llm_service = llm_service

    def answer_question(
        self,
        question: str,
        doc_id: Optional[str] = None,
        top_k: int = Config.DEFAULT_TOP_K,
        similarity_threshold: float = Config.SIMILARITY_THRESHOLD,
    ) -> RAGResponse:
        """Answer a question using retrieved document context.

        Args:
            question: The user inquiry.
            doc_id: Optional document ID to filter search scope.
            top_k: Maximum chunks to retrieve.
            similarity_threshold: Minimum cosine similarity score.

        Returns:
            RAGResponse containing answer and verified source citations.
        """
        clean_question = question.strip() if question else ""
        if not clean_question:
            return RAGResponse(
                question=question,
                answer="Please enter a question to analyze your documents.",
                has_context=False,
            )

        # 1. Retrieve relevant chunks
        try:
            retrieved_chunks = self.retrieval_service.retrieve(
                query=clean_question,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                doc_id=doc_id,
            )
        except Exception as e:
            return RAGResponse(
                question=clean_question,
                answer=f"Error during document retrieval: {str(e)}",
                has_context=False,
                error=str(e),
            )

        # 2. Check if relevant context was found
        if not retrieved_chunks:
            # Check if candidates exist below threshold to give actionable diagnostic guidance
            raw_candidates = self.retrieval_service.retrieve(
                query=clean_question,
                top_k=top_k,
                similarity_threshold=0.0,
                doc_id=doc_id,
            )
            if raw_candidates and similarity_threshold > 0.0:
                top_score = raw_candidates[0].score
                return RAGResponse(
                    question=clean_question,
                    answer=(
                        f"⚠️ **Similarity Threshold Filter**: No passages passed your **Similarity Threshold of {similarity_threshold:.2f}**.\n\n"
                        f"- The highest candidate score found was **{top_score:.1%}**.\n"
                        f"- **Fix**: In **Retrieval & Search Settings** above, lower the **Similarity Threshold slider** (e.g. to **{min(0.10, top_score):.2f}** or **0.05**) and try again."
                    ),
                    sources=[],
                    has_context=False,
                )

            return RAGResponse(
                question=clean_question,
                answer="The information was not found in the uploaded documents. Please ensure your documents are indexed or try rephrasing your question.",
                sources=[],
                has_context=False,
            )

        # 3. Construct context block with explicit source citations
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, start=1):
            page_info = f"Page {chunk.page_number}" if str(chunk.page_number).isdigit() else f"Section: {chunk.page_number}"
            context_parts.append(
                f"[Source {i} | File: {chunk.file_name} | {page_info}]\n{chunk.text}"
            )
        context_block = "\n\n---\n\n".join(context_parts)

        # 4. Construct prompt
        prompt = (
            f"Retrieved Document Context:\n"
            f"============================\n"
            f"{context_block}\n"
            f"============================\n\n"
            f"User Question: {clean_question}\n\n"
            f"Instructions:\n"
            f"- Answer the question using ONLY the retrieved document context above.\n"
            f"- If the answer is unavailable in the retrieved context, state clearly: 'The information was not found in the uploaded documents.'\n"
            f"- Identify and reference the exact source documents and pages/sections used."
        )

        # 5. Call LLM
        try:
            answer = self.llm_service.generate(
                prompt=prompt,
                system_instruction=Config.SYSTEM_INSTRUCTION,
                temperature=0.2,
            )
            return RAGResponse(
                question=clean_question,
                answer=answer,
                sources=retrieved_chunks,
                has_context=True,
            )
        except MissingAPIKeyError:
            # Fallback to intelligent rule-based extraction from top retrieved chunks
            offline_answer = self._extract_offline_answer(clean_question, retrieved_chunks)
            return RAGResponse(
                question=clean_question,
                answer=offline_answer,
                sources=retrieved_chunks,
                has_context=True,
                error="MISSING_API_KEY",
            )
        except LLMError as e:
            err_msg = str(e)
            if "nodename nor servname" in err_msg or "Failed to resolve" in err_msg or "Connection" in err_msg:
                offline_answer = self._extract_offline_answer(clean_question, retrieved_chunks)
                friendly_answer = (
                    f"{offline_answer}\n\n"
                    f"*(Notice: Direct synthesis offline due to network connection. Extracted directly from cited passages.)*"
                )
                return RAGResponse(
                    question=clean_question,
                    answer=friendly_answer,
                    sources=retrieved_chunks,
                    has_context=True,
                    error="NETWORK_ERROR",
                )
            return RAGResponse(
                question=clean_question,
                answer=f"⚠️ AI Service Notice: {err_msg}",
                sources=retrieved_chunks,
                has_context=True,
                error=err_msg,
            )

    def _extract_offline_answer(self, question: str, chunks: List[RetrievalResult]) -> str:
        """Rule-based answer extraction from retrieved passages when LLM is unconfigured."""
        import re
        if not chunks:
            return "No relevant information found in documents."

        top_chunk = chunks[0]
        text = top_chunk.text
        q_lower = question.lower()

        # 1. Name / Identity extraction
        if any(w in q_lower for w in ["name", "who", "candidate", "author", "person"]):
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            for line in lines[:4]:
                first_part = line.split("/")[0].split("—")[0].strip()
                if 2 < len(first_part) < 60 and not any(k in first_part.lower() for k in ["http", "www", "resume", "page"]):
                    return (
                        f"**{first_part}**\n\n"
                        f"*(Extracted from `{top_chunk.file_name}`, Page {top_chunk.page_number} via semantic search)*"
                    )

        # 2. Email extraction
        if "email" in q_lower or "mail" in q_lower:
            for chunk in chunks:
                match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", chunk.text)
                if match:
                    return (
                        f"**Email:** `{match.group()}`\n\n"
                        f"*(Found in `{chunk.file_name}`, Page {chunk.page_number})*"
                    )

        # 3. Phone extraction
        if any(w in q_lower for w in ["phone", "contact", "mobile", "number"]):
            for chunk in chunks:
                match = re.search(r"\+?\d[\d -]{8,}\d", chunk.text)
                if match:
                    return (
                        f"**Phone / Contact:** `{match.group()}`\n\n"
                        f"*(Found in `{chunk.file_name}`, Page {chunk.page_number})*"
                    )

        # 4. Keyword sentence extraction
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 15]
        q_words = [w for w in re.findall(r"\b\w{3,}\b", q_lower) if w not in {"what", "the", "and", "for", "with"}]
        best_sentence = ""
        max_matches = 0
        for s in sentences:
            matches = sum(1 for w in q_words if w in s.lower())
            if matches > max_matches:
                max_matches = matches
                best_sentence = s

        if best_sentence:
            return (
                f"**{best_sentence.strip()}.**\n\n"
                f"*(Extracted from `{top_chunk.file_name}`, Page {top_chunk.page_number})*"
            )

        return (
            f"Relevant passage from `{top_chunk.file_name}` (Page {top_chunk.page_number}):\n\n"
            f"> {text[:350]}..."
        )
