"""
Configuration — reads from environment variables.
Locally: loads from a .env file. On Railway: reads injected env vars.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""  # server-side only, never expose to frontend
    supabase_jwt_secret: str = ""

    # App
    app_env: str = "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
