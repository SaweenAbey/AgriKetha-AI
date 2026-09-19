print("🔥 main.py is executing!")

import base64
import io
import numpy as np

from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image
import uvicorn

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
    version="1.0.0"
)


# ============================================================
# GLOBAL MODEL INSTANCE
# ============================================================

vision_model = None


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
        "model_loaded": vision_model is not None
    }


# ============================================================
# IMAGE ANALYSIS
# ============================================================

@app.post(
    "/agent/image/analyze",
    response_model=VisionResponse
)
async def analyze_image(
    file: UploadFile = File(...),
    crop: str = "rice"
):
    """
    Analyze a crop leaf image.

    Supported crops:

    - rice
    - tomato

    Rice:
        Uses the existing Disease/Nutrition/Pest ensemble.

    Tomato:
        Uses the dedicated tomato disease model.
    """

    # ========================================================
    # 1. CHECK MODEL
    # ========================================================

    if vision_model is None:
        raise HTTPException(
            status_code=503,
            detail="Vision model is not loaded."
        )


    # ========================================================
    # 2. NORMALIZE CROP NAME
    # ========================================================

    crop = crop.lower().strip()


    # ========================================================
    # 3. VALIDATE CROP
    # ========================================================

    supported_crops = [
        "rice",
        "tomato"
    ]

    if crop not in supported_crops:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported crop '{crop}'. "
                "Supported crops are: rice, tomato."
            )
        )


    # ========================================================
    # 4. VALIDATE FILE TYPE
    # ========================================================

    if not file.content_type:
        raise HTTPException(
            status_code=400,
            detail="File content type is missing."
        )

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image."
        )


    try:

        # ====================================================
        # 5. READ IMAGE
        # ====================================================

        contents = await file.read()

        image_pil = Image.open(
            io.BytesIO(contents)
        ).convert("RGB")

        image_np = np.array(image_pil)


        # ====================================================
        # 6. IMAGE QUALITY VALIDATION
        # ====================================================

        is_valid, validation_message = validate_image(
            image_np
        )

        if not is_valid:
            return VisionResponse(
                status="error",
                crop=crop,
                message=validation_message
            )


        # ====================================================
        # 7. PREPROCESS IMAGE
        # ====================================================

        image_tensor = preprocess_image(
            image_pil
        )


        # ====================================================
        # 8. RUN PREDICTION
        # ====================================================

        if crop == "tomato":

            # Tomato-specific model
            print("🍅 Using Tomato Model")

            (
                prediction,
                confidence,
                alternatives
            ) = vision_model.predict_tomato(
                image_tensor
            )

        else:

            # Existing rice specialist ensemble
            print("🌾 Using Rice Specialist Ensemble")

            (
                prediction,
                confidence,
                alternatives
            ) = vision_model.predict(
                image_tensor
            )


        print(
            f"🔎 Prediction: {prediction}"
        )

        print(
            f"📊 Confidence: {confidence:.4f}"
        )

        print(
            f"🧠 Model: {vision_model.current_model_key}"
        )


        # ====================================================
        # 9. FIND CLASS INDEX
        # ====================================================

        class_idx = None

        # Get the exact model that produced the prediction
        current_model_data = vision_model.models.get(
            vision_model.current_model_key
        )

        if current_model_data is not None:

            class_map = current_model_data["class_map"]

            for idx, class_name in class_map.items():

                if class_name == prediction:
                    class_idx = idx
                    break


        print(
            f"🔢 Class index: {class_idx}"
        )


        # ====================================================
        # 10. GENERATE GRAD-CAM
        # ====================================================

        gradcam_base64 = None
        gradcam_image = None

        if class_idx is not None:

            print("🔍 Generating Grad-CAM...")

            gradcam_image = (
                vision_model.generate_gradcam(
                    image_tensor,
                    class_idx
                )
            )

            gradcam_pil = Image.fromarray(
                gradcam_image.astype(np.uint8)
            )

            buffered = io.BytesIO()

            gradcam_pil.save(
                buffered,
                format="PNG"
            )

            gradcam_base64 = base64.b64encode(
                buffered.getvalue()
            ).decode("utf-8")

            print("✅ Grad-CAM generated!")

        else:

            print(
                "⚠️ Could not determine class index. "
                "Grad-CAM skipped."
            )


        # ====================================================
        # 11. SEVERITY ESTIMATION
        # ====================================================

        if gradcam_image is not None:

            (
                severity_pct,
                severity_level
            ) = vision_model.estimate_severity(
                gradcam_image
            )

            print(
                f"📈 Severity: "
                f"{severity_pct}% - "
                f"{severity_level}"
            )

        else:

            severity_pct = None
            severity_level = None


        # ====================================================
        # 12. FORMAT ALTERNATIVES
        # ====================================================

        alternatives_list = []

        for alt in alternatives:

            alternatives_list.append(
                DiseasePrediction(
                    disease=alt["disease"],
                    confidence=alt["confidence"]
                )
            )


        # ====================================================
        # 13. RETURN RESPONSE
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
            message="Image analyzed successfully"
        )


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:

        print(
            f"❌ Processing error: {str(e)}"
        )

        return VisionResponse(
            status="error",
            crop=crop,
            message=f"Processing error: {str(e)}"
        )


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
async def root():

    return {
        "message": "AgriKetha Vision Agent",
        "version": "1.0.0",
        "supported_crops": [
            "rice",
            "tomato"
        ],
        "endpoints": {
            "health": "/agent/health",
            "analyze": "/agent/image/analyze (POST)"
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
        port=8002
    )