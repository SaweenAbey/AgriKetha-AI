print("[Vision Agent] main.py is executing...")

import base64
import io
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import uvicorn

# Import your modules
from app.schemas import VisionResponse, DiseasePrediction
from app.preprocess import validate_image, preprocess_image
from app.model_ensemble import EnsembledVisionModel

print("[Vision Agent] All imports loaded successfully.")

# Initialize FastAPI
app = FastAPI(
    title="Vision Agent - AgriKetha",
    description="Crop Disease Image Analysis with Explainability",
    version="1.0.0"
)

# Global model instance
vision_model = None

@app.on_event("startup")
async def load_model():
    """Load the vision model on server startup"""
    global vision_model
    print("[Vision Agent] Loading Ensembled Vision Model...")
    try:
        vision_model = EnsembledVisionModel()
        print("[Vision Agent] Vision Agent ready!")
    except Exception as e:
        print(f"[Vision Agent] Notice loading ensemble: {e}")

@app.get("/agent/health")
async def health_check():
    """Health check endpoint"""
    return {

        "status": "healthy", 
        "agent": "vision-agent",
        "model_loaded": vision_model is not None
    }

@app.post("/agent/image/analyze", response_model=VisionResponse)
async def analyze_image(file: UploadFile = File(...)):
    """
    Main endpoint for analyzing crop leaf images.
    """
    # 1. Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # 2. Read image
        contents = await file.read()
        image_pil = Image.open(io.BytesIO(contents)).convert("RGB")
        image_np = np.array(image_pil)
        
        # 3. Quality Validation (Responsible AI)
        is_valid, message = validate_image(image_np)
        if not is_valid:
            return VisionResponse(
                status="error",
                message=message
            )
        
        # 4. Preprocess for model
        image_tensor = preprocess_image(image_pil)
        
        # 5. Run Prediction (Ensemble picks the best specialist!)
        prediction, confidence, alternatives = vision_model.predict(image_tensor)
        
        # 6. Generate Grad-CAM (Explainability)
        class_idx = None
        for idx, name in vision_model.class_names.items():
            if name == prediction:
                class_idx = idx
                break
        
        gradcam_base64 = None
        if class_idx is not None:
            gradcam_image = vision_model.generate_gradcam(image_tensor, class_idx)
            gradcam_pil = Image.fromarray((gradcam_image * 255).astype(np.uint8))
            buffered = io.BytesIO()
            gradcam_pil.save(buffered, format="PNG")
            gradcam_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        # 7. Severity Estimation
        severity_pct, severity_level = vision_model.estimate_severity(
            gradcam_image if 'gradcam_image' in locals() else np.random.rand(224, 224, 3)
        )
        
        # 8. Format alternatives
        alternatives_list = [
            DiseasePrediction(disease=alt["disease"], confidence=alt["confidence"])
            for alt in alternatives
        ]
        
        # 9. Return structured response
        return VisionResponse(
            status="success",
            crop="unknown",
            prediction=prediction,
            confidence=confidence,
            severity_percentage=severity_pct,
            severity_level=severity_level,
            gradcam_base64=gradcam_base64,
            alternatives=alternatives_list,
            message="Image analyzed successfully"
        )
    
    except Exception as e:
        return VisionResponse(
            status="error",
            message=f"Processing error: {str(e)}"
        )

@app.get("/")
async def root():
    return {
        "message": "AgriKetha Vision Agent",
        "version": "1.0.0",
        "endpoints": {
            "health": "/agent/health",
            "analyze": "/agent/image/analyze (POST)"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Vision Agent Server...")
    uvicorn.run(app, host="0.0.0.0", port=8002)