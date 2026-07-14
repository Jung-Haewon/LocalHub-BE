try:
    from pydantic_settings import BaseSettings
except Exception:
    from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "LocalHub BE"
    debug: bool = False
    database_url: str = "sqlite:///./localhub.db"

    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()