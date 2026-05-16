from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def clean_extracted_text(value: str) -> str:
    cleaned = normalize_text(value)
    cleaned = re.sub(r"^[^|]{0,25}\|[^|]{0,25}\|[^|]{0,35}\s*", "", cleaned)
    return cleaned.strip()


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in (match.group(0).lower() for match in WORD_RE.finditer(text))
        if token not in STOPWORDS
    ]


def expand_query_tokens(tokens: Iterable[str]) -> set[str]:
    expanded = set(tokens)
    for token in list(expanded):
        if len(token) > 3 and token.endswith("s"):
            expanded.add(token[:-1])
        elif len(token) > 3:
            expanded.add(f"{token}s")
    return expanded


def chunk_text(text: str, size: int = 1200, overlap: int = 200) -> Iterable[str]:
    cleaned = normalize_text(text)
    if not cleaned:
        return
    if len(cleaned) <= size:
        yield cleaned
        return

    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + size)
        window = cleaned[start:end]
        if end < len(cleaned):
            last_space = window.rfind(" ")
            if last_space > size // 2:
                window = window[:last_space]
                end = start + last_space
        yield window.strip()
        if end >= len(cleaned):
            break
        start = max(end - overlap, start + 1)


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    document_name: str
    page_number: int
    text: str
    tokens: list[str]


@dataclass(slots=True)
class Citation:
    document_name: str
    page_number: int
    snippet: str


@dataclass(slots=True)
class SearchHit:
    chunk: Chunk
    score: float


