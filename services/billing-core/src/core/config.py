"""Application configuration settings."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for billing-core-service."""

    PROJECT_NAME: str = "AgroFactura Cloud - Billing Core"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database: Default to SQLite for local development/testing, PostgreSQL for production
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./billing_core.db",
    )

    # Security & Authentication
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET", "super-secret-key-agrofactura-2026-development-change-me"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # M2M Inter-service Token
    INTERNAL_M2M_TOKEN: str = os.getenv(
        "INTERNAL_M2M_TOKEN", "internal-m2m-token-agrofactura-secret-2026"
    )

    # Document Rendering Service internal URL
    DOCUMENT_RENDERING_SERVICE_URL: str = os.getenv(
        "DOCUMENT_RENDERING_SERVICE_URL", "http://document-rendering:8001"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
