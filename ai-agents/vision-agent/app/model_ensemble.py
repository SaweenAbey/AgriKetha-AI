import os
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torchvision import models

# Friendly label mapping for Rice diseases, pests, and deficiencies
FRIENDLY_NAMES = {
    "Disease_Brownspot": "Rice Brown Spot (Bipolaris oryzae)",
    "Disease_Bacterialblight": "Rice Bacterial Leaf Blight (Xanthomonas oryzae)",
    "Disease_Blast": "Rice Blast (Magnaporthe oryzae)",
    "Disease_Tungro": "Rice Tungro Virus (RTV)",
    "Nutrition_Nitrogen(N)": "Rice Nitrogen (N) Deficiency",
    "Nutrition_Phosphorus(P)": "Rice Phosphorus (P) Deficiency",
    "Nutrition_Potassium(K)": "Rice Potassium (K) Deficiency",
    "Pest_Brown_Planthopper": "Rice Brown Planthopper (Nilaparvata lugens)",
    "Pest_Green_Leafhoppers": "Rice Green Leafhopper (Nephotettix virescens)",
    "Pest_LEAF_FOLDERS": "Rice Leaf Folder (Cnaphalocrocis medinalis)",
    "Pest_Rice_Bug": "Rice Bug (Leptocorisa oratoria)",
    "Pest_Stemz_Borer": "Rice Yellow Stem Borer (Scirpophaga incertulas)",
    "Pest_Whorl_Maggot": "Rice Whorl Maggot (Hydrellia philippina)",
}

# Rice specialist models used by the ensemble ("balanced" is optional/auxiliary)
RICE_MODEL_KEYS = ["disease", "nutrition", "pest", "balanced"]

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406])
IMAGENET_STD = np.array([0.229, 0.224, 0.225])


def friendly_name(raw_name: str) -> str:
    """Convert a raw class label into a readable name."""
    if raw_name in FRIENDLY_NAMES:
        return FRIENDLY_NAMES[raw_name]
    # e.g. "Tomato___Early_blight" -> "Tomato Early blight"
    return " ".join(raw_name.replace("___", " ").replace("_", " ").split())


