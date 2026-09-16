"""Configuration for the local agricultural retrieval service."""

from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS_DIR = PROJECT_ROOT / "knowledge-base" / "documents"
PROCESSED_DIR = PROJECT_ROOT / "knowledge-base" / "processed"
VECTOR_STORE_DIR = PROJECT_ROOT / "vector-store"

EMBEDDING_MODEL_NAME = os.getenv(
    "RESEARCH_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
RELEVANCE_THRESHOLD = float(os.getenv("RESEARCH_RELEVANCE_THRESHOLD", "0.35"))
DEFAULT_TOP_K = 5
MAX_TOP_K = 20
CHUNK_SIZE_WORDS = 180
CHUNK_OVERLAP_WORDS = 30