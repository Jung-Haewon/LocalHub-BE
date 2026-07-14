from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models, schemas
from app.database import get_db

router = APIRouter()


@router.get("/posts", response_model=schemas.PostListResponse)
def list_posts(
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(models.Post)
    if category:
        q = q.filter(models.Post.category == category)

    total = q.with_entities(func.count(models.Post.id)).scalar() or 0
    items = q.order_by(models.Post.created_at.desc()).offset((page - 1) * size).limit(size).all()

    return schemas.PostListResponse(
        total=total,
        page=page,
        size=size,
        items=items,
    )


@router.get("/posts/{post_id}", response_model=schemas.PostDetail)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    post.view_count = (post.view_count or 0) + 1
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.post("/posts", response_model=schemas.PostDetail, status_code=status.HTTP_201_CREATED)
def create_post(payload: schemas.PostCreate, db: Session = Depends(get_db)):
    post = models.Post(
        category=payload.category,
        title=payload.title,
        content=payload.content,
        author_nickname=payload.author_nickname or "익명",
        password=payload.password,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.put("/posts/{post_id}", response_model=schemas.PostDetail)
def update_post(post_id: int, payload: schemas.PostUpdate, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.password != payload.password:
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")
    updated = False
    if payload.title is not None:
        post.title = payload.title
        updated = True
    if payload.content is not None:
        post.content = payload.content
        updated = True
    if updated:
        post.updated_at = datetime.utcnow()
        db.add(post)
        db.commit()
        db.refresh(post)
    return post


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, payload: schemas.PostDeleteRequest, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.password != payload.password:
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")
    db.delete(post)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)