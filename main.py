from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.health import router as health_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")

@app.get("/")
def root():
    return {"message": f"{settings.app_name} running"}