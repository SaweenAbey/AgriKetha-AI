import sys
import io
from pathlib import Path
from PIL import Image, ImageDraw

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.services.vision_engine import vision_engine
from app.api.v1.farmer import _generate_vision_advisory

def main():
    print("=" * 60)
    print("AgriKetha-AI Vision Diagnostics Verification Suite")
    print("=" * 60)

    # 1. Test Rice Leaf Image (long aspect ratio with brown necrotic lesions)
    rice_img = Image.new("RGB", (250, 650), color=(60, 150, 50))
    d = ImageDraw.Draw(rice_img)
    d.ellipse([70, 220, 180, 420], fill=(139, 69, 19))
    d.ellipse([95, 270, 155, 370], fill=(180, 170, 160)) # gray necrosis center

    buf = io.BytesIO()
    rice_img.save(buf, format="JPEG")
    rice_bytes = buf.getvalue()

    res = vision_engine.analyze_crop_image(rice_bytes, filename="IMG_2026_09_19_photo.jpg")
    print("1. Unnamed Rice Leaf Scan (e.g. camera photo IMG_2026_09_19_photo.jpg):")
    print(f"   - Identified Crop: {res['crop']}")
    print(f"   - Diagnosis: {res['prediction']}")
    print(f"   - Confidence: {res['confidence'] * 100:.1f}%")
    print(f"   - Severity: {res['severity_level']} ({res['severity_percentage']} pct)")
    print(f"   - Alternatives: {res['alternatives']}")
    print(f"   - Has Grad-CAM Heatmap: {bool(res['gradcam_base64'])}")
    assert res["crop"] == "Rice", f"Expected Rice, got {res['crop']}"

    adv = _generate_vision_advisory(res["prediction"], res["crop"], res["severity_level"])
    print(f"   - DOA Biological Control: {adv['biological_control'][:70]}...")
    print(f"   - DOA Chemical Control: {adv['chemical_control'][:70]}...")
    print(f"   - DOA Cultural Control: {adv['cultural_practices'][:70]}...")

    # 2. Test with explicit Rice Category button
    res_hint = vision_engine.analyze_crop_image(rice_bytes, filename="leaf.png", crop_hint="Rice")
    print("\n2. Rice Leaf with 'Rice' category button selected:")
    print(f"   - Identified Crop: {res_hint['crop']}")
    print(f"   - Diagnosis: {res_hint['prediction']}")
    assert res_hint["crop"] == "Rice"

    # 3. Test with Tomato Category button
    res_tomato = vision_engine.analyze_crop_image(rice_bytes, filename="leaf.png", crop_hint="Tomato")
    print("\n3. Tomato Leaf with 'Tomato' category button selected:")
    print(f"   - Identified Crop: {res_tomato['crop']}")
    print(f"   - Diagnosis: {res_tomato['prediction']}")
    assert res_tomato["crop"] == "Tomato"

    # 4. Test with Chili Category button
    res_chili = vision_engine.analyze_crop_image(rice_bytes, filename="leaf.png", crop_hint="Chili")
    print("\n4. Chili Leaf with 'Chili' category button selected:")
    print(f"   - Identified Crop: {res_chili['crop']}")
    print(f"   - Diagnosis: {res_chili['prediction']}")
    assert res_chili["crop"] == "Chili"

    # 5. Test with Brinjal Category button
    res_brinjal = vision_engine.analyze_crop_image(rice_bytes, filename="leaf.png", crop_hint="Brinjal")
    print("\n5. Brinjal Leaf with 'Brinjal' category button selected:")
    print(f"   - Identified Crop: {res_brinjal['crop']}")
    print(f"   - Diagnosis: {res_brinjal['prediction']}")
    assert res_brinjal["crop"] == "Brinjal"

    print("\n" + "=" * 60)
    print("[PASS] ALL VISION DIAGNOSTIC VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
