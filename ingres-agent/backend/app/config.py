import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend root or parent monorepo root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

class Settings:
    PROJECT_NAME: str = "INGRES-Agent Groundwater Virtual Assistant"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DB_PATH: Path = Path(os.getenv("DB_PATH", str(BASE_DIR / "data" / "ingres.db")))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000"
        ).split(",")
        if origin.strip()
    ]

settings = Settings()
