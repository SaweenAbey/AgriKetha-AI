import torch
from pathlib import Path
from PIL import Image

from app.crop_classifier import CropClassifier


# =========================================================
# CONFIGURATION
# =========================================================

TEST_DIR = Path(
    r"C:\Users\ASUS\Downloads\crop_classifier_dataset\test"
)

MAX_IMAGES = 100


# =========================================================
# LOAD MODEL AND REFERENCES
# =========================================================

classifier = CropClassifier()

references = torch.load(
    "crop_feature_references.pth",
    map_location="cpu"
)


# =========================================================
# TEST ONE CLASS
# =========================================================

def test_class(class_name):

    folder = TEST_DIR / class_name

    image_files = []

    for extension in [
        "*.jpg",
        "*.jpeg",
        "*.JPG",
        "*.JPEG",
        "*.png",
        "*.PNG"
    ]:
        image_files.extend(folder.glob(extension))

    image_files = image_files[:MAX_IMAGES]

    print()
    print("=" * 60)
    print(f"Testing {class_name.upper()}: {len(image_files)} images")
    print("=" * 60)

    results = []

    for index, image_path in enumerate(image_files, start=1):

        try:

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

            highest_similarity = max(
                rice_similarity,
                tomato_similarity
            )

            results.append({
                "file": image_path.name,
                "rice": rice_similarity,
                "tomato": tomato_similarity,
                "highest": highest_similarity
            })

            if index % 20 == 0:
                print(f"Processed {index}/{len(image_files)}")

        except Exception as e:

            print(
                f"Skipping {image_path.name}: {e}"
            )


    # =====================================================
    # RESULTS
    # =====================================================

    if not results:
        print("No valid results.")
        return []

    highest_values = [
        result["highest"]
        for result in results
    ]

    print()
    print(f"{class_name.upper()} RESULTS")

    print(
        f"Minimum similarity: {min(highest_values):.4f}"
    )

    print(
        f"Maximum similarity: {max(highest_values):.4f}"
    )

    print(
        f"Average similarity: {sum(highest_values) / len(highest_values):.4f}"
    )

    # Show lowest 10
    lowest = sorted(
        results,
        key=lambda x: x["highest"]
    )[:10]

    print()
    print("10 LOWEST SIMILARITY IMAGES:")

    for result in lowest:

        print(
            f"{result['file']} | "
            f"Rice={result['rice']:.4f} | "
            f"Tomato={result['tomato']:.4f} | "
            f"Highest={result['highest']:.4f}"
        )

    return results


# =========================================================
# RUN TESTS
# =========================================================

rice_results = test_class("rice")

tomato_results = test_class("tomato")


# =========================================================
# OVERALL VALID-CROP THRESHOLD INFORMATION
# =========================================================

all_results = rice_results + tomato_results

if all_results:

    all_similarities = [
        result["highest"]
        for result in all_results
    ]

    print()
    print("=" * 60)
    print("OVERALL VALID CROP RESULTS")
    print("=" * 60)

    print(
        f"Total images tested: {len(all_results)}"
    )

    print(
        f"Lowest valid-crop similarity: "
        f"{min(all_similarities):.4f}"
    )

    print(
        f"Highest valid-crop similarity: "
        f"{max(all_similarities):.4f}"
    )

    print(
        f"Average valid-crop similarity: "
        f"{sum(all_similarities) / len(all_similarities):.4f}"
    )