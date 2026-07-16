import json
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.config import get_settings
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from chatbot.keyword_parser import parse_question
from chatbot.prompt import build_prompt 
from chatbot.chatbot import Chatbot
from chatbot.retriever import Retriever

router = APIRouter()

settings = get_settings()

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    history: List[Any] = []

class SourceItem(BaseModel):
    type: str
    id: Optional[int] = None
    name: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    sources: List[SourceItem]
    session_id: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest, db: Session = Depends(get_db)):
    history = payload.history
    question = payload.message
    session_id = payload.session_id

    llm_messages = [
        {"role": "system", "content": "당신은 서울만 담당하는 LocalHub의 관광 안내 챗봇입니다. 아래 정보를 참고해 질문에 답하세요. 아래 정보 외의 장소 등은 언급하지 마세요. 당신은 관광정보를 제공하는 챗봇이지, 일반적인 대화용 챗봇이 아닙니다."
                "관광지, 레포츠, 문화시설, 쇼핑, 숙박, 여행코스, 축제공연행사의 정보만 가지고 있습니다."}
    ]

    for h in history[:-1]:  # 마지막(현재) 질문은 별도 처리
        role = "assistant" if h.get('from') == 'bot' else "user"
        llm_messages.append({"role": role, "content": h.get('text', '')})
    

    # parse
    parsed = parse_question(question) if callable(parse_question) else {"q": question}
    print(f"Parsed question: {parsed}")

    # retrieve
    rows: List[dict] = []
    if Retriever is not None:
        try:
            db_path = settings.database_url.replace("sqlite:///","")
            retr = Retriever(db_path)
            rows = retr.retrieve(parsed) or []
        except Exception:
            rows = []
    else:
        rows = []

    print(f"Retrieved rows: {rows}")    

    if not rows:
        print("No rows retrieved, calling LLM to parse question for search parameters.")
        # call OpenAI (uses openai package)
        openai_key = settings.openai_api_key
        if not openai_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

        # call LLM via team's llm util
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key) # API 키 설정

            messages = [
                        {
                            "role": "system",
                            "content": """
                    당신은 LocalHub의 검색 질의 분석기입니다.

                    사용자의 자연어 질문을 SQLite 검색에 사용할 JSON으로 변환하세요.

                    반드시 JSON만 출력하세요.
                    설명, 코드블록(```), 마크다운은 절대 출력하지 마세요.

                    반환 형식

                    {
                        "district": ["강남구", "서초구"],
                        "contenttype": "39",
                        "keywords": ["코엑스"]
                    }

                    contenttype 코드

                    12 : 관광지
                    14 : 문화시설
                    15 : 축제/공연
                    25 : 여행코스
                    28 : 레포츠
                    32 : 숙박
                    38 : 쇼핑
                    39 : 음식점

                    규칙

                    1. district
                    - 반드시 서울 행정구 이름만 사용한다.
                    - 확실한 경우에는 하나만 넣는다.
                    - 여러 구가 가능하면 모두 넣는다.
                    - 알 수 없으면 []를 반환한다.

                    2. contenttype
                    - 질문에서 명확히 유추 가능한 경우에만 지정한다.
                    - 알 수 없으면 null.

                    3. keywords
                    - 실제 장소명이나 랜드마크처럼 DB에서 검색 가능한 명사만 넣는다.
                    - "추천", "근처", "좋은", "가고싶다", "데이트", "놀러", "알려줘", "있어?", "맛있는", "예쁜" 등의 일반 표현은 넣지 않는다.
                    - 장소명이나 랜드마크가 아니면 keywords에 넣지 않는다.
                    - 없으면 []를 반환한다.

                    4. 절대로 근거 없이 추측하지 않는다.

                    예시

                    사용자: 강남에서 잘 곳 있어?
                    출력:
                    {"district":["강남구"],"contenttype":"32","keywords":[]}

                    사용자: 강남역 맛집
                    출력:
                    {"district":["강남구"],"contenttype":"39","keywords":["강남역"]}

                    사용자: 코엑스 근처 밥집
                    출력:
                    {"district":["강남구"],"contenttype":"39","keywords":["코엑스"]}

                    사용자: 잠실 놀거리
                    출력:
                    {"district":["송파구"],"contenttype":"12","keywords":["잠실"]}

                    사용자: 서울숲 가고싶어
                    출력:
                    {"district":["성동구"],"contenttype":"12","keywords":["서울숲"]}

                    사용자: 광화문 관광
                    출력:
                    {"district":["종로구"],"contenttype":"12","keywords":["광화문"]}

                    사용자: 명동 쇼핑
                    출력:
                    {"district":["중구"],"contenttype":"38","keywords":["명동"]}

                    사용자: 신촌에서 밥 먹자
                    출력:
                    {"district":["마포구","서대문구"],"contenttype":"39","keywords":["신촌"]}

                    사용자: 서울역 근처 관광
                    출력:
                    {"district":["중구","용산구"],"contenttype":"12","keywords":["서울역"]}

                    사용자: 고속터미널 맛집
                    출력:
                    {"district":["서초구","강남구"],"contenttype":"39","keywords":["고속터미널"]}

                    사용자: 건대에서 놀자
                    출력:
                    {"district":["광진구"],"contenttype":"12","keywords":["건대"]}

                    사용자: 성수 카페
                    출력:
                    {"district":["성동구"],"contenttype":"39","keywords":["성수"]}

                    사용자: 2호선 근처 맛집
                    출력:
                    {"district":null,"contenttype":"39","keywords":[]}

                    사용자: 서울 북쪽에서 등산하고 싶어
                    출력:
                    {"district":null,"contenttype":"12","keywords":["등산", "산"]}

                    사용자: 회사 근처 밥집
                    출력:
                    {"district":null,"contenttype":"39","keywords":["밥집"]}

                    사용자: 여자친구랑 분위기 좋은 데 가고 싶어
                    출력:
                    {"district":null,"contenttype":null,"keywords":[]}

                    사용자: 뿌루루
                    출력:
                    {"district":null,"contenttype":null,"keywords":[]}
                    """
                        },
                        {
                            "role": "user",
                            "content": question
                        }
                    ]
            
            completion = client.chat.completions.create( # 최신 문법
                model="gpt-5-mini",
                messages=messages,
                response_format={"type": "json_object"}
            )
            parsed = json.loads(
                completion.choices[0].message.content
            )
            print(f"Parsed question from LLM: {parsed}")
            rows = retr.retrieve(parsed)
            print(f"Retrieved rows after LLM parsing: {rows}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")
    
    # format context and prompt
    prompt = build_prompt(question, rows)

    # call OpenAI (uses openai package)
    openai_key = settings.openai_api_key
    if not openai_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    # call LLM via team's llm util
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key) # API 키 설정

        final_messages = llm_messages + [
            {"role": "user", "content": prompt} 
        ]
        
        completion = client.chat.completions.create( # 최신 문법
            model="gpt-5-mini",
            messages=final_messages
        )
        reply_text = completion.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")

    # build sources summary
    sources = []
    for r in rows:
        sources.append(SourceItem(
            type=r.get("source_type","location"),
            id=r.get("id"),
            content_id=r.get("source_id") or r.get("content_type_id"),
            name=r.get("title")
        ))

    return ChatResponse(reply=reply_text, sources=sources, session_id=session_id)