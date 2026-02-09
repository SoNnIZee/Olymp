from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    env: str = "dev"
    debug: bool = False
    name: str = "olymp-platform"

    database_url: str

    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24 * 7

    cors_origins: list[str] = Field(default_factory=list)

    pvp_initial_rating: int = 1000
    pvp_rating_k: int = 32
    pvp_matchmaking_max_diff: int = 300
    pvp_match_timeout_seconds: int = 60
    pvp_target_score: int = 3
    pvp_max_rounds: int = 10


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
