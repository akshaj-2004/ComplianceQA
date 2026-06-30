from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    QDRANT_API_KEY: str
    QDRANT_CLUSTER_ENDPOINT: str
    GEMINI_API_KEY: str
    HUGGINGFACEHUB_API_TOKEN: str
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore"
    )

settings = Settings()# pyright: ignore[reportCallIssue]