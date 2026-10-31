import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "../../../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Twilio WhatsApp API
    TWILIO_ACCOUNT_SID: str = Field(default="")
    TWILIO_AUTH_TOKEN: str = Field(default="")
    TWILIO_WHATSAPP_NUMBER: str = Field(default="whatsapp:+14155238886")

    # Meta WhatsApp Cloud API (kept for backward compatibility)
    WHATSAPP_PHONE_NUMBER_ID: str = Field(default="")
    WHATSAPP_ACCESS_TOKEN: str = Field(default="")
    WHATSAPP_VERIFY_TOKEN: str = Field(default="munim_verify_2026")
    WHATSAPP_API_VERSION: str = Field(default="v19.0")

    # Owner details (international format without +, e.g. 919876543210)
    OWNER_WHATSAPP_NUMBER: str = Field(default="")

    # Google Sheets
    GOOGLE_SERVICE_ACCOUNT_JSON: str = Field(default="./backend/data/service_account.json")
    GOOGLE_SHEET_ID: str = Field(default="")

    # AI (Gemini & Groq)
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash")
    GROQ_API_KEY: str = Field(default="")

    # App settings
    APP_ENV: str = Field(default="development")
    APP_SECRET_KEY: str = Field(default="munim-ai-hackathon-secret-2026")
    LOG_LEVEL: str = Field(default="INFO")
    DATABASE_URL: str = Field(default="sqlite:///./backend/data/munim.db")
    DRY_RUN: bool = Field(default=False)
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://127.0.0.1:3000")

    # Supabase
    SUPABASE_URL: str = Field(default="")
    SUPABASE_PUBLISHABLE_KEY: str = Field(default="")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
