"""Configuration management for Clarifile Document Intelligence System."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Project Root Directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env if present
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


class Config:
    """Application configuration settings."""

    # Project directories
    DATA_DIR = PROJECT_ROOT / "data"
    DEFAULT_CHROMA_DIR = DATA_DIR / "chroma_db"

    # API Keys & LLM settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

    # Embedding settings
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2").strip()

    # ChromaDB settings
    CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", str(DEFAULT_CHROMA_DIR)))
    if not CHROMA_PERSIST_DIR.is_absolute():
        CHROMA_PERSIST_DIR = PROJECT_ROOT / CHROMA_PERSIST_DIR
    CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "clarifile_documents").strip()

    # Chunking settings
    DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "800"))
    DEFAULT_CHUNK_OVERLAP = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "150"))

    # Retrieval settings
    DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.10"))

    # File Upload limits
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "25"))
    SUPPORTED_EXTENSIONS = {"pdf", "docx", "txt", "csv", "xlsx", "pages"}

    # System instruction for Clarifile RAG
    SYSTEM_INSTRUCTION = (
        "You are Clarifile, an accurate document analysis assistant. Answer questions "
        "using only the information provided in the retrieved document context. Do not invent facts "
        "or use unsupported external knowledge. If the answer is unavailable in the retrieved context, "
        "clearly state that the information was not found in the uploaded documents. "
        "Provide concise, understandable answers and identify the document sources used."
    )

    @classmethod
    def get_gemini_api_key(cls, runtime_key: str = None) -> str:
        """Return runtime key if explicitly provided, else environment key."""
        if runtime_key is not None:
            return runtime_key.strip()
        return cls.GEMINI_API_KEY

    @classmethod
    def is_gemini_configured(cls, runtime_key: str = None) -> bool:
        """Check if a Gemini API key is configured and non-empty."""
        key = cls.get_gemini_api_key(runtime_key)
        return bool(key and len(key) > 5)

    @classmethod
    def save_gemini_api_key(cls, key: str, persist_env: bool = True) -> None:
        """Update runtime key and optionally persist to local .env file."""
        cleaned = key.strip()
        cls.GEMINI_API_KEY = cleaned
        os.environ["GEMINI_API_KEY"] = cleaned

        if persist_env:
            env_path = PROJECT_ROOT / ".env"
            lines = []
            if env_path.exists():
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                except Exception:
                    lines = []

            key_found = False
            new_lines = []
            for line in lines:
                if line.strip().startswith("GEMINI_API_KEY="):
                    new_lines.append(f"GEMINI_API_KEY={cleaned}\n")
                    key_found = True
                else:
                    new_lines.append(line)
            if not key_found:
                new_lines.append(f"GEMINI_API_KEY={cleaned}\n")

            try:
                with open(env_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
            except Exception:
                pass
