from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.config import get_settings
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from chatbot.prompt import build_prompt 

# try to import team's parser/retriever; if not available use a fallback
try:
    from chatbot.retriever import Retriever
    from chatbot.keyword_parser import parse_question
except Exception:
    Retriever = None
    def parse_question(q: str) -> dict:
        # very small placeholder parser: just return keywords
        return {"q": q}

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
    sources: List[SourceItem]
    session_id: Optional[str] = None


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
            sources=[],
            session_id=session_id,
        )

    db_path = settings.database_url.replace("sqlite:///","")
    retr = Retriever(db_path)
    rows = retr.retrieve(parsed)
    
    # format context and prompt
    print(rows)
    prompt = build_prompt(question, rows)

    # call OpenAI (uses openai package)
    openai_key = settings.openai_api_key
    if not openai_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key) # API 키 설정

        messages=[
                {"role": "system", "content": "당신은 LocalHub의 관광 안내 챗봇입니다. 아래 정보를 참고해 질문에 답하세요."},
                {"role": "user", "content": prompt}
            ]

        print("--- [DEBUG] LLM에게 전달되는 실제 프롬프트 시작 ---")
        for msg in messages:
            print(f"Role: {msg['role']}\nContent: {msg['content']}\n{'-'*20}")
        print("--- [DEBUG] LLM에게 전달되는 실제 프롬프트 끝 ---")
        
        completion = client.chat.completions.create( # 최신 문법
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "당신은 LocalHub의 관광 안내 챗봇입니다. 아래 정보를 참고해 질문에 답하세요."},
                {"role": "user", "content": prompt}
            ],
        )
        reply_text = completion.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenAI call failed: {e}")

    # build sources summary
    sources = []
    for r in rows:
        sources.append(SourceItem(
            type=r.get("source_type","location"),
            id=r.get("source_id") or r.get("content_id"),
            name=r.get("title")
        ))

    return ChatResponse(reply=reply_text, sources=sources, session_id=session_id)