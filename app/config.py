from pydantic import BaseSettings
from fastapi import APIRouter

class Settings(BaseSettings):
    app_name: str = "LocalHub BE"
    debug: bool = False
    database_url: str = "sqlite:///./localhub.db"

    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}
