from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routes.health import router as health_router
from app.routes.posts import router as posts_router

# chat 라우터는 아직 없을 수 있으니 안전하게 임포트
try:
    from app.routes.chat import router as chat_router
except Exception:
    chat_router = None

settings = get_settings()

app = FastAPI(title=settings.app_name)

# 개발 중에는 모든 오리진 허용. 배포 전에는 프론트 도메인으로 제한하세요.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(health_router, prefix="/api")
app.include_router(posts_router, prefix="/api")
if chat_router:
    app.include_router(chat_router, prefix="/api")


@app.get("/")
def root():
    return {"message": f"{settings.app_name} running"}