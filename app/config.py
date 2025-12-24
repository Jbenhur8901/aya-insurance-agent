"""
Configuration centrale de l'application AYA Insurance Agent
"""
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Configuration de l'application"""

    # Application
    APP_NAME: str = "AYA Insurance Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    # Redis/Upstash
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    REDIS_TOKEN: str = os.getenv("REDIS_TOKEN", "")

    # Mobile Money
    EPAY_BASE_URL: str = "https://epay.nodes-hub.com"
    EPAY_API_KEY: str = os.getenv("EPAY_API_KEY", "")

    # Agent Configuration
    DEFAULT_MODEL: str = "gpt-4o-mini"
    VISION_MODEL: str = "gemini-2.0-flash-exp"
    SESSION_TTL: int = 3600  # 1 hour in seconds

    # Webhooks
    BASE_WEBHOOK_URL: str = os.getenv("BASE_WEBHOOK_URL", "http://localhost:8000")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
