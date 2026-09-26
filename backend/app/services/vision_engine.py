"""
In-process fallback for the Vision Agent (Agent 1).

When the Vision Agent microservice on port 8002 is unreachable, the backend
runs the *same* trained models and pipeline in-process
(ai-agents/vision-agent/app/pipeline.py). It never invents a diagnosis:
if the models cannot be loaded, or the image is rejected, an error result is
returned and shown to the farmer.
"""

import contextlib
import importlib
import importlib.util
import io
import sys
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.logging_config import logger

VISION_AGENT_DIR = Path(__file__).resolve().parents[3] / "ai-agents" / "vision-agent"
_PACKAGE = "agriketha_vision_agent"


def _import_vision_module(name: str):
    """
    Import a vision-agent module under an alias package, because the backend
    already owns the top-level package name ``app``.
    """
    if _PACKAGE not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            _PACKAGE,
            VISION_AGENT_DIR / "app" / "__init__.py",
            submodule_search_locations=[str(VISION_AGENT_DIR / "app")],
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[_PACKAGE] = module
        spec.loader.exec_module(module)
    return importlib.import_module(f"{_PACKAGE}.{name}")


@contextlib.contextmanager
def _captured_stdout():
    """
    The vision-agent code prints emoji progress messages, which raise
    UnicodeEncodeError on a Windows cp1252 console. Capture them and forward
    them to the backend log instead.
    """
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            yield
    finally:
        for line in buffer.getvalue().splitlines():
            if line.strip():
                logger.debug("[vision-agent] %s", line)


def _error(message: str) -> Dict[str, Any]:
    return {
        "status": "error",
        "crop": "unknown",
        "prediction": None,
        "confidence": None,
        "severity_percentage": None,
        "severity_level": None,
        "gradcam_base64": None,
        "alternatives": [],
        "message": message,
    }


class IntegratedVisionEngine:
    """Lazily loads the Vision Agent's trained models inside the backend process."""

    def __init__(self):
        self._lock = threading.Lock()
        self._loaded = False
        self._load_error: Optional[str] = None
        self._pipeline = None
        self._vision_model = None
        self._crop_classifier = None

    def _ensure_loaded(self) -> bool:
        with self._lock:
            if self._loaded or self._load_error:
                return self._loaded
            try:
                with _captured_stdout():
                    self._pipeline = _import_vision_module("pipeline")
                    ensemble = _import_vision_module("model_ensemble")
                    classifier = _import_vision_module("crop_classifier")
                    self._vision_model = ensemble.EnsembledVisionModel()
                    self._crop_classifier = classifier.CropClassifier()
                self._loaded = True
                logger.info("Integrated Vision Engine loaded the Vision Agent models in-process.")
            except Exception as exc:
                self._load_error = str(exc)
                logger.error("Integrated Vision Engine could not load vision models: %s", exc)
            return self._loaded

    def analyze_crop_image(
        self,
        image_bytes: bytes,
        filename: str = "leaf.jpg",
        crop_hint: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Diagnose a leaf photo with the real Vision Agent pipeline.

        ``crop_hint`` and ``filename`` are intentionally ignored: the crop is
        detected from the image itself so a misleading hint or filename cannot
        change the diagnosis.
        """
        try:
            from PIL import Image
            image_pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception:
            return _error("The uploaded file could not be read as an image.")

        if not self._ensure_loaded():
            return _error(
                "The vision models are currently unavailable, so the image could not be "
                "diagnosed. Please try again later or consult an agricultural extension officer."
            )

        try:
            with self._lock, _captured_stdout():
                result = self._pipeline.analyze_leaf_image(
                    image_pil, self._vision_model, self._crop_classifier
                )
        except Exception as exc:
            logger.error("Integrated Vision Engine inference error: %s", exc)
            return _error("The image could not be analyzed due to an internal vision error.")

        result["message"] = f"{result.get('message', '')} (Integrated Vision Engine)".strip()
        return result


# Global singleton instance (models load on first use)
vision_engine = IntegratedVisionEngine()
