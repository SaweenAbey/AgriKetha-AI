from PIL import Image

from app.crop_classifier import CropClassifier


# ---------------------------------------------------------
# Load classifier
# ---------------------------------------------------------

classifier = CropClassifier()


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
# Run OOD validation
# ---------------------------------------------------------

print()
print("=" * 65)
print("OOD / CROP DOMAIN VALIDATION TEST")
print("=" * 65)


for name, image_path in tests.items():

    print()
    print(f"Testing: {name}")
    print("-" * 65)

    image = Image.open(image_path).convert("RGB")

    is_valid, crop, similarity, message = (
        classifier.validate_crop_domain(image)
    )

    print(f"Valid:       {is_valid}")
    print(f"Crop:        {crop}")
    print(f"Similarity:  {similarity:.4f}")
    print(f"Message:     {message}")


print()
print("=" * 65)
print("TEST COMPLETE")
print("=" * 65)