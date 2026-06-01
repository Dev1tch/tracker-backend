from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Tracker Backend"
    API_V1_STR: str = "/api/v1"
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Rate limiting (per-IP fixed window, backed by the check_rate_limit RPC)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_GLOBAL_PER_MIN: int = 120
    RATE_LIMIT_LOGIN_PER_MIN: int = 5
    RATE_LIMIT_SIGNUP_PER_MIN: int = 5

    # Email (Brevo)
    BREVO_EMAIL_SENDER_API_KEY: str
    EMAIL_SENDER_NAME: str = "Life Tracker"
    EMAIL_SENDER_EMAIL: str
    ADMIN_NOTIFICATION_EMAIL: Optional[str] = None
    FRONTEND_APP_URL: str = "https://tracker-six-gules.vercel.app"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()
