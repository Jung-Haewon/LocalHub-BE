from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.config import get_settings
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text

from chatbot.chatbot import Chatbot

router = APIRouter()

settings = get_settings()

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None

class SourceItem(BaseModel):
    type: str
    id: Optional[int] = None
    name: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    intent: str
    sources: List[SourceItem]
    session_id: Optional[str] = None

def build_prompt(rows: List[dict], question: str) -> str:
    if not rows:
        return ""
    parts = ["다음 지역 정보를 참고하여 답변하세요.\n"]
    for i, r in enumerate(rows, 1):
        parts.append(f"{i}.\n장소명: {r.get('title','')}\n주소: {r.get('addr1','')}\n전화번호: {r.get('tel','')}\n")
    parts.append("\n사용자 질문:\n" + question)
    parts.append("\n주의: 검색 결과에 없는 내용은 추측하지 말고 '찾을 수 없습니다.'라고 답변하세요.")
    return "\n".join(parts)

def classify_intent(message: str) -> str:
    m = message.lower()
    if any(k in m for k in ["축제", "페스티벌"]): return "festival"
    if any(k in m for k in ["맛집", "식당", "음식"]): return "restaurant"
    if any(k in m for k in ["관광", "관광지", "볼거리"]): return "tourist_spot"
    if any(k in m for k in ["글", "게시판", "커뮤니티", "질문"]): return "community_search"
    return "other"

def fallback_retrieve(db: Session, parsed: dict, limit: int = 5) -> List[dict]:
    q = parsed.get("q") or parsed.get("keyword") or ""
    items = []
    if q:
        stmt = text(
            "SELECT id, title, addr1, tel, content_type_id, content_id "
            "FROM locations WHERE title LIKE :p LIMIT :l"
        )
        rows = db.execute(stmt, {"p": f"%{q}%", "l": limit}).mappings().all()
        for r in rows:
            items.append({
                "title": r.get("title"),
                "addr1": r.get("addr1"),
                "tel": r.get("tel"),
                "contenttypeid": r.get("content_type_id"),
                "firstimage": None,
                "source_type": "location",
                "source_id": r.get("id"),
                "content_id": r.get("content_id"),
            })
    return items

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest, db: Session = Depends(get_db)):
    question = payload.message
    session_id = payload.session_id
    intent = classify_intent(question)

    # parse
    parsed = parse_question(question) if callable(parse_question) else {"q": question}

    # retrieve
    rows: List[dict] = []
    if Retriever is not None:
        try:
            db_path = settings.database_url.replace("sqlite:///","")
            retr = Retriever(db_path)
            rows = retr.retrieve(parsed) or []
            # retriever가 빈 결과를 반환하면, DB fallback으로 재시도
            if not rows:
                rows = fallback_retrieve(db, parsed)
        except Exception:
            rows = fallback_retrieve(db, parsed)
    else:
        rows = fallback_retrieve(db, parsed)

    if not rows:
        return ChatResponse(
            reply="조건에 맞는 정보를 찾을 수 없습니다.",
            intent=intent,
            sources=[],
            session_id=session_id,
        )

    # format context and prompt (use team prompt)
    prompt = team_build_prompt(question, rows)

    # call LLM via team's llm util
    try:
        reply_text = ask_llm(prompt)
        if not isinstance(reply_text, str):
            reply_text = str(reply_text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")

    # build sources summary
    sources = []
    for r in rows:
        sources.append(SourceItem(
            type=r.get("source_type","location"),
            id=r.get("source_id") or r.get("content_id"),
            name=r.get("title")
        ))

    return ChatResponse(reply=reply_text, intent=intent, sources=sources, session_id=session_id)