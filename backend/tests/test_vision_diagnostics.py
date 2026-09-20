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

    # 6. Test with Potato Tuber / Scab Image
    potato_img = Image.new("RGB", (320, 260), color=(220, 180, 80)) # golden tan potato skin
    d_p = ImageDraw.Draw(potato_img)
    d_p.ellipse([80, 70, 140, 130], fill=(110, 60, 20)) # brown scab spot
    d_p.ellipse([180, 120, 240, 170], fill=(95, 50, 15)) # brown scab spot

    buf_p = io.BytesIO()
    potato_img.save(buf_p, format="JPEG")
    potato_bytes = buf_p.getvalue()

    res_potato = vision_engine.analyze_crop_image(potato_bytes, filename="potato_photo.jpg")
    print("\n6. Potato Photo Scan (potato_photo.jpg):")
    print(f"   - Identified Crop: {res_potato['crop']}")
    print(f"   - Diagnosis: {res_potato['prediction']}")
    print(f"   - Confidence: {res_potato['confidence'] * 100:.1f}%")
    assert res_potato["crop"] == "Potato"
    assert "Scab" in res_potato["prediction"] or "Potato" in res_potato["prediction"]

    adv_potato = _generate_vision_advisory(res_potato["prediction"], res_potato["crop"], res_potato["severity_level"])
    print(f"   - DOA Scab Control: {adv_potato['biological_control'][:70]}...")
    assert "Trichoderma" in adv_potato["biological_control"] or "tuber" in adv_potato["biological_control"]

    # 7. Test with Non-Leaf / Unrelated Image (e.g. gray wall or car or unrelated image)
    non_leaf_img = Image.new("RGB", (300, 300), color=(180, 180, 210)) # solid bluish gray, no foliage
    d_nl = ImageDraw.Draw(non_leaf_img)
    d_nl.rectangle([50, 50, 250, 250], fill=(70, 70, 80)) # dark square

    buf_nl = io.BytesIO()
    non_leaf_img.save(buf_nl, format="JPEG")
    non_leaf_bytes = buf_nl.getvalue()

    res_nl = vision_engine.analyze_crop_image(non_leaf_bytes, filename="random_object.jpg")
    print("\n6. Non-Leaf / Unrelated Photo Scan (random_object.jpg):")
    print(f"   - Status: {res_nl['status']}")
    print(f"   - Is Recognized: {res_nl['is_recognized']}")
    print(f"   - Identified Crop: {res_nl['crop']}")
    print(f"   - Diagnosis: {res_nl['prediction']}")
    print(f"   - Message: {res_nl['message']}")
    assert res_nl["status"] == "unrecognized"
    assert res_nl["is_recognized"] is False
    assert "Not in Knowledge Base" in res_nl["prediction"]

    adv_nl = _generate_vision_advisory(res_nl["prediction"], res_nl["crop"], res_nl["severity_level"])
    print(f"   - Advisory Disease Title: {adv_nl['disease_name']}")
    print(f"   - Advisory Guidance: {adv_nl['biological_control']}")
    assert "No crop leaf identified" in adv_nl["biological_control"]

    print("\n" + "=" * 60)
    print("[PASS] ALL VISION DIAGNOSTIC VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
