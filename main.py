from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.routes.health import router as health_router
from app.routes.posts import router as posts_router
from chatbot.chatbot import Chatbot 
import seed

# 전역 변수로 챗봇 객체 선언
bot = None

# DB 셋업 함수 (seed.py에 있던 로직을 여기에 넣거나 가져오세요)
def setup_database():
    print("데이터베이스 세팅 시작...")
    seed.main()  # seed.py의 main 함수를 호출하여 DB를 세팅
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 앱 시작 시: DB 셋업 및 챗봇 객체 생성
    global bot
    setup_database()
    bot = Chatbot("localhub.db")
    print("챗봇 초기화 완료.")
    
    yield  # 서버 실행 중
    
    # 2. 앱 종료 시: 필요하다면 정리 작업
    print("서버 종료 중...")

settings = get_settings()

# lifespan을 FastAPI에 등록
app = FastAPI(title=settings.app_name, lifespan=lifespan)

# ... (기존 CORSMiddleware 설정은 그대로 유지) ...
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health_router, prefix="/api")
app.include_router(posts_router, prefix="/api")

# chat 라우터 등록 시 bot 객체를 전달할 수 있도록 구성
try:
    from app.routes.chat import router as chat_router
    app.include_router(chat_router, prefix="/api")
except ImportError:
    pass

@app.get("/")
def root():
    return {"message": f"{settings.app_name} running"}

if __name__ == "__main__":
    import uvicorn
    # 8000번 포트에서 서버 실행
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)