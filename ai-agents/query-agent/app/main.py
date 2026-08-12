from fastapi import FastAPI, HTTPException

from app.agent_communication import send_to_agent_2
from app.nlp import analyze_query
from app.schemas import QueryRequest, QueryResponse

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

    
    result = analyze_query(question)

    
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
        "agent_1_result": result,
        "agent_2_connected": agent_2_connected,
        "agent_2_result": agent_2_result
    }
