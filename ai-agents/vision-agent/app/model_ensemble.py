import torch
import torch.nn as nn
from torchvision import models
import numpy as np
import os


class EnsembledVisionModel:
    """
    Vision model manager for AgriKetha.

    Loads:
    1. Disease specialist model
    2. Nutrition specialist model
    3. Pest specialist model
    4. Tomato disease model

    The original Disease/Nutrition/Pest models are kept as
    a separate ensemble.

    The Tomato model is handled separately because its
    classes are specific to tomato leaves.
    """

    def __init__(self):
        # ---------------------------------------------------------
        # Device
        # ---------------------------------------------------------
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        print(f"Using device: {self.device}")

        # ---------------------------------------------------------
        # Store all models
        # ---------------------------------------------------------
        self.models = {}

        # Combined class names for the original specialist models
        self.class_names = {}

        # ---------------------------------------------------------
        # 1. Load Disease Model
        # ---------------------------------------------------------
        self.models["disease"] = self._load_model(
            "best_disease_model.pth",
            "disease_classes.txt"
        )

        # ---------------------------------------------------------
        # 2. Load Nutrition Model
        # ---------------------------------------------------------
        self.models["nutrition"] = self._load_model(
            "best_nutrition_model.pth",
            "nutrition_classes.txt"
        )

        # ---------------------------------------------------------
        # 3. Load Pest Model
        # ---------------------------------------------------------
        self.models["pest"] = self._load_model(
            "best_pest_model.pth",
            "pest_classes.txt"
        )

        # ---------------------------------------------------------
        # 4. Load Tomato Model
        # ---------------------------------------------------------
        self.models["tomato"] = self._load_model(
            "best_tomato_model.pth",
            "tomato_classes.txt"
        )

        # ---------------------------------------------------------
        # Combine original specialist class names
        #
        # Do NOT include tomato here because tomato has its own
        # dedicated prediction path.
        # ---------------------------------------------------------
        self.class_names = {}

        for key in ["disease", "nutrition", "pest"]:
            if self.models[key] is not None:
                self.class_names.update(
                    self.models[key]["class_map"]
                )

        # ---------------------------------------------------------
        # Model used for Grad-CAM
        # ---------------------------------------------------------
        self.current_model_key = "disease"

        self.target_layers = []

        # ---------------------------------------------------------
        # Print model status
        # ---------------------------------------------------------
        loaded_models = []

        for key, model_data in self.models.items():
            if model_data is not None:
                loaded_models.append(key)

        print(
            f"✅ Vision Models Ready! "
            f"Loaded models: {', '.join(loaded_models)}"
        )

        print(
            f"✅ Original specialist classes: "
            f"{len(self.class_names)}"
        )

        if self.models["tomato"] is not None:
            tomato_classes = len(
                self.models["tomato"]["class_map"]
            )

            print(
                f"🍅 Tomato model ready with "
                f"{tomato_classes} classes"
            )

    # ============================================================
    # LOAD MODEL
    # ============================================================

    def _load_model(self, weights_path, class_path):
        """
        Helper method to load one MobileNetV3 model.

        The architecture must exactly match the architecture
        used during training.
        """

        # ---------------------------------------------------------
        # Check files
        # ---------------------------------------------------------
        if not os.path.exists(weights_path):
            print(
                f"⚠️ Warning: {weights_path} not found!"
            )
            return None

        if not os.path.exists(class_path):
            print(
                f"⚠️ Warning: {class_path} not found!"
            )
            return None

        # ---------------------------------------------------------
        # Load class names
        # ---------------------------------------------------------
        with open(class_path, "r") as f:
            class_list = [
                line.strip()
                for line in f.readlines()
                if line.strip()
            ]

        class_map = {
            i: name
            for i, name in enumerate(class_list)
        }

        # ---------------------------------------------------------
        # Create MobileNetV3 Large
        #
        # This matches the training architecture.
        # ---------------------------------------------------------
        model = models.mobilenet_v3_large(
            weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V1
        )

        num_classes = len(class_list)

        # ---------------------------------------------------------
        # Replace classifier
        # ---------------------------------------------------------
        model.classifier = nn.Sequential(
            nn.Linear(960, 1280),
            nn.Hardswish(),
            nn.Dropout(0.2),
            nn.Linear(1280, num_classes)
        )

        # ---------------------------------------------------------
        # Load trained weights
        # ---------------------------------------------------------
        model.load_state_dict(
            torch.load(
                weights_path,
                map_location=self.device
            )
        )

        # ---------------------------------------------------------
        # Move to device
        # ---------------------------------------------------------
        model = model.to(self.device)

        # ---------------------------------------------------------
        # Evaluation mode
        # ---------------------------------------------------------
        model.eval()

        print(
            f"✅ Loaded {os.path.basename(weights_path)}: "
            f"{len(class_list)} classes"
        )

        return {
            "model": model,
            "class_map": class_map
        }

    # ============================================================
    # ORIGINAL RICE SPECIALIST ENSEMBLE
    # ============================================================

    def predict(self, image_tensor: torch.Tensor):
        """
        Run the original Disease, Nutrition and Pest models.

        The prediction with the highest confidence is returned.

        This method is preserved from the original system.
        """

        all_predictions = []

        # ---------------------------------------------------------
        # Run each original specialist model
        # ---------------------------------------------------------
        for key in ["disease", "nutrition", "pest"]:

            if self.models[key] is None:
                continue

            model = self.models[key]["model"]
            class_map = self.models[key]["class_map"]

            # Make sure tensor is on correct device
            input_tensor = image_tensor.to(self.device)

            with torch.no_grad():

                outputs = model(input_tensor)

                probs = torch.nn.functional.softmax(
                    outputs,
                    dim=1
                )

                top_prob, top_idx = torch.topk(
                    probs,
                    1,
                    dim=1
                )

                confidence = float(
                    top_prob[0][0].cpu().item()
                )

                class_idx = int(
                    top_idx[0][0].cpu().item()
                )

                prediction = class_map.get(
                    class_idx,
                    f"{key}_unknown"
                )

                all_predictions.append({
                    "category": key,
                    "prediction": prediction,
                    "confidence": confidence
                })

        # ---------------------------------------------------------
        # Make sure at least one model exists
        # ---------------------------------------------------------
        if not all_predictions:
            raise RuntimeError(
                "No Disease, Nutrition or Pest models are loaded."
            )

        # ---------------------------------------------------------
        # Sort by confidence
        # ---------------------------------------------------------
        all_predictions.sort(
            key=lambda x: x["confidence"],
            reverse=True
        )

        # ---------------------------------------------------------
        # Highest confidence prediction
        # ---------------------------------------------------------
        top = all_predictions[0]

        # ---------------------------------------------------------
        # Build alternatives
        # ---------------------------------------------------------
        alternatives = []

        for pred in all_predictions[1:3]:

            alternatives.append({
                "disease": pred["prediction"],
                "confidence": pred["confidence"]
            })

        # ---------------------------------------------------------
        # Remember model for Grad-CAM
        # ---------------------------------------------------------
        self.current_model_key = top["category"]

        return (
            top["prediction"],
            top["confidence"],
            alternatives
        )

    # ============================================================
    # TOMATO MODEL
    # ============================================================

    def predict_tomato(self, image_tensor: torch.Tensor):
        """
        Run the dedicated tomato disease model.

        This model has 10 tomato classes:

        - Tomato___Bacterial_spot
        - Tomato___Early_blight
        - Tomato___healthy
        - Tomato___Late_blight
        - Tomato___Leaf_Mold
        - Tomato___Septoria_leaf_spot
        - Tomato___Spider_mites Two-spotted_spider_mite
        - Tomato___Target_Spot
        - Tomato___Tomato_mosaic_virus
        - Tomato___Tomato_Yellow_Leaf_Curl_Virus

        Returns:
            prediction
            confidence
            alternatives
        """

        # ---------------------------------------------------------
        # Check tomato model
        # ---------------------------------------------------------
        tomato_model_data = self.models.get("tomato")

        if tomato_model_data is None:
            raise RuntimeError(
                "Tomato model is not loaded. "
                "Check best_tomato_model.pth and "
                "tomato_classes.txt."
            )

        model = tomato_model_data["model"]

        class_map = tomato_model_data["class_map"]

        # ---------------------------------------------------------
        # Move image to correct device
        # ---------------------------------------------------------
        input_tensor = image_tensor.to(self.device)

        # ---------------------------------------------------------
        # Make prediction
        # ---------------------------------------------------------
        with torch.no_grad():

            outputs = model(input_tensor)

            probabilities = torch.nn.functional.softmax(
                outputs,
                dim=1
            )

            # Get top 3 predictions
            top_k = min(
                3,
                len(class_map)
            )

            top_probabilities, top_indices = torch.topk(
                probabilities,
                top_k,
                dim=1
            )

        predictions = []

        # ---------------------------------------------------------
        # Convert predictions to readable format
        # ---------------------------------------------------------
        for i in range(top_k):

            class_index = int(
                top_indices[0][i].cpu().item()
            )

            confidence = float(
                top_probabilities[0][i].cpu().item()
            )

            prediction = class_map.get(
                class_index,
                "tomato_unknown"
            )

            predictions.append({
                "prediction": prediction,
                "confidence": confidence
            })

        # ---------------------------------------------------------
        # Main prediction
        # ---------------------------------------------------------
        top_prediction = predictions[0]

        # ---------------------------------------------------------
        # Alternatives
        # ---------------------------------------------------------
        alternatives = []

        for prediction in predictions[1:]:

            alternatives.append({
                "disease": prediction["prediction"],
                "confidence": prediction["confidence"]
            })

        # ---------------------------------------------------------
        # Remember tomato model for Grad-CAM
        # ---------------------------------------------------------
        self.current_model_key = "tomato"

        return (
            top_prediction["prediction"],
            top_prediction["confidence"],
            alternatives
        )

    # ============================================================
    # GRAD-CAM
    # ============================================================

    def generate_gradcam(
        self,
        image_tensor: torch.Tensor,
        target_class: int
    ):
        """
        Generate Grad-CAM using the model that produced
        the current prediction.
        """

        try:

            from pytorch_grad_cam import GradCAM

            from pytorch_grad_cam.utils.image import (
                show_cam_on_image
            )

            # -----------------------------------------------------
            # Get current model
            # -----------------------------------------------------
            model_dict = self.models.get(
                self.current_model_key
            )

            if model_dict is None:

                print(
                    "⚠️ Grad-CAM model not found."
                )

                return np.random.rand(
                    224,
                    224,
                    3
                ).astype(np.float32)

            model = model_dict["model"]

            # -----------------------------------------------------
            # MobileNetV3 final feature layer
            # -----------------------------------------------------
            target_layers = [
                model.features[-1]
            ]

            # -----------------------------------------------------
            # Convert normalized tensor back to image
            # -----------------------------------------------------
            image_np = (
                image_tensor
                .squeeze(0)
                .permute(1, 2, 0)
                .cpu()
                .numpy()
            )

            mean = np.array([
                0.485,
                0.456,
                0.406
            ])

            std = np.array([
                0.229,
                0.224,
                0.225
            ])

            image_np = (
                std * image_np
                + mean
            )

            image_np = np.clip(
                image_np,
                0,
                1
            )

            # -----------------------------------------------------
            # Create Grad-CAM
            # -----------------------------------------------------
            cam = GradCAM(
                model=model,
                target_layers=target_layers
            )

            grayscale_cam = cam(
                input_tensor=image_tensor.to(
                    self.device
                ),
                targets=[target_class]
            )

            grayscale_cam = grayscale_cam[0, :]

            # -----------------------------------------------------
            # Overlay heatmap
            # -----------------------------------------------------
            visualization = show_cam_on_image(
                image_np,
                grayscale_cam,
                use_rgb=True
            )

            return visualization

        except Exception as e:

            print(
                f"⚠️ Grad-CAM error: {e}"
            )

            return np.random.rand(
                224,
                224,
                3
            ).astype(np.float32)

    # ============================================================
    # SEVERITY ESTIMATION
    # ============================================================

    def estimate_severity(self, heatmap):
        """
        Estimate severity from the Grad-CAM heatmap.
        """

        if heatmap is None:
            return 25.0, "Moderate"

        try:

            # -----------------------------------------------------
            # Calculate affected area
            # -----------------------------------------------------
            affected_area = np.sum(
                heatmap[:, :, 0] > 0.5
            )

            total_area = (
                heatmap.shape[0]
                * heatmap.shape[1]
            )

            severity_pct = (
                affected_area
                / total_area
            ) * 100

            # -----------------------------------------------------
            # Severity level
            # -----------------------------------------------------
            if severity_pct < 10:

                level = "Mild (Early Stage)"

            elif severity_pct < 40:

                level = "Moderate (Spreading)"

            else:

                level = "Severe (Critical Action Needed)"

            return (
                round(severity_pct, 2),
                level
            )

        except Exception:

            return 25.0, "Moderate"