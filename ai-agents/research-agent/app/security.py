"""Input hardening for the retrieval pipeline.

- ``normalize_query`` limits keyword stuffing before a query is embedded.
- ``find_injection_markers`` flags document text that tries to issue
  instructions to the downstream LLM (indirect prompt injection).
"""

import hmac
import re

from .config import MAX_QUERY_CHARS, MAX_TOKEN_REPEATS


INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"ignore\s+(all\s+)?(the\s+)?(previous|prior|above)\s+instructions",
        r"disregard\s+(all\s+)?(the\s+)?(previous|prior|above)",
        r"\bsystem\s*(alert|prompt|override|message)\b",
        r"you\s+are\s+now\b",
        r"new\s+instructions\s*:",
        r"</?\s*(system|evidence|instructions?)\s*>",
        r"\bdo\s+not\s+follow\s+(the\s+)?(rules|guidelines)",
    )
]


def normalize_query(query: str) -> str:
    """Collapse whitespace, cap token repetition and truncate the query."""
    counts: dict[str, int] = {}
    kept: list[str] = []
    for token in query.split():
        key = token.lower()
        counts[key] = counts.get(key, 0) + 1
        if counts[key] <= MAX_TOKEN_REPEATS:
            kept.append(token)
    return " ".join(kept)[:MAX_QUERY_CHARS]


def find_injection_markers(text: str) -> list[str]:
    """Return the instruction-like phrases found in a document passage."""
    return [match.group(0) for pattern in INJECTION_PATTERNS for match in pattern.finditer(text)]


def is_valid_agent_key(provided: str | None, expected: str) -> bool:
    """Constant-time comparison of the inter-service shared secret."""
    if not expected:
        return True
    return bool(provided) and hmac.compare_digest(provided, expected)
