from fastapi import FastAPI, HTTPException

from app.agent_communication import send_to_agent_2
from app.nlp import analyze_query
from app.schemas import QueryRequest, QueryResponse
from app.multilingual import detect_language, translate_to_english

app = FastAPI(
    title="AgriKetha Query Analysis Agent",
    description="Agent 1 parses farming queries, identifies crops and symptoms, and determines intents.",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "agent": "Query Analysis & NLP Agent",
        "status": "running"
    }


@app.post("/analyze", response_model=QueryResponse)
def analyze(request: QueryRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    if len(question) > 800:
        raise HTTPException(
            status_code=400,
            detail="Question is too long"
        )


    lang = detect_language(question)
    translated_question = None
    
    if lang != "en":
        translated_question = translate_to_english(question, lang)
        query_to_analyze = translated_question
    else:
        query_to_analyze = question

    result = analyze_query(query_to_analyze)

    try:
        agent_2_result = send_to_agent_2(result)
        agent_2_connected = True
    except Exception as e:
        agent_2_result = {
            "status": "offline",
            "message": "Agent 2 is currently unreachable.",
            "error_detail": str(e)
        }
        agent_2_connected = False

    return {
        "success": True,
        "agent": "query-analysis-agent",
        "question": question,
        "detected_language": lang,
        "translated_question": translated_question,
        "agent_1_result": result,
        "agent_2_connected": agent_2_connected,
        "agent_2_result": agent_2_result
    }
