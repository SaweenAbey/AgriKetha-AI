from pathlib import Path
import torch
from PIL import Image
from crop_classifier import CropClassifier


# =========================================================
# CONFIGURATION
# =========================================================

DATASET_DIR = Path(
    r"C:\Users\ASUS\Downloads\crop_classifier_dataset\train"
)

OUTPUT_FILE = Path("crop_feature_references.pth")

MAX_IMAGES_PER_CLASS = 500


# =========================================================
# LOAD CLASSIFIER
# =========================================================

print("Loading crop classifier...")

classifier = CropClassifier()


# =========================================================
# BUILD CLASS REFERENCES
# =========================================================

references = {}

for crop in ["rice", "tomato"]:

    crop_dir = DATASET_DIR / crop

    if not crop_dir.exists():
        print(f"WARNING: Dataset folder not found: {crop_dir}")
        continue

    image_files = []

    for extension in ["*.jpg", "*.jpeg", "*.JPG", "*.JPEG", "*.png", "*.PNG"]:
        image_files.extend(crop_dir.glob(extension))

    # Limit number of images
    image_files = image_files[:MAX_IMAGES_PER_CLASS]

    print(
        f"\nProcessing {crop}: "
        f"{len(image_files)} images"
    )

    features = []

    for index, image_path in enumerate(image_files, start=1):

        try:
            image = Image.open(image_path).convert("RGB")

            feature = classifier.extract_features(image)

            features.append(feature.cpu())

            if index % 50 == 0:
                print(
                    f"  Processed {index}/{len(image_files)}"
                )

        except Exception as e:

            print(
                f"  Skipping {image_path.name}: {e}"
            )


    # ---------------------------------------------------------
    # Check whether features were generated
    # ---------------------------------------------------------

    if not features:
        print(
            f"ERROR: No features generated for {crop}"
        )
        continue


    # ---------------------------------------------------------
    # Calculate mean feature vector
    # ---------------------------------------------------------

    feature_matrix = torch.stack(features)

    mean_feature = feature_matrix.mean(dim=0)

    # Normalize reference vector
    mean_feature = torch.nn.functional.normalize(
        mean_feature,
        p=2,
        dim=0
    )


    references[crop] = mean_feature

    print(
        f"✓ {crop} reference created "
        f"using {len(features)} images"
    )


# =========================================================
# SAVE REFERENCES
# =========================================================

if len(references) != 2:

    raise RuntimeError(
        "Could not create references for both rice and tomato."
    )


torch.save(
    references,
    OUTPUT_FILE
)


print("\n========================================")
print("Crop feature references created!")
print("========================================")
print(f"Output: {OUTPUT_FILE.resolve()}")

for crop, feature in references.items():

    print(
        f"{crop}: "
        f"shape={tuple(feature.shape)}, "
        f"norm={feature.norm().item():.4f}"
    )