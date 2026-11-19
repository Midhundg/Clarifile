"""File, input, and configuration validators for Clarifile."""

import os
import re
from typing import Tuple, Any
from utils.config import Config


class ValidationError(Exception):
    """Custom exception raised when validation fails."""
    pass


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal or unsafe characters."""
    if not filename:
        return "unnamed_document"
    # Take only the base name (remove directory components)
    clean_name = os.path.basename(filename)
    # Remove control characters or path separators
    clean_name = re.sub(r'[\\/*?:"<>|]', "_", clean_name)
    # Avoid hidden files or leading dots
    clean_name = clean_name.lstrip(".")
    return clean_name or "document"


def validate_file_upload(file_name: str, file_size: int) -> Tuple[bool, str]:
    """Validate uploaded file by name, extension, and size.

    Args:
        file_name: The name of the file.
        file_size: Size of the file in bytes.

    Returns:
        Tuple of (is_valid: bool, error_message: str).
    """
    if not file_name or not file_name.strip():
        return False, "File name cannot be empty."

    # Check extension
    parts = file_name.rsplit(".", 1)
    if len(parts) < 2:
        return False, f"File '{file_name}' has no extension. Supported formats: {', '.join(sorted(Config.SUPPORTED_EXTENSIONS))}."

    extension = parts[1].lower()
    if extension not in Config.SUPPORTED_EXTENSIONS:
        return (
            False,
            f"Unsupported format '.{extension}'. Supported: {', '.join(sorted(Config.SUPPORTED_EXTENSIONS))}."
        )

    # Check size
    if file_size <= 0:
        return False, f"File '{file_name}' is empty (0 bytes)."

    max_bytes = Config.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        return (
            False,
            f"File '{file_name}' exceeds maximum allowed size of {Config.MAX_FILE_SIZE_MB} MB."
        )

    return True, ""


def validate_api_key(api_key: str) -> Tuple[bool, str]:
    """Validate Google Gemini API key presence and basic syntax."""
    if not api_key or not api_key.strip():
        return False, "API key is missing. Please configure your GEMINI_API_KEY."

    cleaned = api_key.strip()
    if len(cleaned) < 10:
        return False, "API key appears too short or invalid."

    return True, ""
