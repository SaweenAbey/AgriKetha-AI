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
    """

    def __init__(self):
        # ---------------------------------------------------------
        # Device
        # ---------------------------------------------------------
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        print(f"[Crop Classifier] Using device: {self.device}")

        # ---------------------------------------------------------
        # Project base directory
        # app/crop_classifier.py -> vision-agent/
        # ---------------------------------------------------------
        base_dir = Path(__file__).resolve().parents[1]

        self.model_path = base_dir / "best_crop_classifier.pth"
        self.classes_path = base_dir / "crop_classes.txt"

        # ---------------------------------------------------------
        # Load classes
        # ---------------------------------------------------------
        if not self.classes_path.exists():
            raise FileNotFoundError(
                f"Crop classes file not found: {self.classes_path}"
            )

        with open(self.classes_path, "r", encoding="utf-8") as f:
            self.classes = [
                line.strip()
                for line in f
                if line.strip()
            ]

        if not self.classes:
            raise ValueError("No crop classes found.")

        print(f"[Crop Classifier] Classes: {self.classes}")

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
                f"Crop classifier model not found: {self.model_path}"
            )

        state_dict = torch.load(
            str(self.model_path),
            map_location=self.device
        )

        self.model.load_state_dict(state_dict)

        self.model = self.model.to(self.device)
        self.model.eval()

        # ---------------------------------------------------------
        # Image preprocessing
        # Must match training/testing
        # ---------------------------------------------------------
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        print(
            f"[Crop Classifier] Model loaded successfully: "
            f"{self.model_path.name}"
        )

    # =========================================================
    # PREDICTION
    # =========================================================

    def predict(self, image: Image.Image):
        """
        Predict the crop type.

        Returns:
            crop: predicted crop name
            confidence: prediction confidence
        """

        # Ensure RGB
        image = image.convert("RGB")

        # Preprocess
        image_tensor = self.transform(image).unsqueeze(0)
        image_tensor = image_tensor.to(self.device)

        # Prediction
        with torch.no_grad():
            outputs = self.model(image_tensor)

            probabilities = torch.softmax(
                outputs,
                dim=1
            )

            confidence, predicted_index = torch.max(
                probabilities,
                dim=1
            )

        crop = self.classes[predicted_index.item()]
        confidence_value = confidence.item()

        print(
            f"[Crop Classifier] "
            f"Prediction: {crop} "
            f"| Confidence: {confidence_value:.4f}"
        )

        return crop, confidence_value