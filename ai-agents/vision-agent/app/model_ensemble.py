import torch
import torch.nn as nn
from torchvision import models
import numpy as np
import os

class EnsembledVisionModel:
    """
    Loads 3 separate specialist models (Disease, Nutrition, Pest)
    and combines their predictions by picking the highest confidence.
    """
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        # Store all 3 models
        self.models = {}
        self.class_names = {}
        
        # 1. Load Disease Model
        self.models["disease"] = self._load_model(
            "best_disease_model.pth",
            "disease_classes.txt"
        )
        
        # 2. Load Nutrition Model
        self.models["nutrition"] = self._load_model(
            "best_nutrition_model.pth",
            "nutrition_classes.txt"
        )
        
        # 3. Load Pest Model
        self.models["pest"] = self._load_model(
            "best_pest_model.pth",
            "pest_classes.txt"
        )
        
        # Combine all class names
        self.class_names = {}
        for key in ["disease", "nutrition", "pest"]:
            if self.models[key] is not None:
                self.class_names.update(self.models[key]["class_map"])
        
        # For Grad-CAM (use the model that made the prediction)
        self.current_model_key = "disease"
        self.target_layers = []
        
        print(f"✅ Ensembled Model Ready! Total Classes: {len(self.class_names)}")
    
    def _load_model(self, weights_path, class_path):
        """Helper to load a single model with its class mapping"""
        if not os.path.exists(weights_path) or not os.path.exists(class_path):
            print(f"⚠️ Warning: {weights_path} or {class_path} not found!")
            return None
        
        # Load class names
        with open(class_path, "r") as f:
            class_list = [line.strip() for line in f.readlines()]
        class_map = {i: name for i, name in enumerate(class_list)}
        
        # Create model structure
        model = models.mobilenet_v3_large(weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V1)
        num_classes = len(class_list)
        model.classifier = nn.Sequential(
            nn.Linear(960, 1280),
            nn.Hardswish(),
            nn.Dropout(0.2),
            nn.Linear(1280, num_classes)
        )
        
        # Load weights
        model.load_state_dict(torch.load(weights_path, map_location=self.device))
        model = model.to(self.device)
        model.eval()
        
        print(f"✅ Loaded {os.path.basename(weights_path)}: {len(class_list)} classes")
        return {"model": model, "class_map": class_map}
    
    def predict(self, image_tensor: torch.Tensor):
        """
        Run all 3 models and return the highest confidence prediction.
        """
        all_predictions = []
        
        # Run each model
        for key in ["disease", "nutrition", "pest"]:
            if self.models[key] is None:
                continue
            
            model = self.models[key]["model"]
            class_map = self.models[key]["class_map"]
            
            with torch.no_grad():
                image_tensor = image_tensor.to(self.device)
                outputs = model(image_tensor)
                probs = torch.nn.functional.softmax(outputs, dim=1)
                top_prob, top_idx = torch.topk(probs, 1)
                
                confidence = float(top_prob[0][0].cpu().numpy())
                class_idx = int(top_idx[0][0].cpu().numpy())
                prediction = class_map.get(class_idx, f"{key}_unknown")
                
                all_predictions.append({
                    "category": key,
                    "prediction": prediction,
                    "confidence": confidence
                })
        
        # Sort by confidence (highest first)
        all_predictions.sort(key=lambda x: x["confidence"], reverse=True)
        
        # The top prediction is the final answer
        top = all_predictions[0]
        
        # Build alternatives (next 2 highest confidences)
        alternatives = []
        for pred in all_predictions[1:3]:
            alternatives.append({
                "disease": pred["prediction"],
                "confidence": pred["confidence"]
            })
        
        # Remember which model made the prediction for Grad-CAM
        self.current_model_key = top["category"]
        
        return top["prediction"], top["confidence"], alternatives
    
    def generate_gradcam(self, image_tensor: torch.Tensor, target_class: int):
        """
        Generate Grad-CAM using the model that made the final prediction.
        """
        try:
            from pytorch_grad_cam import GradCAM
            from pytorch_grad_cam.utils.image import show_cam_on_image
            
            # Get the model that made the prediction
            model_dict = self.models.get(self.current_model_key)
            if model_dict is None:
                return np.random.rand(224, 224, 3).astype(np.float32)
            
            model = model_dict["model"]
            target_layers = [model.features[-1]]
            
            # Convert tensor to image
            image_np = image_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
            mean = np.array([0.485, 0.456, 0.406])
            std = np.array([0.229, 0.224, 0.225])
            image_np = std * image_np + mean
            image_np = np.clip(image_np, 0, 1)
            
            cam = GradCAM(model=model, target_layers=target_layers)
            grayscale_cam = cam(input_tensor=image_tensor, targets=[target_class])
            grayscale_cam = grayscale_cam[0, :]
            
            visualization = show_cam_on_image(image_np, grayscale_cam, use_rgb=True)
            return visualization
        except Exception as e:
            print(f"⚠️ Grad-CAM error: {e}")
            return np.random.rand(224, 224, 3).astype(np.float32)
    
    def estimate_severity(self, heatmap):
        """Estimate severity from heatmap"""
        if heatmap is None:
            return 25.0, "Moderate"
        try:
            affected_area = np.sum(heatmap[:, :, 0] > 0.5)
            total_area = heatmap.shape[0] * heatmap.shape[1]
            severity_pct = (affected_area / total_area) * 100
            if severity_pct < 10:
                level = "Mild (Early Stage)"
            elif severity_pct < 40:
                level = "Moderate (Spreading)"
            else:
                level = "Severe (Critical Action Needed)"
            return round(severity_pct, 2), level
        except:
            return 25.0, "Moderate"