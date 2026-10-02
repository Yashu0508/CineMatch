from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve the repository-root environment file from this module's location so
# the documented `cd backend && uvicorn ...` command loads the same settings as
# a launch from the repository root.  A relative env_file would otherwise
# silently fall back to development defaults when the working directory is
# `backend/`.
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = REPOSITORY_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")
    app_env: str = "development"
    app_log_level: str = "INFO"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./cinematch.db"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    tmdb_access_token: str = ""
    tmdb_api_base_url: str = "https://api.themoviedb.org/3"
    tmdb_language: str = "en-US"
    tmdb_region: str = "IN"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_version: str = "v1"
    recommender_mode: str = "hybrid"
    content_weight: float = 0.45
    collab_weight: float = 0.35
    popularity_weight: float = 0.10
    preference_weight: float = 0.10
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    tmdb_cache_ttl_seconds: int = 300
    omdb_api_key: str = ""
    omdb_api_base_url: str = "https://www.omdbapi.com/"
    omdb_cache_ttl_seconds: int = 300

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
