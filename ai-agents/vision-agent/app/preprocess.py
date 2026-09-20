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

    # 3. Check Botanical Foliage presence (ensuring image contains plant foliage)
    if len(image_np.shape) == 3 and image_np.shape[2] >= 3:
        arr = image_np[:, :, :3].astype(float)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        max_rgb = np.maximum(np.maximum(r, g), b)
        min_rgb = np.minimum(np.minimum(r, g), b)
        saturation = (max_rgb - min_rgb) / np.maximum(max_rgb, 1.0)
        chromatic = saturation > 0.14

        green_mask = chromatic & (g > 35) & (g > r * 1.05) & (g > b * 1.10)
        yellow_mask = chromatic & (r > 75) & (g > 65) & (b < r * 0.78) & (b < g * 0.78)
        brown_mask = chromatic & (r > 45) & (r < 185) & (g > 25) & (g < 155) & (b < g * 0.85) & (r > g + 5)
        botanical_pct = float(np.mean(green_mask | yellow_mask | brown_mask)) * 100.0

        if botanical_pct < 8.0:
            return False, "The uploaded image does not appear to be a recognized crop leaf (Rice, Tomato, Chili, Brinjal) or is not in our knowledge base. Please upload a clear photo of a crop leaf."

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