from __future__ import annotations

import math
import re
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"
MAX_CONTEXT_CHARS = 6000

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "at", "by", "for",
    "is", "are", "was", "be", "been", "do", "does", "did", "as", "if", "it",
    "its", "we", "us", "our", "you", "your", "my", "me", "i", "he", "she",
    "they", "them", "this", "that", "there", "what", "who", "how", "much",
    "can", "could", "would", "should", "have", "has", "had", "will", "just",
    "not", "but", "get", "got", "so", "up", "no", "yes", "also", "about",
    "into", "any", "all", "please", "offer", "offers", "service", "services",
}

SKIP_STEMS = {
    "error-404",
    "thank-you",
    "payment-confirmation",
    "payment-failed",
    "payment-page",
    "payment",
    "payment-cancelled",
}


def load_docs() -> dict[str, str]:
    docs: dict[str, str] = {}
    if not KNOWLEDGE_DIR.exists():
        return docs
    for path in sorted(KNOWLEDGE_DIR.rglob("*.md")):
        if path.stem.lower() in SKIP_STEMS:
            continue
        docs[str(path.relative_to(KNOWLEDGE_DIR))] = path.read_text(encoding="utf-8", errors="replace")
    return docs


def _boost(name: str) -> float:
    if "/" not in name:
        return 2.5
    if name.startswith("site/pages/"):
        return 1.4
    return 1.0


def _terms(query: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", (query or "").lower())
    return [word for word in words if len(word) > 1 and word not in STOPWORDS]


def _score(terms: list[str], text: str, name: str) -> float:
    lowered = text.lower()
    present = [term for term in terms if term in lowered]
    if not present:
        return 0.0
    coverage = len(present) / len(terms)
    hits = sum(lowered.count(term) for term in present)
    base = coverage * 4 + math.log1p(hits)
    return base * _boost(name) / (1 + len(text) / 20000)


def search(
    query: str,
    *,
    limit: int = 4,
    docs: dict[str, str] | None = None,
) -> list[tuple[str, str]]:
    terms = _terms(query)
    if not terms:
        return []
    corpus = load_docs() if docs is None else docs
    scored: list[tuple[float, str, str]] = []
    for name, text in corpus.items():
        score = _score(terms, text, name)
        if score:
            scored.append((score, name, text))
    scored.sort(key=lambda row: row[0], reverse=True)
    return [(name, text) for _, name, text in scored[:limit]]


def build_context(query: str) -> str:
    results = search(query)
    if not results:
        docs = load_docs()
        results = [(name, text) for name, text in docs.items() if "/" not in name and name != "README.md"][:2]
    chunks: list[str] = []
    total = 0
    for name, text in results:
        chunk = f"### {name}\n{text.strip()}"
        if total + len(chunk) > MAX_CONTEXT_CHARS:
            chunk = chunk[: max(0, MAX_CONTEXT_CHARS - total)]
        chunks.append(chunk)
        total += len(chunk)
        if total >= MAX_CONTEXT_CHARS:
            break
    return "\n\n".join(chunks)
