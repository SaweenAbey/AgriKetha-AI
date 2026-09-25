print("[Vision Agent] main.py is executing!")

import io

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image

# Import application modules
from app.schemas import VisionResponse, DiseasePrediction
from app.model_ensemble import EnsembledVisionModel
from app.crop_classifier import CropClassifier
from app.pipeline import SUPPORTED_CROPS, analyze_leaf_image

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

    The pipeline (quality check, fruit/leaf gate, OOD validation, rice/tomato
    detection, crop-specific model, Grad-CAM, severity) lives in
    app/pipeline.py so the backend fallback runs exactly the same logic.
    """

    if vision_model is None or crop_classifier is None:
        raise HTTPException(
            status_code=503,
            detail="Vision models are not loaded.",
        )

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image.",
        )

    try:
        contents = await file.read()
        image_pil = Image.open(io.BytesIO(contents)).convert("RGB")
        result = analyze_leaf_image(image_pil, vision_model, crop_classifier)
    except Exception as e:
        print(f"[Vision Agent] Processing error: {e}")
        return VisionResponse(
            status="error",
            crop="unknown",
            alternatives=[],
            message=f"Processing error: {e}",
        )

    print(f"[Vision Agent] {result['status']} | crop={result['crop']} | prediction={result['prediction']}")
    return VisionResponse(
        **{**result, "alternatives": [DiseasePrediction(**alt) for alt in result["alternatives"]]}
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