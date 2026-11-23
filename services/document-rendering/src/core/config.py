"""Application configuration settings for document-rendering-service."""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for document-rendering-service."""

    PROJECT_NAME: str = "AgroFactura Cloud - Document Rendering"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # M2M Inter-service Token
    INTERNAL_M2M_TOKEN: str = os.getenv(
        "INTERNAL_M2M_TOKEN", "internal-m2m-token-agrofactura-secret-2026"
    )

    # Cloud Brokers Mock Modes (for local development, CI and testing)
    GDRIVE_MOCK_MODE: bool = os.getenv("GDRIVE_MOCK_MODE", "true").lower() == "true"
    SMTP_MOCK_MODE: bool = os.getenv("SMTP_MOCK_MODE", "true").lower() == "true"

    # Optional Real SMTP Config
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.example.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
