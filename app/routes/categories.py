from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import models

router = APIRouter()

# human-friendly display names for category ids
CATEGORY_DISPLAY = {
    "tourist_spot": "관광지",
    "festival": "축제/공연/행사",
    "accommodation": "숙박",
    "shopping": "쇼핑",
    "leports": "레포츠",
    "culture": "문화시설",
    "travel_course": "여행코스",
}


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    # gather distinct categories and counts from locations table
    q = db.query(models.Location.category, func.count(models.Location.id)).group_by(models.Location.category)
    rows = q.all()

    categories = []
    for cat, cnt in rows:
        if not cat:
            continue
        display = CATEGORY_DISPLAY.get(cat, cat)
        # try to pick a thumbnail from any location in this category
        thumb = db.query(models.Location.first_image).filter(models.Location.category == cat, models.Location.first_image != None).first()
        thumbnail = thumb[0] if thumb else None
        categories.append({
            "id": cat,
            "name": display,
            "thumbnail": thumbnail,
            "count": cnt,
        })

    # if DB empty, provide recommended default categories
    if not categories:
        for cid, name in CATEGORY_DISPLAY.items():
            categories.append({"id": cid, "name": name, "thumbnail": None, "count": 0})

    return {"categories": categories}
