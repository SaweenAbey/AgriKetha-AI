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

class OrchestratorService:
    """
    Agent 4 - Central orchestration service.

    Responsibilities:
    - Coordinate Agent 1 (Vision)
    - Coordinate Agent 2 (Query/NLP)
    - Coordinate Agent 3 (Research/RAG)
    - Aggregate results
    - Prepare information for the advisory LLM
    """

    def __init__(self):
        self.llm_service = LLMService()

    async def process_request(
        self,
        question: str,
        image_bytes: Optional[bytes] = None,
        image_filename: Optional[str] = None,
        image_content_type: Optional[str] = None,
    ) -> dict[str, Any]:

        session_id = str(uuid.uuid4())

        logger.info(
            "Agent 4 request started | session_id=%s",
            session_id,
        )

        agent_activity: list[dict[str, Any]] = []

        # ---------------------------------------------------------
        # STEP 1: Call Agent 2 - Query/NLP Agent
        # ---------------------------------------------------------

        query_result: Optional[dict[str, Any]] = None

        try:
            query_result = await call_query_agent(question)

            agent_activity.append(
                {
                    "agent": "query-agent",
                    "status": "success",
                    "details": "Question analyzed successfully.",
                }
            )

            logger.info(
                "Agent 2 completed | session_id=%s",
                session_id,
            )

        except AgentClientError as exc:
            logger.warning(
                "Agent 2 failed | session_id=%s | error=%s",
                session_id,
                exc,
            )

            agent_activity.append(
                {
                    "agent": "query-agent",
                    "status": "failed",
                    "details": str(exc),
                }
            )

        # ---------------------------------------------------------
        # Extract NLP information
        # ---------------------------------------------------------

        crop = None
        intent = None
        detected_language = None
        translated_question = None

        if query_result:

            detected_language = query_result.get(
                "detected_language"
            )

            translated_question = query_result.get(
                "translated_question"
            )


            nlp_result = query_result.get(
                "agent_1_result",
                {},
            )

            crop = nlp_result.get("crop")
            intent = nlp_result.get("intent")

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
                        "details": "Crop image analyzed successfully.",
                    }
                )

                logger.info(
                    "Agent 1 completed | session_id=%s",
                    session_id,
                )

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
                    "details": "No image was provided.",
                }
            )

        # ---------------------------------------------------------
        # STEP 3: Prepare Research Query
        # ---------------------------------------------------------

        research_query = translated_question or question

        if vision_result:

            prediction = vision_result.get("prediction")

            if prediction:
                research_query = (
                    f"{research_query}. "
                    f"Vision analysis indicates: {prediction}."
                )

        # ---------------------------------------------------------
        # STEP 4: Call Agent 3 - Research/RAG Agent
        # ---------------------------------------------------------

        research_result: Optional[dict[str, Any]] = None

        try:

            research_result = await call_research_agent(
                query=research_query,
                crop=crop,
                topic=None,
                top_k=5,
            )

            agent_activity.append(
                {
                    "agent": "research-agent",
                    "status": "success",
                    "details": "Agricultural evidence retrieved successfully.",
                }
            )

            logger.info(
                "Agent 3 completed | session_id=%s",
                session_id,
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
                    "status": "failed",
                    "details": str(exc),
                }
            )

        # ---------------------------------------------------------
        # STEP 5: Extract Evidence
        # ---------------------------------------------------------

        evidence: list[dict[str, Any]] = []
        sources: list[dict[str, Any]] = []

        if research_result:

            results = research_result.get(
                "results",
                [],
            )

            for item in results:

                evidence.append(
                    {
                        "content": item.get("content"),
                        "source": item.get("source"),
                        "page": item.get("page"),
                        "crop": item.get("crop"),
                        "topic": item.get("topic"),
                        "similarity_score": item.get(
                            "similarity_score"
                        ),
                    }
                )

                sources.append(
                    {
                        "source": item.get("source"),
                        "page": item.get("page"),
                        "similarity_score": item.get(
                            "similarity_score"
                        ),
                    }
                )

        # ---------------------------------------------------------
        # STEP 6: Return aggregated result
        #
        # LLM generation will be added in the next step.
        # ---------------------------------------------------------

        # ---------------------------------------------------------
        # Generate final agricultural advisory using Gemini
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

            agent_activity.append({
                "agent": "gemini-llm",
                "status": "success",
                "details": "Final agricultural advisory generated successfully.",
            })

        except LLMServiceError as exc:
            logger.error(
                "LLM advisory generation failed | session_id=%s | error=%s",
                session_id,
                exc,
            )

            agent_activity.append({
                "agent": "gemini-llm",
                "status": "failed",
                "details": "Final advisory generation failed.",
            })

            advisory = (
                "I could not generate the final agricultural advisory at this time. "
                "Please consult a qualified agricultural expert before taking action."
            )

        logger.info(
            "Agent 4 request completed | session_id=%s",
            session_id,
        )

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
                "Agricultural recommendations should be based on "
                "retrieved evidence. Do not guess pesticide or "
                "fertilizer quantities."
            ),
        }