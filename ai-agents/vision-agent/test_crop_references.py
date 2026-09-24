import torch
from pathlib import Path
from PIL import Image

from app.crop_classifier import CropClassifier


# ---------------------------------------------------------
# Load classifier
# ---------------------------------------------------------

classifier = CropClassifier()


# ---------------------------------------------------------
# Load reference features
# ---------------------------------------------------------

reference_file = Path("crop_feature_references.pth")

references = torch.load(
    reference_file,
    map_location="cpu"
)


# ---------------------------------------------------------
# Test images
# ---------------------------------------------------------

tests = {
    "Car": r"C:\Users\ASUS\Downloads\Car.jpg",

    "Person": r"C:\Users\ASUS\Downloads\men.jpg",

    "Rice": r"C:\Users\ASUS\Downloads\RRDI_BrownSpot5-1.jpg",

    "Tomato": r"C:\Users\ASUS\Downloads\archive\Tomato Leaf Disease\train\Tomato___Septoria_leaf_spot\image (83).JPG"
}


# ---------------------------------------------------------
# Calculate similarities
# ---------------------------------------------------------

print()
print("=" * 60)
print("CROP REFERENCE SIMILARITY TEST")
print("=" * 60)


for name, image_path in tests.items():

    print()
    print(f"Testing: {name}")

    image = Image.open(image_path).convert("RGB")

    feature = classifier.extract_features(image)

    feature = feature.unsqueeze(0)

    rice_reference = references["rice"].unsqueeze(0)

    tomato_reference = references["tomato"].unsqueeze(0)


    rice_similarity = torch.nn.functional.cosine_similarity(
        feature,
        rice_reference
    ).item()


    tomato_similarity = torch.nn.functional.cosine_similarity(
        feature,
        tomato_reference
    ).item()


    print(f"  Rice similarity:   {rice_similarity:.4f}")
    print(f"  Tomato similarity: {tomato_similarity:.4f}")


    if rice_similarity > tomato_similarity:
        print("  Closest reference: RICE")
    else:
        print("  Closest reference: TOMATO")


print()
print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)