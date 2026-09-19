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
    Validate image quality.
    Returns: (is_valid, message)
    """
    if image_np is None or image_np.size == 0:
        return False, "Invalid image data."

    # Convert to grayscale
    if len(image_np.shape) == 3:
        if image_np.shape[2] == 4:
            # RGBA to RGB
            image_np = image_np[:, :, :3]
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY) if 'cv2' in globals() else np.mean(image_np, axis=2).astype(np.uint8)
    else:
        gray = image_np

    # 1. Check Extreme Brightness (pitch black or completely washed out)
    mean_brightness = float(np.mean(gray))
    if mean_brightness < 8:
        return False, "Image is pitch black. Please take the photo in better lighting."
    if mean_brightness > 250:
        return False, "Image is completely overexposed. Please retake the photo."

    # 2. Check Blurriness (Laplacian variance) - gentle threshold for mobile cameras
    if 'cv2' in globals():
        try:
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            if blur_score < 10:
                return False, "Image is extremely blurred. Please hold camera steady."
        except Exception:
            pass

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