#!/usr/bin/env python3
import argparse
import json
import os
from typing import Any, Dict, List

from app.database import engine, SessionLocal, Base
from app import models

def infer_category_from_filename(path: str) -> str:
    name = os.path.basename(path)
    if "관광지" in name:
        return "tourist_spot"
    if "축제" in name:
        return "festival"
    if "숙박" in name:
        return "accommodation"
    if "쇼핑" in name:
        return "shopping"
    if "레포츠" in name or "레포츠" in name.lower():
        return "leports"
    if "문화" in name:
        return "culture"
    return os.path.splitext(name)[0]

def normalize_item(item: Dict[str, Any], category: str) -> Dict[str, Any]:
    def to_float(v):
        try:
            return float(v)
        except Exception:
            return None

    return {
        "content_id": item.get("contentid") or item.get("id") or None,
        "category": category,
        "title": item.get("title") or item.get("name") or "",
        "addr1": item.get("addr1"),
        "addr2": item.get("addr2"),
        "zipcode": item.get("zipcode"),
        "tel": item.get("tel"),
        "first_image": item.get("firstimage"),
        "first_image2": item.get("firstimage2"),
        "mapx": to_float(item.get("mapx")),
        "mapy": to_float(item.get("mapy")),
        "content_type": item.get("contenttypeid") or item.get("contentType"),
        "content_type_id": item.get("contenttypeid"),
        "created_time_raw": item.get("createdtime"),
        "modified_time_raw": item.get("modifiedtime"),
        "extra_raw": json.dumps(item, ensure_ascii=False),
    }

def load_json_items(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # common structure: { "items": [ ... ] }
    if isinstance(data, dict):
        if "items" in data and isinstance(data["items"], list):
            return data["items"]
        # some files may have nested structure like { "response": { "body": { "items": {...} } } }
        # try to traverse common wrappers
        def find_items(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    if k == "items" and isinstance(v, list):
                        return v
                    if isinstance(v, dict):
                        found = find_items(v)
                        if found:
                            return found
            return None
        found = find_items(data)
        if found is not None:
            return found
        # fallback: if top-level keys are numeric indices as dict
        return [data]
    if isinstance(data, list):
        return data
    return []

def main():
    parser = argparse.ArgumentParser(description="Seed locations JSON into SQLite")
    parser.add_argument("files", nargs="+", help="JSON files to load")
    parser.add_argument("--category", help="Force category for all items (optional)")
    parser.add_argument("--create-tables", action="store_true", help="Create DB tables before inserting")
    args = parser.parse_args()

    if args.create_tables:
        Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    inserted = 0
    skipped = 0
    try:
        for fp in args.files:
            inferred = args.category or infer_category_from_filename(fp)
            items = load_json_items(fp)
            for raw in items:
                norm = normalize_item(raw, inferred)
                cid = norm["content_id"]
                if cid:
                    exists = session.query(models.Location).filter(models.Location.content_id == cid).first()
                    if exists:
                        skipped += 1
                        continue
                loc = models.Location(
                    content_id=norm["content_id"],
                    category=norm["category"],
                    title=norm["title"],
                    addr1=norm["addr1"],
                    addr2=norm["addr2"],
                    zipcode=norm["zipcode"],
                    tel=norm["tel"],
                    first_image=norm["first_image"],
                    first_image2=norm["first_image2"],
                    mapx=norm["mapx"],
                    mapy=norm["mapy"],
                    content_type=norm["content_type"],
                    content_type_id=norm["content_type_id"],
                    created_time_raw=norm["created_time_raw"],
                    modified_time_raw=norm["modified_time_raw"],
                    extra_raw=norm["extra_raw"],
                )
                session.add(loc)
                inserted += 1
            # flush per file to keep memory bounded
            session.commit()
        print(f"Inserted: {inserted}, Skipped(existing): {skipped}")
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()