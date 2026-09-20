print("[Vision Agent] main.py is executing!")

import base64
import io

import numpy as np
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image

# Import application modules
from app.schemas import VisionResponse, DiseasePrediction
from app.preprocess import validate_image, preprocess_image
from app.model_ensemble import EnsembledVisionModel
from app.crop_classifier import CropClassifier

print("[Vision Agent] All imports loaded!")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Vision Agent - AgriKetha",
    description="Crop Disease Image Analysis with Automatic Crop Detection",
    version="1.0.0",
)


# ============================================================
# GLOBAL MODEL INSTANCES
# ============================================================

vision_model = None
crop_classifier = None

SUPPORTED_CROPS = ["rice", "tomato"]


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def load_model():
    """
    Load all vision models and the crop classifier
    when the Vision Agent starts.
    """

    global vision_model
    global crop_classifier

    print("[Vision Agent] Loading Vision Models...")

    # Existing disease/pest/nutrition/tomato models
    vision_model = EnsembledVisionModel()

    # Automatic Rice/Tomato classifier
    crop_classifier = CropClassifier()

    print("[Vision Agent] Vision Agent ready!")


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/agent/health")
async def health_check():
    """
    Check whether the Vision Agent and models are available.
    """

    return {
        "status": "healthy",
        "agent": "vision-agent",
        "model_loaded": vision_model is not None,
        "crop_classifier_loaded": crop_classifier is not None,
    }


# ============================================================
# HELPERS
# ============================================================

def _gradcam_to_base64(gradcam_image: np.ndarray) -> str:
    """
    Convert a Grad-CAM array to a base64 PNG string.

    Handles both:
    - 0-1 float output
    - 0-255 output
    """

    img = np.asarray(
        gradcam_image,
        dtype=np.float32
    )

    if img.max() <= 1.0:
        img = img * 255.0

    img = np.clip(
        img,
        0,
        255
    ).astype(np.uint8)

    buffered = io.BytesIO()

    Image.fromarray(img).save(
        buffered,
        format="PNG"
    )

    return base64.b64encode(
        buffered.getvalue()
    ).decode("utf-8")


def _find_class_index(prediction: str):
    """
    Find the class index of the prediction
    in the model that produced it.
    """

    model_key = getattr(
        vision_model,
        "current_model_key",
        None
    )

    models = getattr(
        vision_model,
        "models",
        None
    ) or {}

    current_model_data = models.get(
        model_key
    )

    if current_model_data is None:
        return None

    for idx, class_name in current_model_data.get(
        "class_map",
        {}
    ).items():

        if class_name == prediction:
            return idx

    return None


# ============================================================
# IMAGE ANALYSIS
# ============================================================

