import uuid
from typing import Any, Optional

from app.core.logging_config import logger
from app.services.agent_clients import (
    AgentClientError,
    call_query_agent,
    call_research_agent,
    call_vision_agent,
)
from app.services.llm_service import LLMService, LLMServiceError
from app.core.middleware import record_audit_log



def _fallback_crop_nlp(question: str) -> dict[str, Any]:
    """Lightweight fallback NLP if Query Agent microservice is unreachable."""
    q_lower = question.lower()
    crop = None
    if any(k in q_lower for k in ["tomato", "තක්කාලි", "thakkali", "தக்காளி"]):
        crop = "tomato"
    elif any(k in q_lower for k in ["rice", "paddy", "වී", "ගොයම්", "wee", "goyam", "nel", "நெல்"]):
        crop = "rice"
    elif any(k in q_lower for k in ["chilli", "chili", "pepper", "මිරිස්", "miris", "kochchi", "மிளகாய்"]):
        crop = "chilli"
    elif any(k in q_lower for k in ["potato", "අල", "arthapal", "ala", "உருளைக்கிழங்கு"]):
        crop = "potato"
    elif any(k in q_lower for k in ["brinjal", "eggplant", "වම්බටු", "බටු", "wambatu", "கத்தரிக்காய்"]):
        crop = "brinjal"
    elif any(k in q_lower for k in ["cabbage", "ගෝවා", "gowa", "கோவா"]):
        crop = "cabbage"

    lang = "en"
    if any("\u0d80" <= c <= "\u0dff" for c in question):
        lang = "si"
    elif any("\u0b80" <= c <= "\u0bff" for c in question):
        lang = "ta"

    intent = "disease_or_pest_advisory"
    if any(w in q_lower for w in ["fertilizer", "compost", "පොහොර", "urea", "යූරියා"]):
        intent = "fertilizer"
    elif any(w in q_lower for w in ["water", "irrigation", "ජලය", "වතුර"]):
        intent = "irrigation"
    elif any(w in q_lower for w in ["price", "market", "මිල", "තොග"]):
        intent = "market"

    return {"crop": crop, "intent": intent, "detected_language": lang}


def _infer_crop_from_prediction(prediction: Optional[str]) -> Optional[str]:
    """Infer crop name from disease class prediction if crop is otherwise unknown."""
    if not prediction:
        return None
    pred_lower = prediction.lower()
    if "tomato" in pred_lower:
        return "tomato"
    if any(k in pred_lower for k in ["rice", "paddy", "blast", "brown spot", "tungro", "sheath"]):
        return "rice"
    if "chilli" in pred_lower or "chili" in pred_lower:
        return "chilli"
    if "potato" in pred_lower:
        return "potato"
    return None


