import cv2
import numpy as np
from PIL import Image
import torch
from torchvision import transforms

# Standard transforms for MobileNet/EfficientNet
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

def validate_image(image_np: np.ndarray):
    """
    Validate image quality to prevent hallucinations.
    Returns: (is_valid, message)
    """
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    
    # 1. Check Blurriness (Laplacian variance)
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur_score < 100:
        return False, "Image is too blurry. Please hold the camera steady and retake."
    
    # 2. Check Brightness
    mean_brightness = np.mean(gray)
    if mean_brightness < 30:
        return False, "Image is too dark. Please take the photo in good lighting."
    if mean_brightness > 225:
        return False, "Image is overexposed. Please reduce brightness and retake."
    
    # 3. Check if image contains a leaf (edge detection)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / (image_np.shape[0] * image_np.shape[1])
    if edge_density < 0.01:
        return False, "No clear leaf structure detected. Please upload a photo of a leaf."
    
    return True, "Valid Image"

def preprocess_image(image_pil: Image.Image) -> torch.Tensor:
    """
    Convert PIL image to normalized tensor for the model.
    """
    if image_pil.mode != 'RGB':
        image_pil = image_pil.convert('RGB')
    
    image_tensor = transform(image_pil)
    image_tensor = image_tensor.unsqueeze(0)
    
    return image_tensor