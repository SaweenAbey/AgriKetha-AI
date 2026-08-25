from fastapi import FastAPI, HTTPException, File, UploadFile, Form
import tempfile
import os
import speech_recognition as sr

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


@app.post("/analyze-audio", response_model=QueryResponse)
def analyze_audio(
    file: UploadFile = File(...),
    language_code: str = Form("si-LK")
):
    if not file.content_type.startswith("audio/") and not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".ogg", ".webm")):
        raise HTTPException(
            status_code=400,
            detail="File must be an audio file"
        )

    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, f"temp_{file.filename}")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            buffer.write(file.file.read())
            
        r = sr.Recognizer()
        with sr.AudioFile(temp_file_path) as source:
            audio_data = r.record(source)
            
        try:
            transcribed_text = r.recognize_google(audio_data, language=language_code)
        except sr.UnknownValueError:
            raise HTTPException(
                status_code=400,
                detail="Speech Recognition could not understand the audio"
            )
        except sr.RequestError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Speech Recognition service error: {str(e)}"
            )
            
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    lang = detect_language(transcribed_text)
    translated_question = None
    
    if lang != "en":
        translated_question = translate_to_english(transcribed_text, lang)
        query_to_analyze = translated_question
    else:
        query_to_analyze = transcribed_text

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
        "question": transcribed_text,
        "detected_language": lang,
        "translated_question": translated_question,
        "agent_1_result": result,
        "agent_2_connected": agent_2_connected,
        "agent_2_result": agent_2_result
    }
