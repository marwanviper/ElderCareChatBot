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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
