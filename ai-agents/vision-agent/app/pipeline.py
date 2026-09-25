"""
End-to-end leaf image analysis shared by the Vision Agent API and the
backend's in-process fallback, so both always produce the same diagnosis.

Only relative imports are used so the backend can load this package under a
different name (both services call their package ``app``).
"""

from typing import Any, Optional

import cv2
import numpy as np
from PIL import Image

from .preprocess import preprocess_image, validate_image


SUPPORTED_CROPS = ["rice", "tomato"]

# A photo where this share of pixels is saturated red/orange shows fruit
# (e.g. ripe tomatoes), not a leaf. Leaf lesions are brown/yellow, not
# saturated red, and the disease models were trained on leaves only, so they
# return confident but meaningless labels for fruit.
FRUIT_PIXEL_THRESHOLD = 0.20


def fruit_pixel_fraction(image_pil: Image.Image) -> float:
    """Share of pixels that are saturated red/orange (ripe fruit colours)."""
    small = np.array(image_pil.convert("RGB").resize((224, 224)))
    hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
    hue = hsv[..., 0].astype(int)
    sat = hsv[..., 1] / 255.0
    val = hsv[..., 2] / 255.0
    red = ((hue <= 12) | (hue >= 165)) & (sat > 0.45) & (val > 0.30)
    return float(red.mean())


def _find_class_index(vision_model, prediction: str) -> Optional[int]:
    """Class index of ``prediction`` in the model that produced it."""
    model_key = getattr(vision_model, "current_model_key", None)
    model_data = (getattr(vision_model, "models", None) or {}).get(model_key)
    if model_data is None:
        return None
    for idx, class_name in model_data.get("class_map", {}).items():
        if class_name == prediction:
            return idx
    return None


def _error(message: str, crop: str = "unknown") -> dict[str, Any]:
    return {
        "status": "error",
        "crop": crop,
        "prediction": None,
        "confidence": None,
        "severity_percentage": None,
        "severity_level": None,
        "gradcam_base64": None,
        "alternatives": [],
        "message": message,
    }


def gradcam_to_base64(gradcam_image: np.ndarray) -> str:
    """Encode a Grad-CAM overlay (0-1 floats or 0-255) as a base64 PNG."""
    import base64
    import io

    img = np.asarray(gradcam_image, dtype=np.float32)
    if img.max() <= 1.0:
        img = img * 255.0
    buffered = io.BytesIO()
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def analyze_leaf_image(image_pil: Image.Image, vision_model, crop_classifier) -> dict[str, Any]:
    """
    Validate, route and diagnose a crop leaf photo.

    1. Image quality validation
    2. Leaf gate: reject fruit photos the leaf models cannot diagnose
    3. Crop-domain (OOD) validation
    4. Rice / tomato crop classification
    5. Crop-specific disease model
    6. Grad-CAM and severity estimation
    """
    image_pil = image_pil.convert("RGB")

    is_valid, validation_message = validate_image(np.array(image_pil))
    if not is_valid:
        return _error(validation_message)

    fruit_fraction = fruit_pixel_fraction(image_pil)
    if fruit_fraction >= FRUIT_PIXEL_THRESHOLD:
        return _error(
            f"This photo appears to show fruit ({fruit_fraction:.0%} of the image is red/orange "
            "fruit colour), not a leaf. The vision models are trained on rice and tomato "
            "LEAVES only and cannot reliably diagnose fruit diseases. Please upload a close-up "
            "photo of an affected leaf."
        )

    domain_valid, _, _, domain_message = crop_classifier.validate_crop_domain(image_pil)
    if not domain_valid:
        return _error(domain_message)

    crop, crop_confidence = crop_classifier.predict(image_pil)
    crop = crop.lower().strip()
    if crop not in SUPPORTED_CROPS:
        return _error(
            f"Unsupported detected crop '{crop}'. Supported crops are: {', '.join(SUPPORTED_CROPS)}."
        )

    image_tensor = preprocess_image(image_pil)
    if crop == "tomato":
        prediction, confidence, alternatives = vision_model.predict_tomato(image_tensor)
    else:
        prediction, confidence, alternatives = vision_model.predict(image_tensor)

    gradcam_base64 = None
    severity_pct = None
    severity_level = None
    class_idx = _find_class_index(vision_model, prediction)
    if class_idx is not None:
        try:
            gradcam_image = vision_model.generate_gradcam(image_tensor, class_idx)
            if gradcam_image is not None:
                gradcam_base64 = gradcam_to_base64(gradcam_image)
                severity_pct, severity_level = vision_model.estimate_severity(gradcam_image)
        except Exception as exc:  # Grad-CAM must never break the diagnosis
            print(f"[Vision Pipeline] Grad-CAM warning: {exc}")

    return {
        "status": "success",
        "crop": crop,
        "prediction": prediction,
        "confidence": confidence,
        "severity_percentage": severity_pct,
        "severity_level": severity_level,
        "gradcam_base64": gradcam_base64,
        "alternatives": [
            {"disease": alt["disease"], "confidence": alt["confidence"]} for alt in alternatives
        ],
        "message": (
            f"Image analyzed successfully. Crop automatically detected as "
            f"{crop} with {crop_confidence * 100:.2f}% confidence."
        ),
    }
