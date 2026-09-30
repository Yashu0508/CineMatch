from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
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
    allowed_origins: str = "http://localhost:3000"
    tmdb_cache_ttl_seconds: int = 300

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
