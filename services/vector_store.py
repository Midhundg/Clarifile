"""Persistent vector store implementation using ChromaDB."""

import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from services.chunking import DocumentChunk
from utils.config import Config


class VectorStoreError(Exception):
    """Exception raised when vector database operations fail."""
    pass


class VectorStore:
    """Manages persistent document embeddings, indexing, and vector similarity search with ChromaDB."""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = Config.CHROMA_COLLECTION_NAME,
    ):
        self.persist_dir = str(persist_directory or Config.CHROMA_PERSIST_DIR)
        self.collection_name = collection_name
        os.makedirs(self.persist_dir, exist_ok=True)
        self._init_client()

    def _init_client(self) -> None:
        """Initialize persistent ChromaDB client and collection."""
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )
            # Create or get collection with cosine distance metric
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            raise VectorStoreError(f"Failed to initialize ChromaDB at '{self.persist_dir}': {str(e)}") from e

    def document_exists(self, doc_id: str) -> bool:
        """Check if document chunks for doc_id are already indexed."""
        try:
            existing = self.collection.get(
                where={"doc_id": doc_id},
                limit=1,
            )
            return bool(existing and existing["ids"])
        except Exception:
            return False

    def add_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
    ) -> int:
        """Add document chunks and their pre-computed embeddings to ChromaDB.

        Args:
            chunks: List of DocumentChunk instances.
            embeddings: List of embedding vectors matching chunks.

        Returns:
            Number of indexed chunks.
        """
        if not chunks:
            return 0

        if len(chunks) != len(embeddings):
            raise VectorStoreError(
                f"Mismatch between chunks count ({len(chunks)}) and embeddings count ({len(embeddings)})."
            )

        doc_id = chunks[0].doc_id

        # If document already exists, remove previous chunks first to avoid duplication
        if self.document_exists(doc_id):
            self.delete_document(doc_id)

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [
            {
                "doc_id": chunk.doc_id,
                "file_name": chunk.file_name,
                "file_type": chunk.file_type,
                "page_number": str(chunk.page_number),
                "chunk_index": int(chunk.chunk_index),
                "char_count": int(chunk.char_count),
                "word_count": int(chunk.word_count),
            }
            for chunk in chunks
        ]

        try:
            # Batch upsert in groups of 250 for optimal performance
            batch_size = 250
            for i in range(0, len(ids), batch_size):
                self.collection.upsert(
                    ids=ids[i : i + batch_size],
                    embeddings=embeddings[i : i + batch_size],
                    documents=documents[i : i + batch_size],
                    metadatas=metadatas[i : i + batch_size],
                )
            return len(chunks)
        except Exception as e:
            raise VectorStoreError(f"Failed to store chunks in ChromaDB: {str(e)}") from e

    def query(
        self,
        query_embedding: List[float],
        top_k: int = Config.DEFAULT_TOP_K,
        doc_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Perform semantic similarity search against the indexed chunks.

        Args:
            query_embedding: Embedding vector for the search query.
            top_k: Maximum number of chunks to retrieve.
            doc_id: Optional specific document ID to restrict search.

        Returns:
            Dictionary with 'ids', 'distances', 'metadatas', and 'documents'.
        """
        try:
            total_count = self.collection.count()
            if total_count == 0:
                return {"ids": [[]], "distances": [[]], "metadatas": [[]], "documents": [[]]}

            effective_k = min(top_k, total_count)
            where_filter = {"doc_id": doc_id} if doc_id else None

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=effective_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
            return results
        except Exception as e:
            raise VectorStoreError(f"Vector search query failed: {str(e)}") from e

    def delete_document(self, doc_id: str) -> int:
        """Delete all chunks and vectors associated with a document ID.

        Args:
            doc_id: Unique document ID to remove.

        Returns:
            Number of deleted chunks.
        """
        try:
            existing = self.collection.get(where={"doc_id": doc_id})
            if existing and existing["ids"]:
                chunk_ids = existing["ids"]
                self.collection.delete(ids=chunk_ids)
                return len(chunk_ids)
            return 0
        except Exception as e:
            raise VectorStoreError(f"Failed to delete document '{doc_id}' from vector store: {str(e)}") from e

    def get_indexed_documents(self) -> List[Dict[str, Any]]:
        """Retrieve a summary of all unique documents currently stored in ChromaDB."""
        try:
            all_records = self.collection.get(include=["metadatas"])
            if not all_records or not all_records["metadatas"]:
                return []

            docs_map: Dict[str, Dict[str, Any]] = {}
            for meta in all_records["metadatas"]:
                doc_id = meta.get("doc_id")
                if not doc_id:
                    continue

                if doc_id not in docs_map:
                    docs_map[doc_id] = {
                        "doc_id": doc_id,
                        "file_name": meta.get("file_name", "Unknown"),
                        "file_type": meta.get("file_type", ""),
                        "chunk_count": 0,
                        "total_chars": 0,
                    }

                docs_map[doc_id]["chunk_count"] += 1
                docs_map[doc_id]["total_chars"] += meta.get("char_count", 0)

            return list(docs_map.values())
        except Exception as e:
            raise VectorStoreError(f"Failed to list indexed documents: {str(e)}") from e

    def get_total_chunks(self) -> int:
        """Get the total count of chunks in the collection."""
        try:
            return self.collection.count()
        except Exception:
            return 0

    def clear_all(self) -> None:
        """Reset the vector database collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            raise VectorStoreError(f"Failed to reset vector database: {str(e)}") from e
