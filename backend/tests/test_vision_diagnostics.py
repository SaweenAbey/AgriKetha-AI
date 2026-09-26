import sys
import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.services.vision_engine import vision_engine
from app.api.v1.farmer import _generate_vision_advisory


def _png_bytes(image: Image.Image) -> bytes:
    # Add texture so flat synthetic shapes pass the blur/quality check
    rng = np.random.default_rng(0)
    arr = np.asarray(image, dtype=np.int16) + rng.integers(-25, 26, size=(image.height, image.width, 3))
    buf = io.BytesIO()
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(buf, format="PNG")
    return buf.getvalue()


def _red_fruit_image() -> bytes:
    """Two ripe tomato-like fruits against green foliage."""
    img = Image.new("RGB", (400, 400), color=(60, 120, 50))
    d = ImageDraw.Draw(img)
    d.ellipse([40, 90, 210, 300], fill=(215, 45, 25))
    d.ellipse([190, 110, 360, 320], fill=(225, 60, 30))
    return _png_bytes(img)


def _leaf_image() -> bytes:
    """Green leaf blade with brown necrotic lesions."""
    img = Image.new("RGB", (250, 650), color=(60, 150, 50))
    d = ImageDraw.Draw(img)
    d.ellipse([70, 220, 180, 420], fill=(139, 69, 19))
    d.ellipse([95, 270, 155, 370], fill=(180, 170, 160))
    return _png_bytes(img)


def test_fruit_photo_is_rejected_not_misdiagnosed():
    res = vision_engine.analyze_crop_image(_red_fruit_image(), filename="rice_blast.jpg")
    assert res["status"] == "error"
    assert "fruit" in res["message"].lower()
    assert res["prediction"] is None and res["confidence"] is None


def test_crop_hint_and_filename_cannot_force_a_diagnosis():
    leaf = _leaf_image()
    by_hint = vision_engine.analyze_crop_image(leaf, filename="leaf.png", crop_hint="Brinjal")
    by_name = vision_engine.analyze_crop_image(leaf, filename="brinjal_borer.png")
    for res in (by_hint, by_name):
        assert res.get("crop") != "Brinjal"
        if res["status"] == "success":
            assert res["crop"] in {"rice", "tomato"}
            assert 0.0 <= res["confidence"] <= 1.0


def test_unreadable_upload_returns_error():
    res = vision_engine.analyze_crop_image(b"not an image")
    assert res["status"] == "error"


def test_success_results_come_from_real_models():
    res = vision_engine.analyze_crop_image(_leaf_image(), filename="IMG_2026_09_19_photo.jpg")
    if res["status"] == "success":
        assert res["crop"] in {"rice", "tomato"}
        # Hard-coded placeholder values of the old engine must never appear
        assert res["confidence"] not in {0.942, 0.938, 0.945}
        adv = _generate_vision_advisory(res["prediction"], res["crop"], res["severity_level"])
        assert adv["disease_name"] == res["prediction"]
    else:
        assert res["message"]


def main():
    print("=" * 60)
    print("AgriKetha-AI Vision Diagnostics Verification Suite")
    print("=" * 60)
    for test in (
        test_fruit_photo_is_rejected_not_misdiagnosed,
        test_crop_hint_and_filename_cannot_force_a_diagnosis,
        test_unreadable_upload_returns_error,
        test_success_results_come_from_real_models,
    ):
        test()
        print(f"[PASS] {test.__name__}")


if __name__ == "__main__":
    main()
