"""Configuration management using Pydantic Settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = Field(
        default=f"sqlite:///{BASE_DIR / 'data' / 'ecommerce_analytics.db'}",
        description="Database connection URL (PostgreSQL or SQLite)",
    )

    # Data paths
    RAW_DATA_PATH: str = Field(
        default=str(BASE_DIR / "data" / "raw" / "online_retail.csv"),
        description="Path to raw input CSV",
    )
    PROCESSED_DATA_PATH: str = Field(
        default=str(BASE_DIR / "data" / "processed" / "clean_retail_transactions.csv"),
        description="Path for cleaned output CSV",
    )
    REJECTED_RECORDS_PATH: str = Field(
        default=str(BASE_DIR / "data" / "processed" / "rejected_records.csv"),
        description="Path for rejected quarantined records CSV",
    )
    REPORTS_DIR: str = Field(
        default=str(BASE_DIR / "reports"),
        description="Directory for data quality and validation reports",
    )

    # Logging & Environment
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    APP_ENV: str = Field(default="development", description="Application environment")


settings = Settings()
