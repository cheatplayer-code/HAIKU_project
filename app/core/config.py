"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    app_name: str = "Birge API"
    debug: bool = False

    class Config:
        env_prefix = "BIRGE_"


settings = Settings()