class DocumentIndex:
    def __init__(self, pdf_dir: Path) -> None:
        self.pdf_dir = pdf_dir
        self.documents: list[str] = []
        self.chunks: list[Chunk] = []
        self._doc_freq: Counter[str] = Counter()
        self._avg_chunk_len = 0.0

    def build(self) -> None:
        pdf_paths = sorted(self.pdf_dir.glob("*.pdf")) + sorted(self.pdf_dir.glob("*.PDF"))
        chunks: list[Chunk] = []
        documents: list[str] = []

        for pdf_path in pdf_paths:
            reader = PdfReader(str(pdf_path))
            documents.append(pdf_path.name)
            for page_index, page in enumerate(reader.pages, start=1):
                text = clean_extracted_text(page.extract_text() or "")
                if not text:
                    continue
                for local_index, piece in enumerate(chunk_text(text), start=1):
                    tokens = tokenize(piece)
                    if not tokens:
                        continue
                    chunks.append(
                        Chunk(
                            chunk_id=f"{pdf_path.stem}-p{page_index}-c{local_index}",
                            document_name=pdf_path.name,
                            page_number=page_index,
                            text=piece,
                            tokens=tokens,
                        )
                    )

        self.documents = documents
        self.chunks = chunks
        self._recalculate_statistics()

    def _recalculate_statistics(self) -> None:
        self._doc_freq = Counter()
        if not self.chunks:
            self._avg_chunk_len = 0.0
            return

        total_len = 0
        for chunk in self.chunks:
            total_len += len(chunk.tokens)
            self._doc_freq.update(set(chunk.tokens))
        self._avg_chunk_len = total_len / len(self.chunks)

    def reload(self) -> None:
        self.build()

    @property
    def is_ready(self) -> bool:
        return bool(self.chunks)

    def search(self, question: str, top_k: int = 5) -> list[SearchHit]:
        query_tokens = expand_query_tokens(tokenize(question))
        if not query_tokens or not self.chunks:
            return []

        scores: list[SearchHit] = []
        corpus_size = len(self.chunks)
        k1 = 1.5
        b = 0.75

        for chunk in self.chunks:
            term_counts = Counter(chunk.tokens)
            score = 0.0
            for token in query_tokens:
                freq = term_counts.get(token, 0)
                if freq == 0:
                    continue
                doc_freq = self._doc_freq.get(token, 0)
                idf = math.log(1 + (corpus_size - doc_freq + 0.5) / (doc_freq + 0.5))
                denom = freq + k1 * (1 - b + b * len(chunk.tokens) / max(self._avg_chunk_len, 1))
                score += idf * ((freq * (k1 + 1)) / denom)
            if score > 0:
                scores.append(SearchHit(chunk=chunk, score=score))

        scores.sort(key=lambda item: item.score, reverse=True)
        return scores[:top_k]

    def answer(self, question: str, top_k: int = 5, max_sentences: int = 3) -> dict:
        hits = self.search(question=question, top_k=top_k)
        if not hits:
            return {
                "answer": "I could not find enough grounded evidence in the indexed PDFs to answer that question.",
                "citations": [],
                "matched_chunks": [],
            }

        query_tokens = expand_query_tokens(tokenize(question))
        min_overlap = 1 if len(query_tokens) < 3 else 2
        best_hit_score = hits[0].score
        min_hit_score = max(1.0, best_hit_score * 0.5)
        passage_candidates: list[tuple[float, str, Chunk]] = []
        for hit in hits:
            if hit.score < min_hit_score:
                continue
            passage, overlap = self._best_passage(hit.chunk.text, query_tokens)
            if not passage or overlap < min_overlap:
                continue
            coverage_bonus = overlap / max(len(query_tokens), 1)
            passage_candidates.append((hit.score + coverage_bonus, passage, hit.chunk))

        if not passage_candidates:
            fallback = hits[0].chunk.text[:320].rstrip()
            return {
                "answer": fallback,
                "citations": [
                    {
                        "document_name": hits[0].chunk.document_name,
                        "page_number": hits[0].chunk.page_number,
                        "snippet": hits[0].chunk.text[:220],
                    }
                ],
                "matched_chunks": [self._format_hit(hit) for hit in hits],
            }

        passage_candidates.sort(key=lambda item: item[0], reverse=True)
        picked: list[tuple[str, Chunk]] = []
        seen_passages: set[str] = set()
        for _, passage, chunk in passage_candidates:
            normalized = passage.lower()
            if normalized in seen_passages:
                continue
            seen_passages.add(normalized)
            picked.append((passage, chunk))
            if len(picked) >= max_sentences:
                break

        answer = " ".join(passage for passage, _ in picked)
        citations: list[dict] = []
        seen_citations: set[tuple[str, int]] = set()
        for passage, chunk in picked:
            key = (chunk.document_name, chunk.page_number)
            if key in seen_citations:
                continue
            seen_citations.add(key)
            citations.append(
                {
                    "document_name": chunk.document_name,
                    "page_number": chunk.page_number,
                    "snippet": passage[:220],
                }
            )

        return {
            "answer": answer,
            "citations": citations,
            "matched_chunks": [self._format_hit(hit) for hit in hits],
        }

    def _format_hit(self, hit: SearchHit) -> dict:
        return {
            "chunk_id": hit.chunk.chunk_id,
            "document_name": hit.chunk.document_name,
            "page_number": hit.chunk.page_number,
            "score": round(hit.score, 4),
            "snippet": hit.chunk.text[:280],
        }

    def _best_passage(self, text: str, query_tokens: set[str], window: int = 260) -> tuple[str, int]:
        normalized = clean_extracted_text(text)
        if not normalized:
            return "", 0

        lowered = normalized.lower()
        candidate_starts: list[int] = []
        for token in query_tokens:
            start = lowered.find(token)
            while start != -1:
                candidate_starts.append(start)
                start = lowered.find(token, start + len(token))

        if not candidate_starts:
            return normalized[:window].rstrip(), 0

        best_score = -1
        best_passage = ""
        best_overlap = 0
        delimiters = ".!?"
        for start in candidate_starts:
            left = 0
            for delimiter in delimiters:
                candidate = normalized.rfind(delimiter, 0, start)
                left = max(left, candidate + 1)

            right_candidates = [normalized.find(delimiter, start) for delimiter in delimiters]
            right_candidates = [candidate for candidate in right_candidates if candidate != -1]
            right = min(right_candidates) + 1 if right_candidates else min(len(normalized), start + window)

            if right - left < 80:
                left = max(0, start - window // 2)
                right = min(len(normalized), start + window // 2)

            snippet = normalized[left:right].strip(" ,;")
            snippet_tokens = set(tokenize(snippet))
            overlap = len(query_tokens & snippet_tokens)
            score = overlap * 10 - abs(start - len(normalized) // 2) * 0.001
            if score > best_score:
                best_score = score
                best_overlap = overlap
                best_passage = snippet

        return best_passage, best_overlap
