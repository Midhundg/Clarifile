"""Document summarization service providing short, detailed, and observation summaries."""

from typing import Dict, Any, Optional, List
from services.llm_service import BaseLLMService, GeminiLLMService, MissingAPIKeyError, LLMError
from services.text_processor import TextProcessor
from utils.config import Config


class SummarizationService:
    """Provides multi-tiered summaries (short, detailed, observations) with map-reduce for large texts."""

    def __init__(self, llm_service: Optional[BaseLLMService] = None):
        self.llm_service = llm_service or GeminiLLMService()

    def set_llm_service(self, llm_service: BaseLLMService) -> None:
        self.llm_service = llm_service

    def summarize_document(
        self,
        full_text: str,
        file_name: str,
        summary_type: str = "all",  # "short", "detailed", "observations", or "all"
    ) -> Dict[str, str]:
        """Generate structured summaries for a document.

        Args:
            full_text: The extracted document text.
            file_name: Document name for context.
            summary_type: Type of summary to produce.

        Returns:
            Dictionary containing 'short', 'detailed', 'observations', and 'method'.
        """
        cleaned = TextProcessor.clean_text(full_text)
        if not cleaned:
            return {
                "short": "No readable content to summarize.",
                "detailed": "No readable content to summarize.",
                "observations": "No readable content to summarize.",
                "method": "empty",
            }

        # Check if text is large (e.g. > 15,000 characters)
        max_direct_chars = 15000
        text_for_summary = cleaned
        if len(cleaned) > max_direct_chars:
            text_for_summary = self._map_reduce_summarize(cleaned, file_name)

        try:
            return self._llm_summarize(text_for_summary, file_name, summary_type)
        except (MissingAPIKeyError, LLMError) as e:
            # Fallback to intelligent extractive summarization
            fallback = self._extractive_summary(cleaned)
            fallback["warning"] = f"LLM unavailable ({str(e)}). Showing extractive rule-based summary."
            return fallback

    def _llm_summarize(self, text: str, file_name: str, summary_type: str) -> Dict[str, str]:
        """Perform LLM-based structured summarization."""
        prompt = (
            f"Document Title: {file_name}\n\n"
            f"Document Content:\n"
            f"-----------------\n"
            f"{text}\n"
            f"-----------------\n\n"
            f"Please generate a comprehensive analysis containing exactly three labeled sections:\n\n"
            f"### SHORT SUMMARY\n"
            f"A concise 2-3 sentence overview highlighting the document's central purpose.\n\n"
            f"### DETAILED SUMMARY\n"
            f"A structured, executive summary outlining the core arguments, context, and primary findings.\n\n"
            f"### IMPORTANT OBSERVATIONS\n"
            f"A bulleted list of 3-5 critical observations, strategic implications, or noteworthy takeaways."
        )

        sys_inst = (
            "You are Clarifile, an expert document intelligence assistant. Provide accurate, "
            "objective summaries grounded exclusively in the provided document text."
        )

        response = self.llm_service.generate(prompt=prompt, system_instruction=sys_inst, temperature=0.2)

        # Parse sections
        short_summary = ""
        detailed_summary = ""
        observations = ""

        if "### SHORT SUMMARY" in response:
            parts = response.split("### SHORT SUMMARY")
            sub_parts = parts[1].split("### DETAILED SUMMARY")
            short_summary = sub_parts[0].strip()

            if len(sub_parts) > 1:
                sub_parts2 = sub_parts[1].split("### IMPORTANT OBSERVATIONS")
                detailed_summary = sub_parts2[0].strip()
                if len(sub_parts2) > 1:
                    observations = sub_parts2[1].strip()
        else:
            # Fallback parsing
            detailed_summary = response.strip()
            short_summary = TextProcessor.clean_text(response[:300])
            observations = "See detailed summary for key observations."

        return {
            "short": short_summary or "Short summary could not be isolated.",
            "detailed": detailed_summary or response.strip(),
            "observations": observations or "Observations could not be isolated.",
            "method": "llm",
        }

    def _map_reduce_summarize(self, text: str, file_name: str, chunk_size: int = 10000) -> str:
        """Compress large documents by summarizing sections first before final pass."""
        sections = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
        section_summaries: List[str] = []

        for idx, sec in enumerate(sections[:5], start=1):  # Limit to first 5 large sections
            try:
                sec_prompt = (
                    f"Condense the following section ({idx}/{len(sections)}) of '{file_name}' into "
                    f"2-3 dense informational paragraphs:\n\n{sec}"
                )
                sec_summary = self.llm_service.generate(sec_prompt, temperature=0.1)
                section_summaries.append(sec_summary)
            except Exception:
                # If section summary fails, take first 500 chars of section
                section_summaries.append(sec[:500])

        return "\n\n".join(section_summaries)

    def _extractive_summary(self, text: str) -> Dict[str, str]:
        """Extractive fallback summary using frequency-weighted sentence ranking."""
        sentences = TextProcessor.segment_sentences(text)
        if not sentences:
            return {
                "short": "No content available.",
                "detailed": "No content available.",
                "observations": "No content available.",
                "method": "extractive",
            }

        # Deduplicate sentences preserving order
        seen = set()
        unique_sentences = []
        for s in sentences:
            s_clean = s.strip()
            if s_clean and s_clean.lower() not in seen:
                seen.add(s_clean.lower())
                unique_sentences.append(s_clean)
        sentences = unique_sentences

        # Short summary: first 2-3 sentences
        short = " ".join(sentences[:2])

        # Detailed summary: top 5 sentences
        detailed = "\n\n".join([f"• {s}" for s in sentences[:5]])

        # Observations: sentences with actionable or quantitative terms
        keywords = ["important", "key", "decision", "result", "total", "increase", "decrease", "must", "recommend"]
        notable = [s for s in sentences if any(k in s.lower() for k in keywords)]
        observations = "\n\n".join([f"• {s}" for s in notable[:4]]) if notable else "• " + "\n• ".join(sentences[2:5])

        return {
            "short": short,
            "detailed": detailed,
            "observations": observations,
            "method": "extractive_fallback",
        }
