"""Evidence retrieval over the persisted agricultural vector store."""

from .config import EMBEDDING_MODEL_NAME, RELEVANCE_THRESHOLD, VECTOR_STORE_DIR
from .embeddings import EmbeddingModel
from .schemas import EvidenceResult
from .vector_store import VectorStore


class RetrievalOutcome:
    """Evidence results plus a transparent explanation of how they were produced."""

    def __init__(
        self,
        results: list[EvidenceResult],
        status: str,
        message: str | None,
        requested_crop: str | None,
        available_crops: list[str],
    ):
        self.results = results
        self.status = status
        self.message = message
        self.requested_crop = requested_crop
        self.available_crops = available_crops


class AgriculturalRetriever:
    def __init__(self):
        self.store = VectorStore(VECTOR_STORE_DIR)
        self.loaded = self.store.load()
        self.embedder = EmbeddingModel(EMBEDDING_MODEL_NAME) if self.loaded else None
        self.known_crops: list[str] = (
            sorted({m["crop"].lower() for m in self.store.metadata if m.get("crop")})
            if self.loaded
            else []
        )

    def retrieve(
        self,
        query: str,
        crop: str | None,
        topic: str | None,
        top_k: int,
    ) -> RetrievalOutcome:
        crop_filter = crop.lower() if crop else None
        topic_filter = topic.lower() if topic else None

        if not self.loaded or self.embedder is None:
            return RetrievalOutcome(
                results=[],
                status="no_relevant_evidence",
                message=(
                    "The agricultural knowledge base is not loaded, so no evidence "
                    "sources are available for this query."
                ),
                requested_crop=crop,
                available_crops=[],
            )

        # The knowledge base only covers a fixed set of crops. Filtering by a
        # crop that has no indexed documents would silently return nothing,
        # so this is reported explicitly instead of returning an empty list
        # with no explanation.
        if crop_filter and crop_filter not in self.known_crops:
            return RetrievalOutcome(
                results=[],
                status="unsupported_crop",
                message=(
                    f"No agricultural documents are indexed for crop '{crop}'. "
                    f"Evidence is currently available for: {', '.join(self.known_crops)}."
                ),
                requested_crop=crop,
                available_crops=self.known_crops,
            )

        query_vector = self.embedder.encode([query])
        candidates = self.store.search(query_vector, max(top_k * 5, 20))
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

        if not results:
            return RetrievalOutcome(
                results=[],
                status="no_relevant_evidence",
                message=(
                    "No knowledge base passages met the relevance threshold "
                    f"(>= {RELEVANCE_THRESHOLD}) for this query."
                ),
                requested_crop=crop,
                available_crops=self.known_crops,
            )

        return RetrievalOutcome(
            results=results,
            status="success",
            message=None,
            requested_crop=crop,
            available_crops=self.known_crops,
        )