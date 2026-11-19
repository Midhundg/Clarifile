"""BM25 (Best Matching 25) Lexical Retrieval Engine for Clarifile.

Provides exact token, keyword, and entity scoring to complement dense vector embeddings.
"""

import math
import re
from collections import Counter
from typing import List, Dict, Set


# Standard retrieval stop-words to eliminate uninformative query matches
RETRIEVAL_STOP_WORDS: Set[str] = {
    "what", "is", "the", "a", "an", "in", "of", "for", "to", "and", "with", "on",
    "at", "by", "from", "this", "that", "it", "as", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "can", "could",
    "will", "would", "shall", "should", "tell", "me", "about", "give", "show",
    "please", "find", "whose", "who", "which", "where", "how"
}


class BM25Scorer:
    """Okapi BM25 implementation for term-frequency and inverse-document-frequency ranking."""

    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)

        # Tokenize corpus without stop words
        self.tokenized_corpus: List[List[str]] = [
            [w for w in re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", doc.lower()) if w not in RETRIEVAL_STOP_WORDS]
            for doc in corpus
        ]

        self.doc_lens = [len(doc) for doc in self.tokenized_corpus]
        self.avgdl = sum(self.doc_lens) / max(self.corpus_size, 1)

        # Precompute frequencies
        self.doc_freqs: List[Dict[str, int]] = [Counter(doc) for doc in self.tokenized_corpus]

        # Calculate document frequency (DF) for each term across corpus
        self.df = Counter()
        for doc in self.tokenized_corpus:
            for term in set(doc):
                self.df[term] += 1

        # Calculate Inverse Document Frequency (IDF)
        self.idf: Dict[str, float] = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

    def score_query(self, query: str) -> List[float]:
        """Compute BM25 scores for all documents given a query string.

        Args:
            query: The user search prompt.

        Returns:
            List of float scores for each document in the corpus.
        """
        q_tokens = [
            w for w in re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", query.lower())
            if w not in RETRIEVAL_STOP_WORDS
        ]

        if not q_tokens:
            # If query was entirely stop words (e.g. "what is it"), fallback to all alphanumeric tokens
            q_tokens = re.findall(r"\b[a-zA-Z0-9_]+\b", query.lower())

        scores = [0.0] * self.corpus_size

        for term in q_tokens:
            if term not in self.idf:
                continue

            idf = self.idf[term]
            for i, freq_dict in enumerate(self.doc_freqs):
                freq = freq_dict.get(term, 0)
                if freq > 0:
                    numerator = freq * (self.k1 + 1.0)
                    denominator = freq + self.k1 * (1.0 - self.b + self.b * (self.doc_lens[i] / self.avgdl))
                    scores[i] += idf * (numerator / denominator)

        return scores
