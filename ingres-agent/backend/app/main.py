from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agent import AgentOutput, run_agent
from app.config import settings

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


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Grounded agent natural language answer")
    tool_called: Optional[str] = Field(None, description="Name of database function invoked")
    params: Optional[Dict[str, Any]] = Field(None, description="Resolved and normalized parameters")
    data: Optional[Dict[str, Any]] = Field(None, description="Raw structured data payload returned by tool")


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
    """Chat endpoint for citizen and official groundwater queries."""
    result: AgentOutput = await run_agent(payload.message)
    return ChatResponse(
        answer=result.answer,
        tool_called=result.tool_called,
        params=result.params,
        data=result.data,
    )
