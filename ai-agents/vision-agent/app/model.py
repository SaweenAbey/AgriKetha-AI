import torch
import torch.nn as nn
from torchvision import models
import numpy as np
import os

class VisionModel:
    def __init__(self, weights_path=None, class_names_path=None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")

        # 1. Create the MobileNetV3 structure
        self.model = models.mobilenet_v3_large(pretrained=True)

        # 2. 🔥 FIXED: Use correct paths (files are in parent folder!)
        if class_names_path is None:
            class_names_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "class_names.txt")
        
        if weights_path is None:
            weights_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "best_rice_unified_model.pth")

        print(f"Looking for class names at: {class_names_path}")
        print(f"Looking for weights at: {weights_path}")

        # 3. Load the Class Names
        if os.path.exists(class_names_path):
            with open(class_names_path, "r") as f:
                class_list = [line.strip() for line in f.readlines()]
            self.class_names = {i: name for i, name in enumerate(class_list)}
            num_classes = len(class_list)
            print(f"✅ Loaded {num_classes} classes: {class_list[:3]}...")
        else:
            print(f"❌ ERROR: class_names.txt not found at {class_names_path}")
            self.class_names = {i: f"class_{i}" for i in range(12)}
            num_classes = 12

        # 4. Replace the head of the network
        self.model.classifier = nn.Sequential(
            nn.Linear(960, 1280),
            nn.Hardswish(),
            nn.Dropout(0.2),
            nn.Linear(1280, num_classes)
        )

        # 5. Load your trained weights (THE BRAIN YOU JUST TRAINED!)
        if os.path.exists(weights_path):
            self.model.load_state_dict(torch.load(weights_path, map_location=self.device))
            print(f"✅ Loaded your trained model from {weights_path} (Your Brain!)")
        else:
            print(f"❌ ERROR: Weights not found at {weights_path}")
            print("   Please make sure 'best_rice_unified_model.pth' exists in the vision-agent folder.")

        self.model = self.model.to(self.device)
        self.model.eval()
        self.target_layers = [self.model.features[-1]]

    # ===== PREDICTION FUNCTION =====
    def predict(self, image_tensor: torch.Tensor):
        with torch.no_grad():
            image_tensor = image_tensor.to(self.device)
            outputs = self.model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)

            top_probs, top_indices = torch.topk(probabilities, 3)
            top_probs = top_probs.cpu().numpy()[0]
            top_indices = top_indices.cpu().numpy()[0]

        prediction = self.class_names.get(top_indices[0], "unknown")
        confidence = float(top_probs[0])

        alternatives = []
        for i in range(1, 3):
            alternatives.append({
                "disease": self.class_names.get(top_indices[i], "unknown"),
                "confidence": float(top_probs[i])
            })

        return prediction, confidence, alternatives

    # ===== GRAD-CAM (Placeholder for now) =====
    def generate_gradcam(self, image_tensor: torch.Tensor, target_class: int):
        # Placeholder - we'll add real Grad-CAM later
        return np.random.rand(224, 224, 3).astype(np.float32)

    # ===== SEVERITY ESTIMATION =====
    def estimate_severity(self, heatmap):
        # Placeholder
        return 25.0, "Moderate"