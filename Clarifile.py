"""Clarifile — Intelligent File Analyzer & RAG Document Intelligence System.

This module preserves legacy extraction and rule-based helper functions for
backward-compatibility, while delegating the primary Streamlit interface to app.py.
"""

import sys
import runpy
from pathlib import Path

# Legacy helper functions preserved for backward compatibility
from services.document_loader import DocumentLoader
from services.text_processor import TextProcessor
from services.keyword_service import KeywordService


def read_pdf(file):
    """Legacy PDF extraction helper."""
    doc = DocumentLoader.load_document(file, getattr(file, "name", "document.pdf"))
    return doc.full_text


def read_docx(file):
    """Legacy DOCX extraction helper."""
    doc = DocumentLoader.load_document(file, getattr(file, "name", "document.docx"))
    return doc.full_text


def read_txt(file):
    """Legacy TXT extraction helper."""
    doc = DocumentLoader.load_document(file, getattr(file, "name", "document.txt"))
    return doc.full_text


def read_csv(file):
    """Legacy CSV extraction helper."""
    doc = DocumentLoader.load_document(file, getattr(file, "name", "document.csv"))
    return doc.full_text


def read_excel(file):
    """Legacy Excel extraction helper."""
    doc = DocumentLoader.load_document(file, getattr(file, "name", "document.xlsx"))
    return doc.full_text


def summarize_text(text, max_sentences=5):
    """Legacy extractive summarizer."""
    sentences = TextProcessor.segment_sentences(text)
    return " ".join(sentences[:max_sentences])


def extract_key_points(text, count=5):
    """Legacy key points extractor."""
    sentences = TextProcessor.segment_sentences(text)
    return sentences[:count]


def extract_keywords(text, top_n=10):
    """Legacy keyword extractor."""
    results = KeywordService.extract_keywords(text, top_n=top_n)
    return [item["keyword"] for item in results]


# When executed directly or via `streamlit run Clarifile.py`, execute the full RAG app
if __name__ == "__main__" or "streamlit" in sys.modules:
    app_path = Path(__file__).parent / "app.py"
    runpy.run_path(str(app_path), run_name="__main__")