from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the backend directory (parent of app directory)
BACKEND_DIR = Path(__file__).parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # External Services
    WHATSAPP_NOTIF_ENDPOINT: str = ""  # WhatsApp Business #1 API
    WHATSAPP_INPUT_ENDPOINT: str = ""  # WhatsApp Business #2 API
    EMAIL_SERVICE_ENDPOINT: str = ""  # Email service API
    WEBHOOK_API_KEY: str = ""  # For validating incoming webhooks

    # Firebase Cloud Messaging (Push Notifications)
    FCM_SERVER_KEY: str = ""
    FCM_SENDER_ID: str = ""

    model_config = SettingsConfigDict(
        env_file=".env" if Path(".env").exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )
    # ── Voice workflow ──
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    SARVAM_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-haiku-4-5-20251001"
    CLAUDE_MAX_TOKENS: int = 2048
    MAX_CONCURRENT_VOICE_JOBS: int = 10
    VOICE_RATE_LIMIT_REQUESTS: int = 10
    VOICE_RATE_LIMIT_WINDOW: int = 60
    MAX_AUDIO_SIZE_BYTES: int = 5242880
    MAX_AUDIO_DURATION_SECONDS: int = 600
    MAX_CLIENTS_IN_PROMPT: int = 100
    MAX_RETRIES: int = 3
    RETRY_BASE_DELAY: float = 1.0
    RETRY_MAX_DELAY: float = 30.0
    ALLOWED_AUDIO_TYPES: set = {"audio/ogg", "audio/wav", "audio/webm", "audio/mp4", "audio/mpeg", "audio/aac", "audio/flac", "audio/x-m4a"}

    MAX_CONCURRENT_OCR_JOBS: int = 10
    OCR_RATE_LIMIT_REQUESTS: int = 10
    OCR_RATE_LIMIT_WINDOW: int = 60

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

