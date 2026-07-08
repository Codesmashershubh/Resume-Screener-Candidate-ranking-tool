"""
Minimal, dependency-free NLP utilities: tokenization, TF-IDF, cosine similarity.

Why hand-rolled instead of scikit-learn / sentence-transformers:
  - No model download required (sentence-transformers needs a ~90MB+ model
    pulled from the internet on first run; that's a bad experience for a
    tool that promises "free and fully working" out of the box).
  - Full transparency: every number the UI shows can be traced back to a
    formula in this file, which matters for an "explainability layer".
  - Zero extra dependencies for this half of the scoring engine.

The formula mirrors scikit-learn's default TfidfVectorizer smoothing
(idf = ln((1+n)/(1+df)) + 1), so results behave the way anyone familiar
with standard TF-IDF would expect.
"""

from __future__ import annotations
import math
import re
from collections import Counter

STOPWORDS: set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can",
    "could", "did", "do", "does", "doing", "down", "during", "each", "few",
    "for", "from", "further", "had", "has", "have", "having", "he", "her",
    "here", "hers", "herself", "him", "himself", "his", "how", "i", "if",
    "in", "into", "is", "it", "its", "itself", "just", "me", "more", "most",
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only",
    "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same",
    "she", "should", "so", "some", "such", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up", "very",
    "was", "we", "were", "what", "when", "where", "which", "while", "who",
    "whom", "why", "will", "with", "would", "you", "your", "yours",
    "yourself", "yourselves", "etc", "e.g", "eg", "ie", "i.e",
    # resume/JD boilerplate that adds noise, not signal
    "experience", "years", "year", "work", "working", "role", "job",
    "team", "company", "responsibilities", "requirements", "required",
    "preferred", "ability", "strong", "including", "including but",
    "responsible", "using", "used", "use", "skills", "skill",
}

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.#]{1,}")


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    tokens = (t.lower() for t in _TOKEN_RE.findall(text))
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def compute_tfidf(token_lists: list[list[str]]) -> list[dict[str, float]]:
    """Fit + transform in one step over the given corpus (list of token lists).

    Returns one {term: weight} dict per input document, in the same order.
    """
    n_docs = len(token_lists)
    if n_docs == 0:
        return []

    doc_freq: Counter[str] = Counter()
    for tokens in token_lists:
        for term in set(tokens):
            doc_freq[term] += 1

    idf = {
        term: math.log((1 + n_docs) / (1 + freq)) + 1.0
        for term, freq in doc_freq.items()
    }

    vectors: list[dict[str, float]] = []
    for tokens in token_lists:
        if not tokens:
            vectors.append({})
            continue
        term_freq = Counter(tokens)
        total = sum(term_freq.values())
        vectors.append(
            {term: (count / total) * idf[term] for term, count in term_freq.items()}
        )
    return vectors


def cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    shared = set(vec_a) & set(vec_b)
    if not shared:
        return 0.0
    dot = sum(vec_a[t] * vec_b[t] for t in shared)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def top_terms(vector: dict[str, float], n: int = 12) -> list[str]:
    return [term for term, _ in sorted(vector.items(), key=lambda kv: kv[1], reverse=True)[:n]]


def shared_top_terms(vec_a: dict[str, float], vec_b: dict[str, float], n: int = 8) -> list[str]:
    """Top terms that matter to *both* documents, ranked by combined weight."""
    shared = set(vec_a) & set(vec_b)
    ranked = sorted(shared, key=lambda t: vec_a[t] + vec_b[t], reverse=True)
    return ranked[:n]
