from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image


class CropClassifier:
    """
    Classifies an uploaded agricultural image as:
    - rice
    - tomato

    Uses the trained MobileNetV3-Small crop classifier.

    Also performs an out-of-distribution (OOD) check to determine
    whether the uploaded image is sufficiently similar to the
    supported rice/tomato image domain.
    """

    # ---------------------------------------------------------
    # OOD similarity threshold
    #
    # Based on the validation tests:
    # Lowest valid crop similarity: 0.5810
    # Car similarity:               0.5483
    # Person similarity:            0.4556
    #
    # 0.56 provides a small separation between the observed
    # unrelated examples and the lowest observed valid crop.
    # ---------------------------------------------------------
    OOD_THRESHOLD = 0.56

    def __init__(self):

        # ---------------------------------------------------------
        # Device
        # ---------------------------------------------------------
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        print(
            f"[Crop Classifier] Using device: {self.device}"
        )

        # ---------------------------------------------------------
        # Project base directory
        #
        # app/crop_classifier.py -> vision-agent/
        # ---------------------------------------------------------
        base_dir = Path(__file__).resolve().parents[1]

        self.model_path = (
            base_dir / "best_crop_classifier.pth"
        )

        self.classes_path = (
            base_dir / "crop_classes.txt"
        )

        self.reference_path = (
            base_dir / "crop_feature_references.pth"
        )

        # ---------------------------------------------------------
        # Load classes
        # ---------------------------------------------------------
        if not self.classes_path.exists():
            raise FileNotFoundError(
                f"Crop classes file not found: "
                f"{self.classes_path}"
            )

        with open(
            self.classes_path,
            "r",
            encoding="utf-8"
        ) as f:

            self.classes = [
                line.strip()
                for line in f
                if line.strip()
            ]

        if not self.classes:
            raise ValueError(
                "No crop classes found."
            )

        print(
            f"[Crop Classifier] Classes: "
            f"{self.classes}"
        )

        # ---------------------------------------------------------
        # Create MobileNetV3-Small
        # Must match training architecture
        # ---------------------------------------------------------
        self.model = models.mobilenet_v3_small(
            weights=None
        )

        self.model.classifier[3] = nn.Linear(
            self.model.classifier[3].in_features,
            len(self.classes)
        )

        # ---------------------------------------------------------
        # Load trained weights
        # ---------------------------------------------------------
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Crop classifier model not found: "
                f"{self.model_path}"
            )

        state_dict = torch.load(
            str(self.model_path),
            map_location=self.device
        )

        self.model.load_state_dict(
            state_dict
        )

        self.model = self.model.to(
            self.device
        )

        self.model.eval()

        # ---------------------------------------------------------
        # Image preprocessing
        # Must match training/testing
        # ---------------------------------------------------------
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[
                    0.485,
                    0.456,
                    0.406
                ],
                std=[
                    0.229,
                    0.224,
                    0.225
                ]
            )
        ])

        print(
            "[Crop Classifier] Model loaded "
            f"successfully: {self.model_path.name}"
        )

        # ---------------------------------------------------------
        # Load OOD feature references
        # ---------------------------------------------------------
        self.references = None

        if self.reference_path.exists():

            self.references = torch.load(
                str(self.reference_path),
                map_location="cpu"
            )

            # Move references to the same device as the model
            self.references = {
                crop: feature.to(self.device)
                for crop, feature
                in self.references.items()
            }

            # Make sure required references exist
            if (
                "rice" not in self.references
                or "tomato" not in self.references
            ):
                raise ValueError(
                    "crop_feature_references.pth must contain "
                    "'rice' and 'tomato' references."
                )

            print(
                "[Crop Classifier] "
                "Feature references loaded successfully"
            )

            print(
                "[Crop Classifier] "
                f"OOD threshold: {self.OOD_THRESHOLD}"
            )

        else:

            print(
                "[Crop Classifier] WARNING: "
                "crop_feature_references.pth not found."
            )

            print(
                "[Crop Classifier] "
                "OOD validation will be unavailable."
            )

    # =========================================================
    # FEATURE EXTRACTION
    # =========================================================

    def extract_features(
        self,
        image: Image.Image
    ):
        """
        Extract the feature representation produced by the
        MobileNetV3-Small backbone.

        This does NOT make a crop prediction.

        Returns:
            Normalized feature vector.
        """

        # ---------------------------------------------------------
        # Ensure RGB
        # ---------------------------------------------------------
        image = image.convert("RGB")

        # ---------------------------------------------------------
        # Preprocess
        # ---------------------------------------------------------
        image_tensor = self.transform(
            image
        ).unsqueeze(0)

        image_tensor = image_tensor.to(
            self.device
        )

        # ---------------------------------------------------------
        # Extract features
        # ---------------------------------------------------------
        with torch.no_grad():

            features = self.model.features(
                image_tensor
            )

            # Global average pooling
            features = self.model.avgpool(
                features
            )

            # Flatten
            features = torch.flatten(
                features,
                1
            )

            # L2 normalize
            features = torch.nn.functional.normalize(
                features,
                p=2,
                dim=1
            )

        return features.squeeze(0)

    # =========================================================
    # OOD / DOMAIN VALIDATION
    # =========================================================

    def validate_crop_domain(
        self,
        image: Image.Image
    ):
        """
        Determine whether the uploaded image belongs to the
        supported rice/tomato image domain.

        Returns:
            (
                is_valid,
                closest_crop,
                similarity,
                message
            )
        """

        # ---------------------------------------------------------
        # Check whether references are available
        # ---------------------------------------------------------
        if self.references is None:

            return (
                True,
                None,
                None,
                "OOD validation unavailable."
            )

        # ---------------------------------------------------------
        # Extract uploaded image features
        # ---------------------------------------------------------
        feature = self.extract_features(
            image
        ).unsqueeze(0)

        # ---------------------------------------------------------
        # Compare with rice reference
        # ---------------------------------------------------------
        rice_similarity = (
            torch.nn.functional.cosine_similarity(
                feature,
                self.references["rice"].unsqueeze(0)
            ).item()
        )

        # ---------------------------------------------------------
        # Compare with tomato reference
        # ---------------------------------------------------------
        tomato_similarity = (
            torch.nn.functional.cosine_similarity(
                feature,
                self.references["tomato"].unsqueeze(0)
            ).item()
        )

        # ---------------------------------------------------------
        # Find closest supported crop
        # ---------------------------------------------------------
        if rice_similarity >= tomato_similarity:

            closest_crop = "rice"
            highest_similarity = rice_similarity

        else:

            closest_crop = "tomato"
            highest_similarity = tomato_similarity

        # ---------------------------------------------------------
        # Print OOD information
        # ---------------------------------------------------------
        print(
            "[Crop Classifier] "
            f"OOD check | "
            f"Rice={rice_similarity:.4f} | "
            f"Tomato={tomato_similarity:.4f} | "
            f"Highest={highest_similarity:.4f}"
        )

        # ---------------------------------------------------------
        # Reject unrelated image
        # ---------------------------------------------------------
        if highest_similarity < self.OOD_THRESHOLD:

            print(
                "[Crop Classifier] "
                "Image rejected as outside "
                "supported crop domain."
            )

            return (
                False,
                "unknown",
                highest_similarity,
                "Please upload a paddy or tomato leaf."
            )

        # ---------------------------------------------------------
        # Valid supported crop domain
        # ---------------------------------------------------------
        print(
            "[Crop Classifier] "
            f"Image accepted as {closest_crop}."
        )

        return (
            True,
            closest_crop,
            highest_similarity,
            "Image belongs to the supported crop domain."
        )

    # =========================================================
    # PREDICTION
    # =========================================================

    def predict(
        self,
        image: Image.Image
    ):
        """
        Predict the crop type.

        Returns:
            crop:
                Predicted crop name.

            confidence:
                Prediction confidence.
        """

        # ---------------------------------------------------------
        # Ensure RGB
        # ---------------------------------------------------------
        image = image.convert("RGB")

        # ---------------------------------------------------------
        # Preprocess
        # ---------------------------------------------------------
        image_tensor = self.transform(
            image
        ).unsqueeze(0)

        image_tensor = image_tensor.to(
            self.device
        )

        # ---------------------------------------------------------
        # Prediction
        # ---------------------------------------------------------
        with torch.no_grad():

            outputs = self.model(
                image_tensor
            )

            probabilities = torch.softmax(
                outputs,
                dim=1
            )

            confidence, predicted_index = torch.max(
                probabilities,
                dim=1
            )

        # ---------------------------------------------------------
        # Get crop name
        # ---------------------------------------------------------
        crop = self.classes[
            predicted_index.item()
        ]

        confidence_value = confidence.item()

        print(
            "[Crop Classifier] "
            f"Prediction: {crop} "
            f"| Confidence: {confidence_value:.4f}"
        )

        return (
            crop,
            confidence_value
        )