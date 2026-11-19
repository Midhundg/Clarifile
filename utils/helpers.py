"""Helper utility functions for hashing, formatting, and UI presentation."""

import hashlib
from typing import Any, Optional


def generate_doc_id(file_name: str, content: bytes | str) -> str:
    """Generate a unique, deterministic document ID based on filename and content hash."""
    hasher = hashlib.sha256()
    hasher.update(file_name.encode("utf-8", errors="ignore"))
    if isinstance(content, str):
        hasher.update(content.encode("utf-8", errors="ignore"))
    elif isinstance(content, bytes):
        hasher.update(content)
    # Return 16-character hex hash prefixed with doc_
    return f"doc_{hasher.hexdigest()[:16]}"


def format_file_size(size_bytes: int) -> str:
    """Format byte size into human-readable representation."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max_length characters gracefully."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)].rstrip() + suffix


def format_source_citation(file_name: str, page: Any, score: Optional[float] = None) -> str:
    """Format citation string for display."""
    page_str = f"Page {page}" if isinstance(page, int) else f"Section: {page}"
    if score is not None:
        return f"📄 {file_name} ({page_str}) — Relevance: {score:.1%}"
    return f"📄 {file_name} ({page_str})"
