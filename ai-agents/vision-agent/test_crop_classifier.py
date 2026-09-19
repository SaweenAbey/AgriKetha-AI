import sys
import torch
from torchvision import models, transforms
from PIL import Image


MODEL_PATH = "best_crop_classifier.pth"
CLASSES_PATH = "crop_classes.txt"


# Load class names
with open(CLASSES_PATH, "r") as f:
    classes = [line.strip() for line in f if line.strip()]

print("Classes:", classes)


# Create the same MobileNetV3-Small architecture used during training
model = models.mobilenet_v3_small(weights=None)

model.classifier[3] = torch.nn.Linear(
    model.classifier[3].in_features,
    len(classes)
)

# Load trained model
state_dict = torch.load(MODEL_PATH, map_location="cpu")
model.load_state_dict(state_dict)

model.eval()


# Same preprocessing used for the classifier
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# Get image path from command line
if len(sys.argv) < 2:
    print("\nUsage:")
    print('python .\\test_crop_classifier.py "IMAGE_PATH"')
    sys.exit(1)

image_path = sys.argv[1]

print("\nTesting image:")
print(image_path)

# Load image
image = Image.open(image_path).convert("RGB")

# Preprocess
image_tensor = transform(image).unsqueeze(0)


# Prediction
with torch.no_grad():
    outputs = model(image_tensor)
    probabilities = torch.softmax(outputs, dim=1)

    confidence, predicted_index = torch.max(probabilities, dim=1)

predicted_crop = classes[predicted_index.item()]
confidence_value = confidence.item()


print("\n========== CROP CLASSIFICATION ==========")
print(f"Predicted Crop : {predicted_crop}")
print(f"Confidence     : {confidence_value:.4f}")
print(f"Confidence %   : {confidence_value * 100:.2f}%")
print("=========================================")