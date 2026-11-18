import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agent import AgentOutput, run_agent
from app.config import settings
from app.translator import (
    detect_language,
    translate_query_to_english,
    translate_answer_to_hindi,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Virtual Assistant for India Groundwater Resource Estimation System (INGRES, SIH25066)",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., description="Citizen or official natural language question", json_schema_extra={"example": "What is the groundwater level in Jaipur in 2023?"})
    session_id: Optional[str] = Field(None, description="Optional session or conversation ID")
    language: Optional[str] = Field("auto", description="Preferred language ('auto', 'en', 'hi')")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Grounded agent natural language answer")
    tool_called: Optional[str] = Field(None, description="Name of database function invoked")
    params: Optional[Dict[str, Any]] = Field(None, description="Resolved and normalized parameters")
    data: Optional[Dict[str, Any]] = Field(None, description="Raw structured data payload returned by tool")
    detected_language: str = Field(default="en", description="Detected language ('en' or 'hi')")
    response_language: str = Field(default="en", description="Language of the answer ('en' or 'hi')")
    latency_ms: Optional[float] = Field(default=None, description="Execution latency in milliseconds")


@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_check": f"{settings.API_PREFIX}/health",
    }


@app.get(f"{settings.API_PREFIX}/health")
def health_check():
    return {
        "status": "ok",
        "service": "ingres-agent-backend",
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gemini_configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here"),
        "database": {
            "path": str(settings.DB_PATH),
            "exists": settings.DB_PATH.exists(),
        },
    }


@app.post(f"{settings.API_PREFIX}/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """Chat endpoint supporting English and Hindi with automatic language detection."""
    start_time = time.perf_counter()
    detected = detect_language(payload.message)
    target_lang = payload.language if payload.language in ("en", "hi") else detected

    # Translate query to English if input is in Hindi
    agent_query = payload.message
    if detected == "hi" or target_lang == "hi":
        agent_query = translate_query_to_english(payload.message)

    # Execute agent pipeline in English
    result: AgentOutput = await run_agent(agent_query)

    # Translate response back to Hindi if requested or input was Hindi
    final_answer = result.answer
    if target_lang == "hi" or detected == "hi":
        final_answer = translate_answer_to_hindi(
            english_answer=result.answer,
            tool_name=result.tool_called,
            params=result.params,
            tool_data=result.data,
        )

    latency_ms = round((time.perf_counter() - start_time) * 1000, 1)

    return ChatResponse(
        answer=final_answer,
        tool_called=result.tool_called,
        params=result.params,
        data=result.data,
        detected_language=detected,
        response_language=target_lang if target_lang in ("en", "hi") else detected,
        latency_ms=latency_ms,
    )
