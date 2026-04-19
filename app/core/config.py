from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    groq_api_key_70b: str = ""
    groq_api_key_8b: str = ""
    langchain_api_key: str = ""
    langchain_tracing_v2: str = "false"   # disabled by default — avoids LangSmith 403 errors
    langchain_project: str = "nexusai-dev"
    secret_key: str = "nexusai-dev-secret-2024-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    environment: str = "development"
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"
    model_simple: str = "llama-3.1-8b-instant"
    model_complex: str = "llama-3.3-70b-versatile"
    google_client_id: str = ""
    google_client_secret: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

# No lru_cache — settings reload fresh on every server restart
settings = Settings()

def get_groq_key() -> str:
    """Returns first available GROQ key, with clear error if missing."""
    key = settings.groq_api_key_70b or settings.groq_api_key_8b
    if not key or key.startswith("gsk_PASTE") or key == "your_key_here":
        raise ValueError(
            "GROQ API key not set! Open backend/.env and set:\n"
            "GROQ_API_KEY_70B=gsk_your_actual_key_here\n"
            "Get a free key at: console.groq.com"
        )
    return key
