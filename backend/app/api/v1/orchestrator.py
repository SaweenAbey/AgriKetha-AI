from datetime import datetime, timezone
from typing import Any, List, Optional
import httpx
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from app.api.deps import require_farmer_or_admin
from app.core.config import settings
from app.core.database import get_db
from app.core.logging_config import logger
from app.schemas.orchestrator.schemas import OrchestratorResponse
from app.services.orchestrator_service import OrchestratorService


import asyncio

router = APIRouter(
    prefix="/orchestrator",
    tags=["Agent 4 - Orchestrator"],
)

orchestrator_service = OrchestratorService()


@router.get("/status")
async def get_orchestrator_status():
    """
    Check the connectivity status of all microservice agents concurrently.
    """
    statuses = {
        "orchestrator": "online",
        "gemini_llm": "configured" if settings.GEMINI_API_KEY else "unconfigured",
        "query_agent": "offline",
        "vision_agent": "offline",
        "research_agent": "offline",
    }

    async def check_query():
        for url in [settings.QUERY_AGENT_URL, "http://127.0.0.1:8001"]:
            try:
                async with httpx.AsyncClient(timeout=0.6) as client:
                    res = await client.get(f"{url.rstrip('/')}/")
                    if res.status_code == 200:
                        return "online"
            except Exception:
                pass
        return "offline"

    async def check_vision():
        for url in [settings.VISION_AGENT_URL, "http://127.0.0.1:8002"]:
            try:
                async with httpx.AsyncClient(timeout=0.6) as client:
                    res = await client.get(f"{url.rstrip('/')}/agent/health")
                    if res.status_code == 200:
                        return "online"
            except Exception:
                pass
        return "offline"

    async def check_research():
        for url in [settings.RESEARCH_AGENT_URL, "http://127.0.0.1:8004", "http://127.0.0.1:8003"]:
            try:
                async with httpx.AsyncClient(timeout=0.6) as client:
                    res = await client.get(f"{url.rstrip('/')}/agent/health")
                    if res.status_code == 200:
                        return "online"
            except Exception:
                pass
        return "offline"

    q_stat, v_stat, r_stat = await asyncio.gather(
        check_query(), check_vision(), check_research()
    )
    statuses["query_agent"] = q_stat
    statuses["vision_agent"] = v_stat
    statuses["research_agent"] = r_stat

    return statuses



@router.get("/history")
async def get_orchestrator_history(
    limit: int = 15,
    current_user: dict = Depends(require_farmer_or_admin),
    db = Depends(get_db),
):
    """
    Retrieve previous multi-agent advisory sessions for this farmer.
    """
    user_id_str = current_user["id"]
    cursor = db.orchestrator_sessions.find({"user_id": user_id_str}).sort("created_at", -1).limit(limit)
    sessions = []
    async for s in cursor:
        s["id"] = str(s["_id"])
        del s["_id"]
        sessions.append(s)
    return sessions


@router.post(
    "/query",
    response_model=OrchestratorResponse,
)
async def orchestrate_query(
    question: str = Form(...),
    language: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(require_farmer_or_admin),
    db = Depends(get_db),
):
    """
    Agent 4 main orchestration endpoint.

    Accepts:
    - Farmer's agricultural question
    - Optional preferred language (e.g. 'si', 'en')
    - Optional crop leaf image

    Agent 4 coordinates:
    - Agent 2: Query/NLP
    - Agent 1: Vision (Leaf pathology with Grad-CAM)
    - Agent 3: Research (Agricultural RAG vector retrieval)
    - Agent 4: Gemini LLM Grounded Agricultural Advisory
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
        preferred_language=language,
    )

    # Save session to MongoDB for historical tracking
    try:
        session_record = {
            "user_id": current_user["id"],
            "user_email": current_user.get("email"),
            "session_id": result.get("session_id"),
            "question": question,
            "detected_language": result.get("detected_language"),
            "crop": result.get("crop"),
            "intent": result.get("intent"),
            "advisory": result.get("advisory"),
            "vision_result": result.get("vision_result"),
            "evidence_count": len(result.get("evidence", [])),
            "sources": result.get("sources", []),
            "agent_activity": result.get("agent_activity", []),
            "created_at": datetime.now(timezone.utc),
        }
        await db.orchestrator_sessions.insert_one(session_record)
    except Exception as db_err:
        logger.warning("Could not persist orchestrator session to MongoDB: %s", db_err)

    return result