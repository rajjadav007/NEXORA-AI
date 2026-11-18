from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "nexora-ai-api"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/nexora_ai"
    TEST_DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/nexora_ai_test"
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    RESUME_UPLOAD_MAX_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB default
    RESUME_UPLOAD_STAGING_DIR: str = "storage/staging/resumes"
    RESUME_STORAGE_DIR: str = "storage/resumes"

    @property
    def cors_origins(self) -> List[str]:
        origins = [origin.strip() for origin in self.FRONTEND_ORIGIN.split(",") if origin.strip()]
        return origins or ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
