from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables or .env."""

    app_name: str = "ElderCare Chatbot API"
    app_version: str = "1.0.0"
    debug: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./eldercare.db"

    # Security & JWT
    SECRET_KEY: str = "insecure-dev-secret-key-change-in-production-must-be-long"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Logging
    LOG_LEVEL: str = "INFO"

    # API Prefix
    API_V1_PREFIX: str = "/api/v1"

    # AI & LLM Provider Settings
    DEFAULT_LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str | None = None
    GEMINI_DEFAULT_MODEL: str = "gemini-3.5-flash"
    OPENAI_API_KEY: str | None = None
    OPENAI_DEFAULT_MODEL: str = "gpt-3.5-turbo"
    CHAT_MAX_HISTORY_MESSAGES: int = 20
    CHAT_DEFAULT_TEMPERATURE: float = 0.3
    CHAT_DEFAULT_MAX_TOKENS: int = 1024

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
