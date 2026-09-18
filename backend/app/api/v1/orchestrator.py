from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from app.api.deps import require_farmer_or_admin
from app.schemas.orchestrator.schemas import OrchestratorResponse
from app.services.orchestrator_service import OrchestratorService


router = APIRouter(
    prefix="/orchestrator",
    tags=["Agent 4 - Orchestrator"],
)

orchestrator_service = OrchestratorService()


@router.post(
    "/query",
    response_model=OrchestratorResponse,
)
async def orchestrate_query(
    question: str = Form(...),
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(require_farmer_or_admin),
):
    """
    Agent 4 main orchestration endpoint.

    Accepts:
    - Farmer's agricultural question
    - Optional crop image

    Agent 4 coordinates:
    - Agent 2: Query/NLP
    - Agent 1: Vision
    - Agent 3: Research/RAG
    """

    question = question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    if len(question) > 800:
        raise HTTPException(
            status_code=400,
            detail="Question cannot exceed 800 characters.",
        )

    image_bytes = None
    image_filename = None
    image_content_type = None

    if file is not None:

        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="Uploaded file must be an image.",
            )

        image_bytes = await file.read()
        image_filename = file.filename
        image_content_type = file.content_type

    result = await orchestrator_service.process_request(
        question=question,
        image_bytes=image_bytes,
        image_filename=image_filename,
        image_content_type=image_content_type,
    )

    return result