class EnsembledVisionModel:
    """
    Vision model manager for AgriKetha.

    Loads:
    1. Disease specialist model   (rice)
    2. Nutrition specialist model (rice)
    3. Pest specialist model      (rice)
    4. Balanced unified model     (rice, optional auxiliary)
    5. Tomato disease model

    The rice models are combined as an ensemble (highest confidence wins).
    The Tomato model is handled separately because its classes are
    specific to tomato leaves.
    """

    def __init__(self):
        # ---------------------------------------------------------
        # Device
        # ---------------------------------------------------------
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[Vision Model] Using device: {self.device}")

        # Model files live one folder above app/
        base_dir = Path(__file__).resolve().parents[1]

        # ---------------------------------------------------------
        # Load all models
        # ---------------------------------------------------------
        self.models = {
            "disease": self._load_model(
                base_dir / "best_disease_model.pth",
                base_dir / "disease_classes.txt",
            ),
            "nutrition": self._load_model(
                base_dir / "best_nutrition_model.pth",
                base_dir / "nutrition_classes.txt",
            ),
            "pest": self._load_model(
                base_dir / "best_pest_model.pth",
                base_dir / "pest_classes.txt",
            ),
            "balanced": self._load_model(
                base_dir / "best_rice_balanced_model.pth",
                base_dir / "class_names.txt",
            ),
            "tomato": self._load_model(
                base_dir / "best_tomato_model.pth",
                base_dir / "tomato_classes.txt",
            ),
        }

        # ---------------------------------------------------------
        # Combine rice class names (tomato has its own path)
        # ---------------------------------------------------------
        self.class_names = {}
        for key in RICE_MODEL_KEYS:
            if self.models.get(key) is not None:
                self.class_names.update(self.models[key]["class_map"])

        # ---------------------------------------------------------
        # State used for Grad-CAM
        # ---------------------------------------------------------
        self.current_model_key = "disease"
        self.current_class_idx = None
        self.last_grayscale_cam = None

        # ---------------------------------------------------------
        # Print model status
        # ---------------------------------------------------------
        loaded = [k for k, v in self.models.items() if v is not None]
        print(f"✅ Vision Models Ready! Loaded models: {', '.join(loaded) or 'none'}")
        print(f"✅ Rice specialist classes: {len(self.class_names)}")

        if self.models["tomato"] is not None:
            print(f"🍅 Tomato model ready with {self.models['tomato']['num_classes']} classes")

    # ============================================================
    # LOAD MODEL
    # ============================================================

    def _load_model(self, weights_path, class_path):
        """
        Load one MobileNetV3-Large model with its class mapping.
        The architecture must exactly match the one used in training.
        Returns None if files are missing or loading fails.
        """
        weights_path = Path(weights_path)
        class_path = Path(class_path)

        if not weights_path.exists():
            print(f"⚠️ Warning: {weights_path.name} not found!")
            return None

        if not class_path.exists():
            print(f"⚠️ Warning: {class_path.name} not found!")
            return None

        try:
            with open(class_path, "r", encoding="utf-8") as f:
                class_list = [line.strip() for line in f if line.strip()]

            class_map = {i: name for i, name in enumerate(class_list)}
            num_classes = len(class_list)

            # weights=None: trained weights are loaded below,
            # so there is no need to download ImageNet weights.
            model = models.mobilenet_v3_large(weights=None)
            model.classifier = nn.Sequential(
                nn.Linear(960, 1280),
                nn.Hardswish(),
                nn.Dropout(0.2),
                nn.Linear(1280, num_classes),
            )

            state_dict = torch.load(str(weights_path), map_location=self.device)
            model.load_state_dict(state_dict)
            model = model.to(self.device)
            model.eval()

            print(f"✅ Loaded {weights_path.name}: {num_classes} classes")

            return {
                "model": model,
                "class_map": class_map,
                "num_classes": num_classes,
            }

        except Exception as e:
            print(f"❌ Error loading {weights_path.name}: {e}")
            return None

    # ============================================================
    # SHARED: TOP-K PREDICTIONS FOR ONE MODEL
    # ============================================================

    def _top_k(self, key: str, image_tensor: torch.Tensor, k: int = 3):
        model_info = self.models.get(key)
        if model_info is None:
            return []

        model = model_info["model"]
        class_map = model_info["class_map"]

        with torch.no_grad():
            outputs = model(image_tensor.to(self.device))
            probs = torch.nn.functional.softmax(outputs, dim=1)
            top_k = min(k, len(class_map))
            top_probs, top_indices = torch.topk(probs, top_k, dim=1)

        results = []
        for p, idx in zip(top_probs[0].cpu().tolist(), top_indices[0].cpu().tolist()):
            raw_name = class_map.get(int(idx), f"{key}_unknown")
            results.append(
                {
                    "category": key,
                    "raw_name": raw_name,
                    "prediction": friendly_name(raw_name),
                    "confidence": float(p),
                    "class_idx": int(idx),
                }
            )
        return results

    # ============================================================
    # RICE SPECIALIST ENSEMBLE
    # ============================================================

    def predict(self, image_tensor: torch.Tensor):
        """
        Run the rice Disease, Nutrition, Pest (and Balanced, if loaded) models.
        The prediction with the highest confidence is returned.
        """
        all_predictions = []
        for key in RICE_MODEL_KEYS:
            all_predictions.extend(self._top_k(key, image_tensor, k=3))

        if not all_predictions:
            raise RuntimeError("No rice Disease, Nutrition or Pest models are loaded.")

        # Deduplicate by friendly name and sort by confidence
        seen = set()
        unique_preds = []
        for pred in sorted(all_predictions, key=lambda x: x["confidence"], reverse=True):
            if pred["prediction"] not in seen:
                seen.add(pred["prediction"])
                unique_preds.append(pred)

        top = unique_preds[0]

        alternatives = [
            {"disease": pred["prediction"], "confidence": round(pred["confidence"], 4)}
            for pred in unique_preds[1:3]
        ]

        # Remember model + class for Grad-CAM
        self.current_model_key = top["category"]
        self.current_class_idx = top["class_idx"]

        return top["prediction"], round(top["confidence"], 4), alternatives

    # ============================================================
    # TOMATO MODEL
    # ============================================================

    def predict_tomato(self, image_tensor: torch.Tensor):
        """
        Run the dedicated tomato disease model (10 classes, e.g.
        Tomato___Early_blight, Tomato___Late_blight, Tomato___healthy ...).

        Returns: prediction, confidence, alternatives
        """
        if self.models.get("tomato") is None:
            raise RuntimeError(
                "Tomato model is not loaded. "
                "Check best_tomato_model.pth and tomato_classes.txt."
            )

        predictions = self._top_k("tomato", image_tensor, k=3)
        top = predictions[0]

        alternatives = [
            {"disease": pred["prediction"], "confidence": round(pred["confidence"], 4)}
            for pred in predictions[1:]
        ]

        # Remember model + class for Grad-CAM
        self.current_model_key = "tomato"
        self.current_class_idx = top["class_idx"]

        return top["prediction"], round(top["confidence"], 4), alternatives

    # ============================================================
    # GRAD-CAM
    # ============================================================

    def _denormalize(self, image_tensor: torch.Tensor) -> np.ndarray:
        image_np = image_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
        image_np = IMAGENET_STD * image_np + IMAGENET_MEAN
        return np.clip(image_np, 0, 1).astype(np.float32)

    def generate_gradcam(self, image_tensor: torch.Tensor, target_class: int = None):
        """
        Generate a Grad-CAM overlay using the model that produced
        the current prediction.

        Returns an RGB uint8 image (0-255), or None if Grad-CAM fails.
        """
        self.last_grayscale_cam = None

        try:
            from pytorch_grad_cam import GradCAM
            from pytorch_grad_cam.utils.image import show_cam_on_image
            from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

            model_info = self.models.get(self.current_model_key)
            if model_info is None:
                print("⚠️ Grad-CAM model not found.")
                return None

            model = model_info["model"]
            target_layers = [model.features[-1]]  # MobileNetV3 final feature layer

            if target_class is None:
                target_class = self.current_class_idx

            targets = [ClassifierOutputTarget(int(target_class))] if target_class is not None else None

            image_np = self._denormalize(image_tensor)

            cam = GradCAM(model=model, target_layers=target_layers)
            grayscale_cam = cam(
                input_tensor=image_tensor.to(self.device),
                targets=targets,
            )[0, :]

            # Keep the raw 0-1 attention map for severity estimation
            self.last_grayscale_cam = grayscale_cam

            return show_cam_on_image(image_np, grayscale_cam, use_rgb=True)

        except Exception as e:
            print(f"⚠️ Grad-CAM error: {e}")
            return None

    # ============================================================
    # SEVERITY ESTIMATION
    # ============================================================

    def estimate_severity(self, heatmap=None):
        """
        Estimate severity from the Grad-CAM attention map.

        Uses the raw grayscale CAM (0-1) from the last generate_gradcam call.
        Returns (None, None) if no Grad-CAM is available.
        """
        cam = self.last_grayscale_cam

        if cam is None and heatmap is not None:
            # Fallback: derive a 0-1 map from the overlay image
            cam = np.asarray(heatmap, dtype=np.float32)
            if cam.ndim == 3:
                cam = cam[:, :, 0]
            if cam.max() > 1.0:
                cam = cam / 255.0

        if cam is None:
            return None, None

        try:
            affected_area = np.sum(cam > 0.5)
            total_area = cam.shape[0] * cam.shape[1]
            severity_pct = float(affected_area / total_area) * 100.0

            if severity_pct < 10:
                level = "Mild (Early Stage)"
            elif severity_pct < 40:
                level = "Moderate (Spreading)"
            else:
                level = "Severe (Critical Action Needed)"

            return round(severity_pct, 2), level

        except Exception:
            return None, None