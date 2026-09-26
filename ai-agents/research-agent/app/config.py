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

# Query hardening: cap query length and repeated tokens so keyword stuffing
# cannot dominate the embedding or exhaust the encoder.
MAX_QUERY_CHARS = 1000
MAX_TOKEN_REPEATS = 2

# Shared secret expected in the X-Internal-Agent-Key header. When set, only
# the backend orchestrator (which receives the same value) can call Agent 3.
INTERNAL_AGENT_KEY = os.getenv("AGRIKETHA_INTERNAL_AGENT_KEY", "")