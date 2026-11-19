"""End-to-end RAG pipeline, AI features, and citation verification tests using mocked LLM."""

import pytest
from services.rag_pipeline import RAGPipeline
from services.llm_service import MockLLMService, GeminiLLMService
from services.retrieval_service import RetrievalService
from services.embedding_service import EmbeddingService
from services.vector_store import VectorStore
from services.chunking import DocumentChunk
from services.summarization_service import SummarizationService
from services.keypoint_service import KeyPointService
from services.keyword_service import KeywordService
from services.comparison_service import ComparisonService


@pytest.fixture
def rag_test_setup(tmp_path):
    """Fixture providing initialized VectorStore, RetrievalService, and MockLLM."""
    db_path = str(tmp_path / "rag_chroma")
    store = VectorStore(persist_directory=db_path, collection_name="rag_tests")
    embedder = EmbeddingService.get_instance()

    chunks = [
        DocumentChunk(
            chunk_id="tech_c0",
            doc_id="tech_doc",
            file_name="cloud_infrastructure.pdf",
            file_type="pdf",
            page_number=4,
            chunk_index=0,
            text="The multi-region failover architecture achieves 99.999% SLA availability.",
        ),
        DocumentChunk(
            chunk_id="tech_c1",
            doc_id="tech_doc",
            file_name="cloud_infrastructure.pdf",
            file_type="pdf",
            page_number=5,
            chunk_index=1,
            text="Automated database replication synchronizes across three availability zones.",
        ),
    ]
    embeddings = embedder.embed_texts([c.text for c in chunks])
    store.add_chunks(chunks, embeddings)

    retrieval_service = RetrievalService(vector_store=store, embedding_service=embedder)
    mock_llm = MockLLMService(
        default_response="According to cloud_infrastructure.pdf (Page 4), the SLA availability is 99.999%."
    )
    pipeline = RAGPipeline(retrieval_service=retrieval_service, llm_service=mock_llm)

    return pipeline, store, mock_llm


def test_rag_question_answering_and_citations(rag_test_setup):
    """Verify that RAG generates answers grounded in context with accurate source citations."""
    pipeline, _, mock_llm = rag_test_setup

    response = pipeline.answer_question("What is the SLA availability?", similarity_threshold=0.2)

    assert response.has_context is True
    assert "99.999%" in response.answer
    assert len(response.sources) >= 1

    # Verify source citation mapping
    top_source = response.sources[0]
    assert top_source.file_name == "cloud_infrastructure.pdf"
    assert top_source.page_number == "4" or top_source.page_number == 4
    assert "99.999% SLA" in top_source.text
    assert response.source_documents == ["cloud_infrastructure.pdf"]


def test_rag_insufficient_context(rag_test_setup):
    """Verify that when no chunks meet the similarity threshold, Clarifile states information not found."""
    pipeline, _, _ = rag_test_setup

    # Ask completely unrelated query with high threshold
    response = pipeline.answer_question(
        "What is the average rainfall in the Amazon rainforest in November?",
        similarity_threshold=0.85,
    )

    assert response.has_context is False
    assert ("information was not found" in response.answer.lower() or "threshold" in response.answer.lower())
    assert len(response.sources) == 0


def test_rag_missing_api_key_handling(tmp_path):
    """Verify that a missing API key is handled gracefully without crashing."""
    db_path = str(tmp_path / "missing_key_db")
    store = VectorStore(persist_directory=db_path)
    embedder = EmbeddingService.get_instance()
    retrieval_service = RetrievalService(vector_store=store, embedding_service=embedder)

    # Empty API key
    gemini_service = GeminiLLMService(api_key="")
    pipeline = RAGPipeline(retrieval_service=retrieval_service, llm_service=gemini_service)

    # Add chunk so context exists
    chunk = DocumentChunk(
        chunk_id="c1",
        doc_id="d1",
        file_name="test.txt",
        file_type="txt",
        page_number=1,
        chunk_index=0,
        text="Sample test content",
    )
    store.add_chunks([chunk], embedder.embed_texts([chunk.text]))

    response = pipeline.answer_question("Sample test content", similarity_threshold=0.0)
    assert response.error == "MISSING_API_KEY"


def test_summarization_service():
    """Verify multi-tier summarization with both LLM and fallback modes."""
    sample_text = (
        "Project Orion is a next-generation data lake initiative. "
        "It reduced data ingestion latency from 45 minutes to 30 seconds. "
        "The team approved the migration to Apache Iceberg format. "
        "The scheduled rollout date is October 15, 2026."
    )

    # 1. Mock LLM summarization
    mock_llm = MockLLMService(
        default_response=(
            "### SHORT SUMMARY\nProject Orion is a high-speed data lake initiative.\n\n"
            "### DETAILED SUMMARY\nReduced ingestion latency to 30s using Iceberg.\n\n"
            "### IMPORTANT OBSERVATIONS\n- Significant latency improvement.\n- Migration approved."
        )
    )
    service = SummarizationService(llm_service=mock_llm)
    res = service.summarize_document(sample_text, "orion.txt")

    assert res["method"] == "llm"
    assert "Project Orion" in res["short"]
    assert "30s" in res["detailed"]

    # 2. Extractive fallback
    fallback_res = service._extractive_summary(sample_text)
    assert fallback_res["method"] in ["extractive", "extractive_fallback"]
    assert len(fallback_res["short"]) > 0


def test_keyword_extraction():
    """Verify TF-IDF keyword extraction and stop-word filtering."""
    text = (
        "Quantum computing algorithms accelerate cryptographic factorization. "
        "Quantum superposition and quantum entanglement provide computational advantages. "
        "Traditional encryption methods may become vulnerable to quantum decryption."
    )

    keywords = KeywordService.extract_keywords(text, top_n=5)
    assert len(keywords) > 0

    kw_names = [k["keyword"].lower() for k in keywords]
    assert any("quantum" in k for k in kw_names)

    # Verify no basic stop-words like 'and', 'the', 'to' were returned
    for kw in kw_names:
        assert kw not in {"and", "the", "to", "in", "of", "a", "is"}


def test_comparison_service():
    """Verify side-by-side document comparison."""
    mock_llm = MockLLMService(
        default_response=(
            "### MAIN TOPICS\nDoc A covers SQL databases, while Doc B covers NoSQL.\n\n"
            "### SIMILARITIES\nBoth systems provide persistent storage.\n\n"
            "### DIFFERENCES\nDoc A uses ACID transactions; Doc B uses eventual consistency.\n\n"
            "### MISSING OR UNIQUE INFORMATION\nDoc B omits relational schema design."
        )
    )
    service = ComparisonService(llm_service=mock_llm)

    res = service.compare_documents(
        doc_a_name="sql.txt",
        doc_a_text="Relational databases use SQL tables and ACID transactions.",
        doc_b_name="nosql.txt",
        doc_b_text="Document stores use NoSQL collections and eventual consistency.",
    )

    assert res["method"] == "llm"
    assert "MAIN TOPICS" in res["analysis"]
    assert "SIMILARITIES" in res["analysis"]
    assert "DIFFERENCES" in res["analysis"]
    assert isinstance(res["common_keywords"], list)
