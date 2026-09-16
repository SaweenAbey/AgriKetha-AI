"""FAISS index persistence and chunk metadata storage."""

import json
from dataclasses import asdict
from pathlib import Path

import faiss
import numpy as np

from .chunker import DocumentChunk


INDEX_FILENAME = "agricultural.index"
METADATA_FILENAME = "metadata.json"


class VectorStore:
    def __init__(self, directory: Path):
        self.directory = directory
        self.index: faiss.Index | None = None
        self.metadata: list[dict] = []

    @property
    def exists(self) -> bool:
        return (self.directory / INDEX_FILENAME).exists() and (
            self.directory / METADATA_FILENAME
        ).exists()

    def build(self, vectors: np.ndarray, chunks: list[DocumentChunk]) -> None:
        if len(vectors) != len(chunks) or len(vectors) == 0:
            raise ValueError("vectors and chunks must be non-empty and have equal length")
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)
        self.metadata = [asdict(chunk) for chunk in chunks]

    def save(self) -> None:
        if self.index is None:
            raise ValueError("build the vector store before saving it")
        self.directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.directory / INDEX_FILENAME))
        (self.directory / METADATA_FILENAME).write_text(
            json.dumps(self.metadata, ensure_ascii=True, indent=2), encoding="utf-8"
        )

    def load(self) -> bool:
        if not self.exists:
            return False
        self.index = faiss.read_index(str(self.directory / INDEX_FILENAME))
        self.metadata = json.loads(
            (self.directory / METADATA_FILENAME).read_text(encoding="utf-8")
        )
        return True

    def search(self, vector: np.ndarray, limit: int) -> list[tuple[dict, float]]:
        if self.index is None or not self.metadata:
            return []
        scores, positions = self.index.search(vector, min(limit, len(self.metadata)))
        return [
            (self.metadata[position], float(score))
            for position, score in zip(positions[0], scores[0])
            if position >= 0
        ]