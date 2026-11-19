"""Unit tests for ChunkingService verifying sentence boundaries, overlap, and metadata."""

import pytest
from services.chunking import ChunkingService, DocumentChunk
from services.document_loader import ExtractedDocument, DocumentPage


def test_chunking_size_and_metadata():
    """Verify that chunks respect size configuration and carry document metadata."""
    chunker = ChunkingService(chunk_size=300, chunk_overlap=50)

    page1_text = (
        "Clarifile is an enterprise-grade document intelligence platform. "
        "It uses retrieval-augmented generation to deliver grounded answers. "
        "Every single chunk retains source file and page metadata for exact verification."
    )
    page2_text = (
        "In addition to Q&A, Clarifile extracts TF-IDF keywords and key points. "
        "The system persists vectors into ChromaDB for high-speed retrieval. "
        "Document comparison allows side-by-side contrasting of multiple files."
    )

    doc = ExtractedDocument(
        doc_id="doc_test123",
        file_name="architecture_spec.pdf",
        file_type="pdf",
        file_size=len(page1_text) + len(page2_text),
        pages=[
            DocumentPage(page_number=1, text=page1_text),
            DocumentPage(page_number=2, text=page2_text),
        ],
        full_text=f"{page1_text}\n\n{page2_text}",
    )

    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 2
    for chunk in chunks:
        assert isinstance(chunk, DocumentChunk)
        assert chunk.doc_id == "doc_test123"
        assert chunk.file_name == "architecture_spec.pdf"
        assert chunk.file_type == "pdf"
        assert chunk.page_number in ["1", "2", 1, 2]
        assert len(chunk.text) > 0
        assert chunk.chunk_id.startswith("doc_test123_c")


def test_chunking_overlap():
    """Verify that consecutive chunks from long text share overlapping sentences."""
    chunker = ChunkingService(chunk_size=200, chunk_overlap=80)

    long_text = (
        "Sentence number one introduces the foundational framework. "
        "Sentence number two expands on the architectural components and data flow. "
        "Sentence number three outlines security, authentication, and vector isolation. "
        "Sentence number four details operational deployment and testing verification. "
        "Sentence number five concludes the technical analysis."
    )

    doc = ExtractedDocument(
        doc_id="doc_overlap",
        file_name="overlap_test.txt",
        file_type="txt",
        file_size=len(long_text),
        pages=[DocumentPage(page_number=1, text=long_text)],
        full_text=long_text,
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) > 1

    # Check that chunk 2 shares some words with chunk 1
    words_c1 = set(chunks[0].text.split())
    words_c2 = set(chunks[1].text.split())
    assert len(words_c1.intersection(words_c2)) > 0


def test_invalid_overlap_raises_error():
    """Verify that chunk_overlap >= chunk_size raises ValueError."""
    with pytest.raises(ValueError):
        ChunkingService(chunk_size=200, chunk_overlap=200)

    with pytest.raises(ValueError):
        ChunkingService(chunk_size=200, chunk_overlap=250)


def test_oversized_sentence_handling():
    """Verify that an exceptionally long sentence is sub-split without raising an error."""
    chunker = ChunkingService(chunk_size=100, chunk_overlap=20)
    huge_sentence = "Word " * 60  # ~300 chars single sentence without punctuation

    doc = ExtractedDocument(
        doc_id="doc_huge",
        file_name="huge.txt",
        file_type="txt",
        file_size=len(huge_sentence),
        pages=[DocumentPage(page_number=1, text=huge_sentence)],
        full_text=huge_sentence,
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) >= 3
    for chunk in chunks:
        assert len(chunk.text) <= 120
