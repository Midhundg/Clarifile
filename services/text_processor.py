"""Text preprocessing, cleaning, sentence segmentation, and text statistics."""

import re
import unicodedata
from typing import List, Dict, Any


class TextProcessor:
    """Provides text normalization, sentence segmentation, and statistics."""

    # Common abbreviations to avoid incorrect sentence splitting
    ABBREVIATIONS = {
        "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.", "vs.", "etc.",
        "e.g.", "i.e.", "u.s.", "u.k.", "inc.", "corp.", "ltd.", "co.", "jan.",
        "feb.", "mar.", "apr.", "jun.", "jul.", "aug.", "sep.", "sept.", "oct.",
        "nov.", "dec."
    }

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Normalize unicode, replace bizarre whitespace and control characters, and clean lines.

        Args:
            text: Raw input text.

        Returns:
            Normalized and cleaned text.
        """
        if not text:
            return ""

        # Normalize unicode (NFKC)
        normalized = unicodedata.normalize("NFKC", text)

        # Replace non-breaking spaces and tabs with standard space
        normalized = normalized.replace("\u00a0", " ").replace("\t", " ")

        # Standardize line endings (\r\n or \r -> \n)
        normalized = re.sub(r"\r\n|\r", "\n", normalized)

        # Remove unprintable control characters except \n
        normalized = "".join(
            ch for ch in normalized if ch == "\n" or (unicodedata.category(ch)[0] != "C")
        )

        # Collapse excessive spaces within lines
        cleaned_lines = []
        for line in normalized.split("\n"):
            cleaned_line = re.sub(r" {2,}", " ", line).strip()
            cleaned_lines.append(cleaned_line)

        # Collapse more than 2 consecutive newlines into 2
        joined = "\n".join(cleaned_lines)
        joined = re.sub(r"\n{3,}", "\n\n", joined)

        # Repair broken hyphenated words from PDF extractions (e.g., 'Im- plemented' -> 'Implemented')
        joined = re.sub(r"(\b[a-zA-Z]{2,})-\s+([a-zA-Z]{2,}\b)", r"\1\2", joined)

        return joined.strip()

    @classmethod
    def segment_sentences(cls, text: str) -> List[str]:
        """Split text into sentences while protecting abbreviations, numbers, and URLs.

        Args:
            text: The text to split into sentences.

        Returns:
            List of sentence strings.
        """
        if not text or not text.strip():
            return []

        cleaned = cls.clean_text(text)

        # Split on paragraph boundaries first
        paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
        all_sentences: List[str] = []

        # Sentence end pattern: punctuation followed by whitespace and capital letter or end of string
        sentence_end_regex = re.compile(r"([.!?]+)(?:\s+|$)")

        for para in paragraphs:
            # Also handle single newline within paragraph as whitespace
            para_flat = re.sub(r"\n", " ", para)
            tokens = para_flat.split(" ")
            current_sentence = []

            for i, token in enumerate(tokens):
                current_sentence.append(token)
                lower_token = token.lower().rstrip(")\"']")

                # Check if this token ends a sentence
                ends_punct = bool(re.search(r"[.!?]+$", lower_token))
                is_abbrev = lower_token in cls.ABBREVIATIONS

                # Check for decimal numbers like 3.14 or bullet points like 1.
                is_numeric = bool(re.match(r"^\d+\.?\d*$", lower_token))

                if ends_punct and not is_abbrev and not is_numeric:
                    # Form sentence
                    sentence_str = " ".join(current_sentence).strip()
                    if sentence_str:
                        all_sentences.append(sentence_str)
                    current_sentence = []

            # Remaining tokens
            if current_sentence:
                sentence_str = " ".join(current_sentence).strip()
                if sentence_str:
                    all_sentences.append(sentence_str)

        return all_sentences

    @classmethod
    def compute_statistics(cls, text: str) -> Dict[str, Any]:
        """Compute comprehensive document text metrics."""
        cleaned = cls.clean_text(text)
        words = re.findall(r"\b\w+\b", cleaned)
        sentences = cls.segment_sentences(cleaned)
        paragraphs = [p for p in cleaned.split("\n\n") if p.strip()]
        lines = [line for line in cleaned.split("\n") if line.strip()]

        return {
            "character_count": len(cleaned),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "line_count": len(lines),
            "avg_word_length": round(sum(len(w) for w in words) / max(len(words), 1), 1),
            "avg_sentence_length_words": round(len(words) / max(len(sentences), 1), 1),
        }
