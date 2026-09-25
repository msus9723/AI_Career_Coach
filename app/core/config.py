from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_keys: str = "dev-key-change-me"
    daily_quota: int = 50
    database_url: str = "sqlite:///./data/coach.db"
    log_level: str = "INFO"
    rate_limit: str = "10/minute"

    @property
    def api_key_set(self) -> set[str]:
        return {key.strip() for key in self.api_keys.split(",") if key.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
