"""Document comparison service providing multi-document contrastive intelligence."""

from typing import Dict, Any, Optional
from services.llm_service import BaseLLMService, GeminiLLMService, MissingAPIKeyError, LLMError
from services.text_processor import TextProcessor
from services.keyword_service import KeywordService


class ComparisonService:
    """Compares two documents across topics, similarities, differences, and missing points."""

    def __init__(self, llm_service: Optional[BaseLLMService] = None):
        self.llm_service = llm_service or GeminiLLMService()

    def set_llm_service(self, llm_service: BaseLLMService) -> None:
        self.llm_service = llm_service

    def compare_documents(
        self,
        doc_a_name: str,
        doc_a_text: str,
        doc_b_name: str,
        doc_b_text: str,
    ) -> Dict[str, Any]:
        """Perform deep comparison between two documents.

        Args:
            doc_a_name: Name of first document.
            doc_a_text: Extracted content of first document.
            doc_b_name: Name of second document.
            doc_b_text: Extracted content of second document.

        Returns:
            Dictionary with structured comparison sections and keyword overlap.
        """
        clean_a = TextProcessor.clean_text(doc_a_text)
        clean_b = TextProcessor.clean_text(doc_b_text)

        if not clean_a or not clean_b:
            return {
                "topics": "Both documents must have readable content to compare.",
                "similarities": "N/A",
                "differences": "N/A",
                "missing_info": "N/A",
                "method": "empty",
            }

        # Extract keywords for both documents to find overlap
        kw_a = {item["keyword"].lower() for item in KeywordService.extract_keywords(clean_a, top_n=20)}
        kw_b = {item["keyword"].lower() for item in KeywordService.extract_keywords(clean_b, top_n=20)}
        common_keywords = sorted(list(kw_a.intersection(kw_b)))
        unique_a = sorted(list(kw_a - kw_b))[:8]
        unique_b = sorted(list(kw_b - kw_a))[:8]

        # Limit text length sent to LLM for comparison
        sample_a = clean_a[:7000]
        sample_b = clean_b[:7000]

        try:
            comparison = self._llm_compare(doc_a_name, sample_a, doc_b_name, sample_b)
            comparison["common_keywords"] = common_keywords
            comparison["unique_to_a"] = unique_a
            comparison["unique_to_b"] = unique_b
            return comparison
        except (MissingAPIKeyError, LLMError) as e:
            fallback = self._statistical_compare(doc_a_name, clean_a, doc_b_name, clean_b)
            fallback["common_keywords"] = common_keywords
            fallback["unique_to_a"] = unique_a
            fallback["unique_to_b"] = unique_b
            fallback["warning"] = f"LLM unavailable ({str(e)}). Displaying statistical comparison."
            return fallback

    def _llm_compare(
        self,
        doc_a_name: str,
        text_a: str,
        doc_b_name: str,
        text_b: str,
    ) -> Dict[str, Any]:
        prompt = (
            f"You are Clarifile, performing an in-depth comparative analysis of two documents.\n\n"
            f"DOCUMENT 1: {doc_a_name}\n"
            f"----------------------------------------\n"
            f"{text_a}\n\n"
            f"DOCUMENT 2: {doc_b_name}\n"
            f"----------------------------------------\n"
            f"{text_b}\n\n"
            f"Please produce a comparative evaluation with the following exact Markdown headers:\n\n"
            f"### MAIN TOPICS\n"
            f"A side-by-side comparison of the core topics and primary scope of each document.\n\n"
            f"### SIMILARITIES\n"
            f"Key points, overlapping themes, shared facts, or common conclusions between both documents.\n\n"
            f"### DIFFERENCES\n"
            f"Contrasting arguments, varying metrics, conflicting data points, or differences in methodology.\n\n"
            f"### MISSING OR UNIQUE INFORMATION\n"
            f"Crucial information present in one document but omitted or absent from the other."
        )

        sys_inst = (
            "You are Clarifile, an expert document intelligence assistant. Provide factual, "
            "rigorous comparisons based solely on the provided document excerpts."
        )

        response = self.llm_service.generate(prompt=prompt, system_instruction=sys_inst, temperature=0.2)

        return {
            "analysis": response,
            "method": "llm",
        }

    def _statistical_compare(
        self,
        name_a: str,
        text_a: str,
        name_b: str,
        text_b: str,
    ) -> Dict[str, Any]:
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())

        overlap_ratio = len(words_a & words_b) / max(len(words_a | words_b), 1)

        summary = (
            f"### STATISTICAL COMPARISON\n\n"
            f"- **Vocabulary Overlap (Jaccard Index)**: {overlap_ratio:.1%}\n"
            f"- **{name_a} Length**: {len(text_a):,} characters, {len(text_a.split()):,} words\n"
            f"- **{name_b} Length**: {len(text_b):,} characters, {len(text_b.split()):,} words\n\n"
            f"Statistical comparison completed based on document vocabulary and length analysis."
        )

        return {
            "analysis": summary,
            "method": "statistical_fallback",
        }
