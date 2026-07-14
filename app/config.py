try:
    from pydantic_settings import BaseSettings
except Exception:
    from pydantic import BaseSettings

from typing import Optional

class Settings(BaseSettings):
    app_name: str = "LocalHub BE"
    debug: bool = False
    database_url: str = "sqlite:///./localhub.db"
    openai_api_key: Optional[str] = None

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

def get_settings() -> Settings:
    return Settings()