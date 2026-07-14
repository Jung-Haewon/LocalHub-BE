from __future__ import annotations
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class PostCreate(BaseModel):
    category: str = Field(..., max_length=50)
    title: str = Field(..., max_length=255)
    content: str = Field(..., min_length=1)
    author_nickname: Optional[str] = Field("익명", max_length=100)
    password: str = Field(..., min_length=1)


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    password: str = Field(..., min_length=1)


class PostDeleteRequest(BaseModel):
    password: str = Field(..., min_length=1)


class PostListItem(BaseModel):
    id: int
    category: str
    title: str
    author_nickname: str
    created_at: datetime
    view_count: int

    model_config = {"from_attributes": True}


class PostDetail(BaseModel):
    id: int
    category: str
    title: str
    content: str
    author_nickname: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    view_count: int

    model_config = {"from_attributes": True}


class PostListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[PostListItem]

    model_config = {"from_attributes": True}