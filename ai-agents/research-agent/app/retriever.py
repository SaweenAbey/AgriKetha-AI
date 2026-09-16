"""Evidence retrieval over the persisted agricultural vector store."""

from .config import EMBEDDING_MODEL_NAME, RELEVANCE_THRESHOLD, VECTOR_STORE_DIR
from .embeddings import EmbeddingModel
from .schemas import EvidenceResult
from .vector_store import VectorStore


class AgriculturalRetriever:
    def __init__(self):
        self.store = VectorStore(VECTOR_STORE_DIR)
        self.loaded = self.store.load()
        self.embedder = EmbeddingModel(EMBEDDING_MODEL_NAME) if self.loaded else None

    def retrieve(
        self,
        query: str,
        crop: str | None,
        topic: str | None,
        top_k: int,
    ) -> list[EvidenceResult]:
        if not self.loaded or self.embedder is None:
            return []

        query_vector = self.embedder.encode([query])
        candidates = self.store.search(query_vector, max(top_k * 5, 20))
        crop_filter = crop.lower() if crop else None
        topic_filter = topic.lower() if topic else None
        results = []
        for metadata, score in candidates:
            if crop_filter and metadata["crop"].lower() != crop_filter:
                continue
            if topic_filter and metadata["topic"].lower() != topic_filter:
                continue
            if score < RELEVANCE_THRESHOLD:
                continue
            results.append(
                EvidenceResult(
                    content=metadata["text"],
                    source=metadata["source"],
                    page=metadata["page"],
                    crop=metadata["crop"],
                    topic=metadata["topic"],
                    similarity_score=round(score, 4),
                )
            )
            if len(results) == top_k:
                break
        return results