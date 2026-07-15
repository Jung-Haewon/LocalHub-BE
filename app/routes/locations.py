from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import math

from app.database import get_db
from app import models

router = APIRouter()


def _haversine_bbox(lat: float, lon: float, km: float):
    # approximate bbox (degrees) for given radius in km
    # 1 deg latitude ~ 111 km
    delta_lat = km / 111.0
    lat_rad = math.radians(lat)
    delta_lon = km / (111.320 * math.cos(lat_rad)) if math.cos(lat_rad) != 0 else km / 111.320
    return (lon - delta_lon, lon + delta_lon, lat - delta_lat, lat + delta_lat)


@router.get("/locations")
def list_locations(
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    q: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    radius: Optional[float] = Query(None),
    content_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(models.Location)

    if content_id:
        query = query.filter(models.Location.content_id == content_id)

    if category:
        query = query.filter(models.Location.category == category)

    if q:
        query = query.filter(models.Location.title.ilike(f"%{q}%"))

    if lat is not None and lon is not None and radius is not None:
        min_lon, max_lon, min_lat, max_lat = _haversine_bbox(lat, lon, radius)
        query = query.filter(models.Location.mapx >= min_lon, models.Location.mapx <= max_lon,
                             models.Location.mapy >= min_lat, models.Location.mapy <= max_lat)

    total = query.with_entities(func.count(models.Location.id)).scalar() or 0
    items = query.order_by(models.Location.id).offset((page - 1) * size).limit(size).all()

    def _serialize(loc: models.Location):
        return {
            "id": loc.id,
            "content_id": loc.content_id,
            "title": loc.title,
            "addr1": loc.addr1,
            "addr2": loc.addr2,
            "zipcode": loc.zipcode,
            "tel": loc.tel,
            "mapx": loc.mapx,
            "mapy": loc.mapy,
            "first_image": loc.first_image,
            "first_image2": loc.first_image2,
            "category": loc.category,
            "content_type_id": loc.content_type_id,
            "created_time_raw": loc.created_time_raw,
            "modified_time_raw": loc.modified_time_raw,
            "extra_raw": loc.extra_raw,
        }

    return {"total": total, "page": page, "size": size, "items": [_serialize(i) for i in items]}


@router.get("/locations/{loc_id}")
def get_location(loc_id: int, db: Session = Depends(get_db)):
    loc = db.query(models.Location).filter(models.Location.id == loc_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return {
        "id": loc.id,
        "content_id": loc.content_id,
        "title": loc.title,
        "addr1": loc.addr1,
        "addr2": loc.addr2,
        "zipcode": loc.zipcode,
        "tel": loc.tel,
        "mapx": loc.mapx,
        "mapy": loc.mapy,
        "first_image": loc.first_image,
        "first_image2": loc.first_image2,
        "category": loc.category,
        "content_type_id": loc.content_type_id,
        "created_time_raw": loc.created_time_raw,
        "modified_time_raw": loc.modified_time_raw,
        "extra_raw": loc.extra_raw,
    }