class OrchestratorService:
    """
    Agent 4 - Central orchestration service.

    Responsibilities:
    - Coordinate Agent 2 (Query/NLP)
    - Coordinate Agent 1 (Vision)
    - Coordinate Agent 3 (Research/RAG)
    - Aggregate results
    - Prepare information for the advisory LLM (Gemini)
    """

    def __init__(self):
        self.llm_service = LLMService()

    async def process_request(
        self,
        question: str,
        image_bytes: Optional[bytes] = None,
        image_filename: Optional[str] = None,
        image_content_type: Optional[str] = None,
        preferred_language: Optional[str] = None,
    ) -> dict[str, Any]:

        session_id = str(uuid.uuid4())
        logger.info("Agent 4 request started | session_id=%s", session_id)

        agent_activity: list[dict[str, Any]] = []

        # ---------------------------------------------------------
        # STEP 1: Call Agent 2 - Query/NLP Agent
        # ---------------------------------------------------------

        query_result: Optional[dict[str, Any]] = None
        crop: Optional[str] = None
        intent: Optional[str] = None
        detected_language: Optional[str] = preferred_language
        translated_question: Optional[str] = None

        try:
            query_result = await call_query_agent(question)

            agent_activity.append(
                {
                    "agent": "query-agent",
                    "status": "success",
                    "details": "Question analyzed successfully by Agent 2.",
                }
            )
            logger.info("Agent 2 completed | session_id=%s", session_id)

        except AgentClientError as exc:
            logger.warning(
                "Agent 2 unreachable, using fallback parser | session_id=%s | error=%s",
                session_id,
                exc,
            )

            fallback_nlp = _fallback_crop_nlp(question)
            crop = fallback_nlp.get("crop")
            intent = fallback_nlp.get("intent")
            detected_language = preferred_language or fallback_nlp.get("detected_language")

            agent_activity.append(
                {
                    "agent": "query-agent",
                    "status": "fallback",
                    "details": f"NLP fallback: Crop={crop or 'General'}, Intent={intent or 'Advisory'}",
                }
            )

        # Extract NLP information if Agent 2 succeeded
        if query_result:
            detected_language = query_result.get("detected_language") or detected_language
            translated_question = query_result.get("translated_question")

            nlp_result = query_result.get("agent_1_result") or {}
            crop = nlp_result.get("crop") or crop
            intent = nlp_result.get("intent") or intent

        # ---------------------------------------------------------
        # STEP 2: Call Agent 1 - Vision Agent
        # ---------------------------------------------------------

        vision_result: Optional[dict[str, Any]] = None

        if image_bytes:
            try:
                vision_result = await call_vision_agent(
                    image_bytes=image_bytes,
                    filename=image_filename or "crop_image.jpg",
                    content_type=image_content_type,
                )

                agent_activity.append(
                    {
                        "agent": "vision-agent",
                        "status": "success",
                        "details": (
                            f"Vision analysis: {vision_result.get('prediction', 'Analyzed')} "
                            f"({vision_result.get('severity_level', 'Diagnostic complete')})"
                        ),
                    }
                )
                logger.info("Agent 1 completed | session_id=%s", session_id)

                # If crop was not identified from the question, infer it from the prediction
                if not crop:
                    crop = _infer_crop_from_prediction(vision_result.get("prediction"))

            except AgentClientError as exc:
                logger.warning(
                    "Agent 1 failed | session_id=%s | error=%s",
                    session_id,
                    exc,
                )
                agent_activity.append(
                    {
                        "agent": "vision-agent",
                        "status": "failed",
                        "details": str(exc),
                    }
                )
        else:
            agent_activity.append(
                {
                    "agent": "vision-agent",
                    "status": "skipped",
                    "details": "No leaf image was provided.",
                }
            )

        # ---------------------------------------------------------
        # STEP 3: Prepare Research Query
        # (use the English translation when available, for better retrieval)
        # ---------------------------------------------------------

        research_query = translated_question or question

        if vision_result:
            prediction = vision_result.get("prediction")
            if prediction:
                research_query = f"{research_query}. Vision analysis indicates: {prediction}."

        # ---------------------------------------------------------
        # STEP 4: Dynamic Routing to Agent 3 - Research/RAG Agent
        # ---------------------------------------------------------

        research_result: Optional[dict[str, Any]] = None

        intent_lower = (intent or "").strip().lower()

        # Intents that do not require agricultural knowledge retrieval
        skip_research_intents = {
            "greeting",
            "hello",
            "small talk",
            "chitchat",
            "unknown",
        }

        # Agent 4 dynamically decides whether Agent 3 is required
        should_call_research = intent_lower not in skip_research_intents

        # If an image was uploaded, research is required to provide
        # evidence-based agricultural information for the vision result.
        if image_bytes is not None:
            should_call_research = True

        if should_call_research:

            agent_activity.append(
                {
                    "agent": "research-agent",
                    "status": "routed",
                    "details": (
                        f"Dynamic routing selected Research Agent "
                        f"for intent: {intent or 'general agricultural query'}"
                    ),
                }
            )

            try:
                research_result = await call_research_agent(
                    query=research_query,
                    crop=crop,
                    topic=None,
                    top_k=5,
                )

                result_count = len(research_result.get("results", []))

                agent_activity.append(
                    {
                        "agent": "research-agent",
                        "status": "success",
                        "details": (
                            f"Retrieved {result_count} relevant agricultural "
                            f"evidence chunks from knowledge base."
                        ),
                    }
                )

                logger.info(
                    "Agent 3 completed | session_id=%s | count=%d",
                    session_id,
                    result_count,
                )

            except AgentClientError as exc:
                logger.warning(
                    "Agent 3 failed | session_id=%s | error=%s",
                    session_id,
                    exc,
                )

                agent_activity.append(
                    {
                        "agent": "research-agent",
                        "status": "warning",
                        "details": f"Research knowledge base notice: {exc}",
                    }
                )

        else:

            agent_activity.append(
                {
                    "agent": "research-agent",
                    "status": "skipped",
                    "details": (
                        f"Dynamic routing skipped Research Agent "
                        f"for intent: {intent or 'unknown'}"
                    ),
                }
            )
        # ---------------------------------------------------------
        # STEP 5: Extract Evidence & Sources
        # ---------------------------------------------------------

        evidence: list[dict[str, Any]] = []
        sources: list[dict[str, Any]] = []

        if research_result:
            for item in research_result.get("results", []):
                evidence.append(
                    {
                        "content": item.get("content"),
                        "source": item.get("source"),
                        "page": item.get("page"),
                        "crop": item.get("crop"),
                        "topic": item.get("topic"),
                        "similarity_score": item.get("similarity_score"),
                    }
                )
                sources.append(
                    {
                        "source": item.get("source"),
                        "page": item.get("page"),
                        "similarity_score": item.get("similarity_score"),
                    }
                )

        # ---------------------------------------------------------
        # STEP 6: Generate Final Agricultural Advisory using Gemini
        # ---------------------------------------------------------

        advisory = ""

        try:
            advisory = await self.llm_service.generate_advisory(
                question=question,
                crop=crop,
                intent=intent,
                vision_result=vision_result,
                evidence=evidence,
                detected_language=detected_language,
            )

            agent_activity.append(
                {
                    "agent": "gemini-llm",
                    "status": "success",
                    "details": "Final agricultural advisory generated with grounded citations.",
                }
            )

        except LLMServiceError as exc:
            logger.error(
                "LLM advisory generation failed | session_id=%s | error=%s",
                session_id,
                exc,
            )
            agent_activity.append(
                {
                    "agent": "gemini-llm",
                    "status": "failed",
                    "details": "Final advisory generation failed.",
                }
            )
            advisory = (
                "I could not generate the final agricultural advisory at this time. "
                "Please consult a qualified agricultural extension officer or expert before taking action."
            )

        # ---------------------------------------------------------
        # STEP 7: Activity Log
        # ---------------------------------------------------------

        await record_audit_log(
            action="AGENT4_ORCHESTRATION",
            status="SUCCESS",
            details={
                "session_id": session_id,
                "question": question,
                "crop": crop,
                "intent": intent,
                "detected_language": detected_language,
                "agents": [
                    activity.get("agent")
                    for activity in agent_activity
                ],
                "agent_activity": agent_activity,
                "evidence_count": len(evidence),
                "vision_used": vision_result is not None,
            },
        )

        logger.info("Agent 4 request completed | session_id=%s", session_id)

        return {
            "success": True,
            "session_id": session_id,
            "question": question,
            "detected_language": detected_language,
            "crop": crop,
            "intent": intent,
            "advisory": advisory,
            "vision_result": vision_result,
            "evidence": evidence,
            "sources": sources,
            "agent_activity": agent_activity,
            "safety_note": (
                "Agricultural recommendations are grounded in retrieved evidence. "
                "Always verify chemical labels and consult extension officers."
            ),
        }