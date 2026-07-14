from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from .database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    author_nickname = Column(String(100), nullable=False, default="익명")
    password = Column(String(255), nullable=False)  # 평문 저장 (교육 목적)
    view_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, nullable=True)

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 원본 API의 contentid (외부 ID)
    content_id = Column(String(50), unique=True, index=True, nullable=True)
    # 대분류(예: tourist_spot, festival, restaurant, 등) — 데이터 적재/처리 시 결정
    category = Column(String(50), nullable=True)
    title = Column(String(255), nullable=False)
    addr1 = Column(String(255), nullable=True)
    addr2 = Column(String(255), nullable=True)
    zipcode = Column(String(20), nullable=True)
    tel = Column(String(100), nullable=True)
    first_image = Column(String(1024), nullable=True)
    first_image2 = Column(String(1024), nullable=True)
    mapx = Column(Float, nullable=True)  # longitude
    mapy = Column(Float, nullable=True)  # latitude
    content_type = Column(String(50), nullable=True)
    content_type_id = Column(String(20), nullable=True)
    created_time_raw = Column(String(50), nullable=True)   # 원본 timestamp 문자열 보존
    modified_time_raw = Column(String(50), nullable=True)
    extra_raw = Column(Text, nullable=True)  # 원본 JSON의 다른 필드를 JSON 문자열로 저장 가능