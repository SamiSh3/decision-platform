"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_name: str = "decision-platform"
    app_env: str = "local"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = (
        "postgresql+psycopg://decision_user:decision_password@localhost:5432/decision_platform"
    )

    # JWT
    jwt_secret_key: str = Field(default="change-me")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    backend_cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Logging
    log_level: str = "INFO"
    log_json: bool = True

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
