print("🔥 main.py is executing!")

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

print("✅ All imports loaded!")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Vision Agent - AgriKetha",
    description="Crop Disease Image Analysis with Explainability",
    version="1.0.0",
)


# ============================================================
# GLOBAL MODEL INSTANCE
# ============================================================

vision_model = None

SUPPORTED_CROPS = ["rice", "tomato"]


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def load_model():
    """
    Load all vision models when the Vision Agent starts.
    """
    global vision_model

    print("🖼️ Loading Vision Models...")
    vision_model = EnsembledVisionModel()
    print("✅ Vision Agent ready!")


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
    }


# ============================================================
# HELPERS
# ============================================================

def _gradcam_to_base64(gradcam_image: np.ndarray) -> str:
    """
    Convert a Grad-CAM array to a base64 PNG string.
    Handles both 0-1 float output and 0-255 output.
    """
    img = np.asarray(gradcam_image, dtype=np.float32)

    if img.max() <= 1.0:
        img = img * 255.0

    img = np.clip(img, 0, 255).astype(np.uint8)

    buffered = io.BytesIO()
    Image.fromarray(img).save(buffered, format="PNG")

    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def _find_class_index(prediction: str):
    """
    Find the class index of the prediction in the model that produced it.
    """
    model_key = getattr(vision_model, "current_model_key", None)
    models = getattr(vision_model, "models", None) or {}

    current_model_data = models.get(model_key)

    if current_model_data is None:
        return None

    for idx, class_name in current_model_data.get("class_map", {}).items():
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
    crop: str = "rice",
):
    """
    Analyze a crop leaf image.

    Supported crops:
    - rice   -> existing Disease/Nutrition/Pest specialist ensemble
    - tomato -> dedicated tomato disease model
    """

    # ========================================================
    # 1. CHECK MODEL
    # ========================================================

    if vision_model is None:
        raise HTTPException(
            status_code=503,
            detail="Vision model is not loaded.",
        )

    # ========================================================
    # 2. NORMALIZE & VALIDATE CROP
    # ========================================================

    crop = (crop or "rice").lower().strip()

    if crop not in SUPPORTED_CROPS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported crop '{crop}'. "
                f"Supported crops are: {', '.join(SUPPORTED_CROPS)}."
            ),
        )

    # ========================================================
    # 3. VALIDATE FILE TYPE
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

    try:
        # ====================================================
        # 4. READ IMAGE
        # ====================================================

        contents = await file.read()
        image_pil = Image.open(io.BytesIO(contents)).convert("RGB")
        image_np = np.array(image_pil)

        # ====================================================
        # 5. IMAGE QUALITY VALIDATION
        # ====================================================

        is_valid, validation_message = validate_image(image_np)

        if not is_valid:
            return VisionResponse(
                status="error",
                crop=crop,
                message=validation_message,
            )

        # ====================================================
        # 6. PREPROCESS IMAGE
        # ====================================================

        image_tensor = preprocess_image(image_pil)

        # ====================================================
        # 7. RUN PREDICTION
        # ====================================================

        if crop == "tomato":
            print("🍅 Using Tomato Model")
            prediction, confidence, alternatives = vision_model.predict_tomato(image_tensor)
        else:
            print("🌾 Using Rice Specialist Ensemble")
            prediction, confidence, alternatives = vision_model.predict(image_tensor)

        print(f"🔎 Prediction: {prediction}")
        print(f"📊 Confidence: {confidence:.4f}")
        print(f"🧠 Model: {getattr(vision_model, 'current_model_key', 'unknown')}")

        # ====================================================
        # 8. FIND CLASS INDEX
        # ====================================================

        class_idx = _find_class_index(prediction)
        print(f"🔢 Class index: {class_idx}")

        # ====================================================
        # 9. GENERATE GRAD-CAM (Explainability)
        # A Grad-CAM failure must not break the prediction.
        # ====================================================

        gradcam_base64 = None
        gradcam_image = None

        if class_idx is not None:
            try:
                print("🔍 Generating Grad-CAM...")
                gradcam_image = vision_model.generate_gradcam(image_tensor, class_idx)

                if gradcam_image is not None:
                    gradcam_base64 = _gradcam_to_base64(gradcam_image)
                    print("✅ Grad-CAM generated!")

            except Exception as g_err:
                print(f"⚠️ Grad-CAM warning: {g_err}")
                gradcam_image = None
                gradcam_base64 = None
        else:
            print("⚠️ Could not determine class index. Grad-CAM skipped.")

        # ====================================================
        # 10. SEVERITY ESTIMATION
        # ====================================================

        severity_pct = None
        severity_level = None

        if gradcam_image is not None:
            severity_pct, severity_level = vision_model.estimate_severity(gradcam_image)
            print(f"📈 Severity: {severity_pct}% - {severity_level}")

        # ====================================================
        # 11. FORMAT ALTERNATIVES
        # ====================================================

        alternatives_list = [
            DiseasePrediction(
                disease=alt["disease"],
                confidence=alt["confidence"],
            )
            for alt in alternatives
        ]

        # ====================================================
        # 12. RETURN RESPONSE
        # ====================================================

        return VisionResponse(
            status="success",
            crop=crop,
            prediction=prediction,
            confidence=confidence,
            severity_percentage=severity_pct,
            severity_level=severity_level,
            gradcam_base64=gradcam_base64,
            alternatives=alternatives_list,
            message="Image analyzed successfully",
        )

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:
        print(f"❌ Processing error: {str(e)}")

        return VisionResponse(
            status="error",
            crop=crop,
            message=f"Processing error: {str(e)}",
        )


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
async def root():
    return {
        "message": "AgriKetha Vision Agent",
        "version": "1.0.0",
        "supported_crops": SUPPORTED_CROPS,
        "endpoints": {
            "health": "/agent/health",
            "analyze": "/agent/image/analyze (POST)",
        },
    }


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":
    print("🚀 Starting Vision Agent Server...")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
    )