@app.post(
    "/agent/image/analyze",
    response_model=VisionResponse,
)
async def analyze_image(
    file: UploadFile = File(...),
):
    """
    Analyze a crop leaf image.

    Processing pipeline:

    1. Validate file type
    2. Validate image quality
    3. Validate crop domain using OOD detection
    4. Automatically detect Rice/Tomato
    5. Run crop-specific disease model
    6. Generate Grad-CAM
    7. Estimate severity
    8. Return analysis

    Supported crops:
    - rice
    - tomato
    """

    # ========================================================
    # 1. CHECK MODELS
    # ========================================================

    if vision_model is None:
        raise HTTPException(
            status_code=503,
            detail="Vision model is not loaded.",
        )

    if crop_classifier is None:
        raise HTTPException(
            status_code=503,
            detail="Crop classifier is not loaded.",
        )

    # ========================================================
    # 2. VALIDATE FILE TYPE
    # ========================================================

    if not file.content_type:
        raise HTTPException(
            status_code=400,
            detail="File content type is missing.",
        )

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image.",
        )

    # Crop is unknown until validation/classification
    crop = "unknown"

    try:

        # ====================================================
        # 3. READ IMAGE
        # ====================================================

        contents = await file.read()

        image_pil = Image.open(
            io.BytesIO(contents)
        ).convert("RGB")

        image_np = np.array(
            image_pil
        )

        # ====================================================
        # 4. IMAGE QUALITY VALIDATION
        # ====================================================

        is_valid, validation_message = validate_image(
            image_np
        )

        if not is_valid:

            print(
                f"❌ Image quality validation failed: "
                f"{validation_message}"
            )

            return VisionResponse(
                status="error",
                crop=crop,
                prediction=None,
                confidence=None,
                severity_percentage=None,
                severity_level=None,
                gradcam_base64=None,
                alternatives=[],
                message=validation_message,
            )

        # ====================================================
        # 5. CROP DOMAIN / OOD VALIDATION
        # ====================================================

        print("🔍 Validating crop domain...")

        (
            domain_valid,
            domain_crop,
            domain_similarity,
            domain_message,
        ) = crop_classifier.validate_crop_domain(
            image_pil
        )

        if not domain_valid:

            print(
                f"❌ OOD rejection | "
                f"Closest crop: {domain_crop} | "
                f"Similarity: {domain_similarity:.4f}"
            )

            return VisionResponse(
                status="error",
                crop="unknown",
                prediction=None,
                confidence=None,
                severity_percentage=None,
                severity_level=None,
                gradcam_base64=None,
                alternatives=[],
                message=domain_message,
            )

        print(
            f"✅ Crop domain accepted | "
            f"Detected domain: {domain_crop} | "
            f"Similarity: {domain_similarity:.4f}"
        )

        # ====================================================
        # 6. AUTOMATIC CROP DETECTION
        # ====================================================

        print("🔍 Detecting crop type...")

        crop, crop_confidence = crop_classifier.predict(
            image_pil
        )

        crop = crop.lower().strip()

        print(
            f"🌱 Detected Crop: {crop}"
        )

        print(
            f"📊 Crop Confidence: "
            f"{crop_confidence:.4f}"
        )

        # ====================================================
        # 7. VERIFY DETECTED CROP
        # ====================================================

        if crop not in SUPPORTED_CROPS:

            print(
                f"❌ Unsupported crop detected: {crop}"
            )

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported detected crop '{crop}'. "
                    f"Supported crops are: "
                    f"{', '.join(SUPPORTED_CROPS)}."
                ),
            )

        # ====================================================
        # 8. PREPROCESS IMAGE
        # ====================================================

        image_tensor = preprocess_image(
            image_pil
        )

        # ====================================================
        # 9. RUN CROP-SPECIFIC MODEL
        # ====================================================

        if crop == "tomato":

            print(
                "🍅 Using Tomato Disease Model"
            )

            prediction, confidence, alternatives = (
                vision_model.predict_tomato(
                    image_tensor
                )
            )

        else:

            print(
                "🌾 Using Rice Specialist Ensemble"
            )

            prediction, confidence, alternatives = (
                vision_model.predict(
                    image_tensor
                )
            )

        print(
            f"🔎 Prediction: {prediction}"
        )

        print(
            f"📊 Disease Confidence: "
            f"{confidence:.4f}"
        )

        print(
            f"🧠 Model: "
            f"{getattr(vision_model, 'current_model_key', 'unknown')}"
        )

        # ====================================================
        # 10. FIND CLASS INDEX
        # ====================================================

        class_idx = _find_class_index(
            prediction
        )

        print(
            f"🔢 Class index: {class_idx}"
        )

        # ====================================================
        # 11. GENERATE GRAD-CAM
        #
        # A Grad-CAM failure must not break prediction.
        # ====================================================

        gradcam_base64 = None
        gradcam_image = None

        if class_idx is not None:

            try:

                print(
                    "🔍 Generating Grad-CAM..."
                )

                gradcam_image = (
                    vision_model.generate_gradcam(
                        image_tensor,
                        class_idx
                    )
                )

                if gradcam_image is not None:

                    gradcam_base64 = (
                        _gradcam_to_base64(
                            gradcam_image
                        )
                    )

                    print(
                        "✅ Grad-CAM generated!"
                    )

            except Exception as g_err:

                print(
                    f"⚠️ Grad-CAM warning: "
                    f"{g_err}"
                )

                gradcam_image = None
                gradcam_base64 = None

        else:

            print(
                "⚠️ Could not determine class index. "
                "Grad-CAM skipped."
            )

        # ====================================================
        # 12. SEVERITY ESTIMATION
        # ====================================================

        severity_pct = None
        severity_level = None

        if gradcam_image is not None:

            severity_pct, severity_level = (
                vision_model.estimate_severity(
                    gradcam_image
                )
            )

            print(
                f"📈 Severity: "
                f"{severity_pct}% - "
                f"{severity_level}"
            )

        # ====================================================
        # 13. FORMAT ALTERNATIVES
        # ====================================================

        alternatives_list = [
            DiseasePrediction(
                disease=alt["disease"],
                confidence=alt["confidence"],
            )
            for alt in alternatives
        ]

        # ====================================================
        # 14. RETURN RESPONSE
        # ====================================================

        return VisionResponse(
            status="success",

            # Automatically detected crop
            crop=crop,

            prediction=prediction,

            confidence=confidence,

            severity_percentage=severity_pct,

            severity_level=severity_level,

            gradcam_base64=gradcam_base64,

            alternatives=alternatives_list,

            message=(
                f"Image analyzed successfully. "
                f"Crop automatically detected as "
                f"{crop} with "
                f"{crop_confidence * 100:.2f}% confidence."
            ),
        )

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except HTTPException:
        raise

    except Exception as e:

        print(
            f"❌ Processing error: {str(e)}"
        )

        return VisionResponse(
            status="error",
            crop=crop,
            prediction=None,
            confidence=None,
            severity_percentage=None,
            severity_level=None,
            gradcam_base64=None,
            alternatives=[],
            message=(
                f"Processing error: {str(e)}"
            ),
        )


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
async def root():

    return {
        "message": "AgriKetha Vision Agent",

        "version": "1.0.0",

        "automatic_crop_detection": True,

        "ood_crop_validation": True,

        "supported_crops": SUPPORTED_CROPS,

        "endpoints": {
            "health": "/agent/health",
            "analyze": "/agent/image/analyze (POST)",
        }
    }


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print(
        "🚀 Starting Vision Agent Server..."
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
    )