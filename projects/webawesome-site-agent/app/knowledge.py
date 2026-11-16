from __future__ import annotations

from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"
MAX_CONTEXT_CHARS = 6000


def load_docs() -> dict[str, str]:
    docs: dict[str, str] = {}
    if not KNOWLEDGE_DIR.exists():
        return docs
    for path in sorted(KNOWLEDGE_DIR.rglob("*.md")):
        docs[str(path.relative_to(KNOWLEDGE_DIR))] = path.read_text(encoding="utf-8", errors="replace")
    return docs


def search(query: str, *, limit: int = 4) -> list[tuple[str, str]]:
    terms = [term for term in (query or "").lower().split() if len(term) > 2]
    if not terms:
        return []
    scored: list[tuple[int, str, str]] = []
    for name, text in load_docs().items():
        lowered = text.lower()
        score = sum(lowered.count(term) for term in terms)
        if score:
            scored.append((score, name, text))
    scored.sort(key=lambda row: row[0], reverse=True)
    return [(name, text) for _, name, text in scored[:limit]]


def build_context(query: str) -> str:
    chunks: list[str] = []
    total = 0
    for name, text in search(query):
        chunk = f"### {name}\n{text.strip()}"
        if total + len(chunk) > MAX_CONTEXT_CHARS:
            chunk = chunk[: max(0, MAX_CONTEXT_CHARS - total)]
        chunks.append(chunk)
        total += len(chunk)
        if total >= MAX_CONTEXT_CHARS:
            break
    return "\n\n".join(chunks)
