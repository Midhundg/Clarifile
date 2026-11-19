"""Keyword extraction service using TF-IDF and statistical n-gram analysis."""

from typing import List, Dict, Any
import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from services.text_processor import TextProcessor


# Comprehensive clean alpha-only stop-words list
STOP_WORDS = {
    "about", "above", "after", "again", "against", "all", "also", "and", "any", "are",
    "aren", "arent", "because", "been", "before", "being", "below", "between", "both", "but",
    "can", "cannot", "could", "couldn", "couldnt", "did", "didn", "didnt", "does", "doesn",
    "doesnt", "doing", "don", "dont", "down", "during", "each", "few", "first", "for", "from",
    "further", "general", "had", "hadn", "hadnt", "has", "hasn", "hasnt", "have", "haven",
    "havent", "having", "her", "here", "hers", "herself", "him", "himself", "his", "how",
    "including", "into", "isn", "isnt", "its", "itself", "just", "like", "may", "might",
    "more", "most", "must", "mustn", "mustnt", "new", "nor", "not", "off", "once", "one",
    "only", "other", "our", "ours", "ourselves", "out", "over", "own", "per", "same", "second",
    "shall", "shan", "shant", "she", "should", "shouldn", "shouldnt", "some", "such", "than",
    "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "three", "through", "too", "two", "under", "until", "used", "using",
    "various", "very", "via", "was", "wasn", "wasnt", "well", "were", "weren", "werent",
    "what", "when", "where", "which", "while", "who", "whom", "why", "will", "with", "within",
    "without", "won", "wont", "would", "wouldn", "wouldnt", "you", "your", "yours", "yourself",
    "yourselves"
}


class KeywordService:
    """Extracts statistically significant unigrams and bigrams using TF-IDF."""

    @classmethod
    def extract_keywords(
        cls,
        text: str,
        top_n: int = 15,
        include_bigrams: bool = True,
    ) -> List[Dict[str, Any]]:
        """Extract top keywords and key phrases using TF-IDF over document sentences.

        Args:
            text: Raw or cleaned document text.
            top_n: Number of top keywords to return.
            include_bigrams: Whether to include 2-word key phrases.

        Returns:
            List of dictionaries containing 'keyword', 'score', and 'frequency'.
        """
        cleaned = TextProcessor.clean_text(text)
        if not cleaned:
            return []

        sentences = TextProcessor.segment_sentences(cleaned)
        if len(sentences) < 2:
            # If document is very short, split by paragraphs or newlines
            sentences = [p for p in cleaned.split("\n") if p.strip()]

        if not sentences:
            sentences = [cleaned]

        ngram_range = (1, 2) if include_bigrams else (1, 1)

        try:
            vectorizer = TfidfVectorizer(
                stop_words=list(STOP_WORDS),
                ngram_range=ngram_range,
                min_df=1,
                max_df=0.95 if len(sentences) > 5 else 1.0,
                token_pattern=r"(?u)\b[a-zA-Z]{3,}\b",
            )
            tfidf_matrix = vectorizer.fit_transform(sentences)
            feature_names = vectorizer.get_feature_names_out()

            # Sum TF-IDF scores across all sentences
            mean_scores = tfidf_matrix.mean(axis=0).A1
            keyword_scores = list(zip(feature_names, mean_scores))

            # Count raw term frequencies in the full text
            words_only = re.findall(r"\b[a-zA-Z]{3,}\b", cleaned.lower())
            word_counts = Counter(words_only)

            # Sort by TF-IDF score descending
            keyword_scores.sort(key=lambda x: x[1], reverse=True)

            results: List[Dict[str, Any]] = []
            seen = set()

            for phrase, score in keyword_scores:
                # Avoid redundant unigrams if already captured by strong bigram
                if phrase in seen:
                    continue

                # Estimate frequency
                if " " in phrase:
                    freq = cleaned.lower().count(phrase)
                else:
                    freq = word_counts.get(phrase, 1)

                if freq > 0:
                    results.append({
                        "keyword": phrase.title() if " " in phrase else phrase,
                        "score": round(float(score), 4),
                        "frequency": freq,
                    })
                    seen.add(phrase)

                if len(results) >= top_n:
                    break

            return results

        except Exception:
            # Fallback to frequency counter with stop-word filter
            return cls._frequency_fallback(cleaned, top_n)

    @classmethod
    def _frequency_fallback(cls, text: str, top_n: int) -> List[Dict[str, Any]]:
        """Fallback to filtered word frequency counter."""
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        filtered = [w for w in words if w not in STOP_WORDS]
        counts = Counter(filtered).most_common(top_n)

        total_words = max(len(filtered), 1)
        return [
            {
                "keyword": word,
                "score": round(count / total_words, 4),
                "frequency": count,
            }
            for word, count in counts
        ]
