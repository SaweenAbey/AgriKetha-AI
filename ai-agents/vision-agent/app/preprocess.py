import cv2
import numpy as np
from PIL import Image
import torch
from torchvision import transforms


# Standard transforms for MobileNet/EfficientNet
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


def validate_image(image_np: np.ndarray):
    """
    Validate uploaded image quality.

    Checks:
    1. Invalid/empty image
    2. Image too dark
    3. Image too bright
    4. Image too blurry

    Returns:
        (is_valid, message)
    """

    # ---------------------------------------------------------
    # 1. Check invalid / empty image
    # ---------------------------------------------------------
    if image_np is None or image_np.size == 0:
        return False, "Invalid image. Please retake the photo."


    # ---------------------------------------------------------
    # 2. Convert image to grayscale
    # ---------------------------------------------------------
    if len(image_np.shape) == 3:

        # RGBA -> RGB
        if image_np.shape[2] == 4:
            image_np = image_np[:, :, :3]

        try:
            gray = cv2.cvtColor(
                image_np,
                cv2.COLOR_RGB2GRAY
            )
        except Exception:
            gray = np.mean(
                image_np,
                axis=2
            ).astype(np.uint8)

    else:
        gray = image_np


    # ---------------------------------------------------------
    # 3. Brightness check
    # ---------------------------------------------------------
    mean_brightness = float(np.mean(gray))


    # Very dark image
    if mean_brightness < 8:
        return (
            False,
            "Image is too dark. Please retake the photo with better lighting."
        )


    # Very bright / overexposed image
    if mean_brightness > 250:
        return (
            False,
            "Image is too bright. Please retake the photo."
        )


    # ---------------------------------------------------------
    # 4. Blur detection
    # ---------------------------------------------------------
    try:

        blur_score = cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()


        # Very low Laplacian variance = very blurry image
        if blur_score < 10:
            return (
                False,
                "Image is too blurry. Please retake the photo."
            )

    except Exception:
        # If blur calculation fails, don't reject the image
        pass

    return True, "Valid Image"


def preprocess_image(image_pil: Image.Image) -> torch.Tensor:
    """
    Convert PIL image into a normalized tensor
    suitable for the vision models.
    """

    # Convert image to RGB
    if image_pil.mode != "RGB":
        image_pil = image_pil.convert("RGB")


    # Apply resize, tensor conversion and normalization
    image_tensor = transform(image_pil)


    # Add batch dimension
    # [3, 224, 224] -> [1, 3, 224, 224]
    image_tensor = image_tensor.unsqueeze(0)


    return image_tensor