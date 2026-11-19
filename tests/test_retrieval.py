"""Unit and integration tests for EmbeddingService, VectorStore, and RetrievalService."""

import shutil
import pytest
from services.embedding_service import EmbeddingService
from services.vector_store import VectorStore
from services.retrieval_service import RetrievalService
from services.chunking import DocumentChunk


@pytest.fixture
def temp_vector_store(tmp_path):
    """Fixture providing an isolated temporary ChromaDB vector store."""
    db_path = str(tmp_path / "test_chroma_db")
    store = VectorStore(persist_directory=db_path, collection_name="test_collection")
    yield store
    # Cleanup
    shutil.rmtree(db_path, ignore_errors=True)


def test_embedding_generation():
    """Verify that EmbeddingService generates 384-dimensional normalized vectors."""
    service = EmbeddingService.get_instance()
    texts = ["Clarifile artificial intelligence document analyzer", "Vector database retrieval"]

    embeddings = service.embed_texts(texts)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    assert len(embeddings[1]) == 384

    # Single query embedding
    query_emb = service.embed_query("document analysis")
    assert len(query_emb) == 384


def test_vector_store_add_and_query(temp_vector_store):
    """Verify storing chunks in ChromaDB and querying by embedding."""
    service = EmbeddingService.get_instance()

    chunks = [
        DocumentChunk(
            chunk_id="doc1_c0",
            doc_id="doc1",
            file_name="quarterly_report.pdf",
            file_type="pdf",
            page_number=1,
            chunk_index=0,
            text="The company generated 50 million dollars in gross revenue during Q3.",
        ),
        DocumentChunk(
            chunk_id="doc1_c1",
            doc_id="doc1",
            file_name="quarterly_report.pdf",
            file_type="pdf",
            page_number=2,
            chunk_index=1,
            text="Customer satisfaction reached 94 percent across all enterprise accounts.",
        ),
        DocumentChunk(
            chunk_id="doc2_c0",
            doc_id="doc2",
            file_name="hardware_manual.txt",
            file_type="txt",
            page_number=1,
            chunk_index=0,
            text="To reboot the server rack, press and hold the power switch for five seconds.",
        ),
    ]

    embeddings = service.embed_texts([c.text for c in chunks])
    indexed_count = temp_vector_store.add_chunks(chunks, embeddings)
    assert indexed_count == 3
    assert temp_vector_store.get_total_chunks() == 3

    # Semantic query for revenue
    query_emb = service.embed_query("financial revenue earnings")
    results = temp_vector_store.query(query_emb, top_k=2)

    retrieved_docs = results["documents"][0]
    assert len(retrieved_docs) >= 1
    assert "gross revenue" in retrieved_docs[0]


def test_retrieval_service_filtering_and_scoring(temp_vector_store):
    """Verify RetrievalService returns scored results and supports document-specific filtering."""
    service = EmbeddingService.get_instance()
    retrieval_service = RetrievalService(vector_store=temp_vector_store, embedding_service=service)

    chunks = [
        DocumentChunk(
            chunk_id="alpha_c0",
            doc_id="doc_alpha",
            file_name="alpha_spec.pdf",
            file_type="pdf",
            page_number=1,
            chunk_index=0,
            text="Alpha system implements neural semantic search and vector embeddings.",
        ),
        DocumentChunk(
            chunk_id="beta_c0",
            doc_id="doc_beta",
            file_name="beta_spec.pdf",
            file_type="pdf",
            page_number=3,
            chunk_index=0,
            text="Beta system focuses on distributed caching and database indexing.",
        ),
    ]
    embeddings = service.embed_texts([c.text for c in chunks])
    temp_vector_store.add_chunks(chunks, embeddings)

    # 1. Global search
    global_results = retrieval_service.retrieve(query="neural semantic search", top_k=2, similarity_threshold=0.1)
    assert len(global_results) >= 1
    assert global_results[0].doc_id == "doc_alpha"
    assert global_results[0].score > 0.3
    assert global_results[0].page_number == "1"

    # 2. Filtered search to doc_beta only
    beta_only_results = retrieval_service.retrieve(
        query="neural semantic search",
        doc_id="doc_beta",
        top_k=2,
        similarity_threshold=0.0,
    )
    assert len(beta_only_results) == 1
    assert beta_only_results[0].doc_id == "doc_beta"


def test_document_deletion_from_vector_store(temp_vector_store):
    """Verify that deleting a document cleans up all associated vectors in ChromaDB."""
    service = EmbeddingService.get_instance()

    chunks = [
        DocumentChunk(
            chunk_id="del_c0",
            doc_id="doc_to_delete",
            file_name="obsolete.txt",
            file_type="txt",
            page_number=1,
            chunk_index=0,
            text="Obsolete document content to be completely deleted.",
        ),
        DocumentChunk(
            chunk_id="keep_c0",
            doc_id="doc_to_keep",
            file_name="important.txt",
            file_type="txt",
            page_number=1,
            chunk_index=0,
            text="Retained document content that should remain indexed.",
        ),
    ]
    embeddings = service.embed_texts([c.text for c in chunks])
    temp_vector_store.add_chunks(chunks, embeddings)
    assert temp_vector_store.get_total_chunks() == 2

    # Delete doc_to_delete
    deleted = temp_vector_store.delete_document("doc_to_delete")
    assert deleted == 1
    assert temp_vector_store.get_total_chunks() == 1
    assert not temp_vector_store.document_exists("doc_to_delete")
    assert temp_vector_store.document_exists("doc_to_keep")
