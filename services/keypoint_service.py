"""Key point extraction service for identifying main ideas, facts, decisions, and dates."""

from typing import List, Dict, Any, Optional
import re
from services.llm_service import BaseLLMService, GeminiLLMService, MissingAPIKeyError, LLMError
from services.text_processor import TextProcessor


class KeyPointService:
    """Extracts structured key points: Main Ideas, Important Facts, Decisions, and Dates/Milestones."""

    def __init__(self, llm_service: Optional[BaseLLMService] = None):
        self.llm_service = llm_service or GeminiLLMService()

    def set_llm_service(self, llm_service: BaseLLMService) -> None:
        self.llm_service = llm_service

    def extract_key_points(self, text: str, file_name: str) -> Dict[str, Any]:
        """Extract categorized key points from document text.

        Returns:
            Dictionary with categorized key points and extraction method.
        """
        cleaned = TextProcessor.clean_text(text)
        if not cleaned:
            return {
                "main_ideas": [],
                "important_facts": [],
                "decisions": [],
                "dates_milestones": [],
                "raw_text": "No content to extract points from.",
                "method": "empty",
            }

        sample_text = cleaned[:12000]

        try:
            return self._llm_extract_points(sample_text, file_name)
        except (MissingAPIKeyError, LLMError) as e:
            fallback = self._rule_based_extract_points(cleaned)
            fallback["warning"] = f"LLM unavailable ({str(e)}). Extracted using rule-based analysis."
            return fallback

    def _llm_extract_points(self, text: str, file_name: str) -> Dict[str, Any]:
        prompt = (
            f"Analyze the following document '{file_name}' and extract key structured information.\n\n"
            f"Document Text:\n"
            f"--------------\n"
            f"{text}\n"
            f"--------------\n\n"
            f"Provide your output formatted with the following exact Markdown headers:\n\n"
            f"### MAIN IDEAS\n"
            f"- (List 2-4 core themes or objectives)\n\n"
            f"### IMPORTANT FACTS\n"
            f"- (List 3-5 verified facts, metrics, or quantitative findings)\n\n"
            f"### DECISIONS & ACTIONS\n"
            f"- (List 2-4 key decisions, recommendations, or actionable next steps)\n\n"
            f"### DATES & TIMELINES\n"
            f"- (List any relevant dates, deadlines, or historical milestones found in text)"
        )

        response = self.llm_service.generate(
            prompt=prompt,
            system_instruction="You are Clarifile, a precision document intelligence engine. Extract strictly grounded facts without hallucination.",
            temperature=0.2,
        )

        return {
            "main_ideas": self._parse_bullet_section(response, "MAIN IDEAS", "IMPORTANT FACTS"),
            "important_facts": self._parse_bullet_section(response, "IMPORTANT FACTS", "DECISIONS & ACTIONS"),
            "decisions": self._parse_bullet_section(response, "DECISIONS & ACTIONS", "DATES & TIMELINES"),
            "dates_milestones": self._parse_bullet_section(response, "DATES & TIMELINES", None),
            "raw_text": response,
            "method": "llm",
        }

    def _parse_bullet_section(self, text: str, start_header: str, end_header: Optional[str]) -> List[str]:
        """Extract bullet points under a specific header."""
        header_marker = f"### {start_header}"
        if header_marker not in text:
            return []

        section_text = text.split(header_marker, 1)[1]
        if end_header:
            end_marker = f"### {end_header}"
            if end_marker in section_text:
                section_text = section_text.split(end_marker, 1)[0]

        items = []
        for line in section_text.split("\n"):
            line = line.strip()
            if line.startswith(("-", "*", "•", "1.", "2.", "3.", "4.", "5.")):
                clean_line = re.sub(r"^[-*•\d\.]+\s*", "", line).strip()
                if clean_line:
                    items.append(clean_line)

        return items

    def _rule_based_extract_points(self, text: str) -> Dict[str, Any]:
        """Rule-based fallback point extraction using regex and sentence cues."""
        sentences = TextProcessor.segment_sentences(text)

        # Dates extraction regex
        date_pattern = re.compile(
            r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}|\d{4})\b"
        )
        dates_found = []
        for s in sentences:
            if date_pattern.search(s):
                dates_found.append(s)

        # Decision / action cues
        decision_cues = ["decided", "agreed", "approved", "recommended", "action", "next step", "must", "resolve"]
        decisions = [s for s in sentences if any(c in s.lower() for c in decision_cues)]

        # Fact cues (numbers, percentages, metrics)
        metric_pattern = re.compile(r"(\$|\%|\b\d+(?:\.\d+)?\b)")
        facts = [s for s in sentences if metric_pattern.search(s) and s not in dates_found]

        return {
            "main_ideas": sentences[:3],
            "important_facts": facts[:4] if facts else sentences[3:6],
            "decisions": decisions[:3] if decisions else ["No explicit decisions recorded in document."],
            "dates_milestones": dates_found[:4] if dates_found else ["No explicit dates identified."],
            "raw_text": "\n".join(sentences[:5]),
            "method": "rule_based_fallback",
        }
