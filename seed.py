#!/usr/bin/env python3
import argparse
import json
import glob
import os
from typing import Any, Dict, List, Optional

from app.database import engine, SessionLocal, Base
from app import models
from database import init_db

Base.metadata.create_all(bind=engine)

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

def to_float(v):
    try:
        return float(v)
    except Exception:
        return None

def normalize_item(item: Dict[str, Any], category: str, outer: Optional[Dict[str,Any]] = None) -> Dict[str, Any]:
    # outer may contain file-level metadata like region or contentType
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
        "mapx": to_float(item.get("mapx") or (outer or {}).get("mapx")),
        "mapy": to_float(item.get("mapy") or (outer or {}).get("mapy")),
        "content_type": item.get("contenttypeid") or item.get("contentType") or (outer or {}).get("contentType"),
        "content_type_id": item.get("contenttypeid"),
        "created_time_raw": item.get("createdtime"),
        "modified_time_raw": item.get("modifiedtime"),
        "extra_raw": json.dumps(item, ensure_ascii=False),
        # keep a few common raw fields from the file-level if present
        "region": (outer or {}).get("region"),
    }

def load_json_items(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # try multiple common shapes
    # case A: { "items": [ ... ] }
    if isinstance(data, dict):
        if "items" in data and isinstance(data["items"], list):
            return data["items"], data
        # nested wrappers: response -> body -> items
        def find_items_with_outer(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    if k == "items" and isinstance(v, list):
                        return v, d
                    if isinstance(v, dict):
                        found = find_items_with_outer(v)
                        if found:
                            return found
            return None
        found = find_items_with_outer(data)
        if found is not None:
            return found
        # maybe top-level is the list itself or has 'list'
        if "list" in data and isinstance(data["list"], list):
            return data["list"], data
        # otherwise treat top-level dict as a single item list
        return [data], data
    if isinstance(data, list):
        return data, None
    return [], None

def gather_files_from_dir(data_dir: str) -> List[str]:
    patterns = ["*.json"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(data_dir, p)))
    files.sort()
    return files

def main(args=None):
    init_db()
    parser = argparse.ArgumentParser(description="Seed locations JSON into SQLite")
    parser.add_argument("files", nargs="*", help="JSON files to load (if empty, load all from ./data)")
    parser.add_argument("--category", help="Force category for all items (optional)")
    parser.add_argument("--create-tables", action="store_true", help="Create DB tables before inserting")
    parsed_args = parser.parse_args(args=args if args is not None else [])

    if parsed_args.create_tables:
        Base.metadata.create_all(bind=engine)

    # determine files
    if parsed_args.files:
        files = parsed_args.files
    else:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        files = gather_files_from_dir(data_dir)

    session = SessionLocal()
    inserted = 0
    skipped = 0
    try:
        for fp in files:
            inferred = parsed_args.category or infer_category_from_filename(fp)
            items_result = load_json_items(fp)
            # load_json_items may return (items, outer) or items only
            if isinstance(items_result, tuple):
                items, outer = items_result
            else:
                items, outer = items_result, None
            for raw in items:
                norm = normalize_item(raw, inferred, outer)
                cid = norm["content_id"]
                if cid:
                    exists = session.query(models.Location).filter(models.Location.content_id == cid).first()
                    if exists:
                        skipped += 1
                        continue
                loc = models.Location(
                    content_id=norm.get("content_id"),
                    category=norm.get("category"),
                    title=norm.get("title"),
                    addr1=norm.get("addr1"),
                    addr2=norm.get("addr2"),
                    zipcode=norm.get("zipcode"),
                    tel=norm.get("tel"),
                    first_image=norm.get("first_image"),
                    first_image2=norm.get("first_image2"),
                    mapx=norm.get("mapx"),
                    mapy=norm.get("mapy"),
                    content_type=norm.get("content_type"),
                    content_type_id=norm.get("content_type_id"),
                    created_time_raw=norm.get("created_time_raw"),
                    modified_time_raw=norm.get("modified_time_raw"),
                    extra_raw=norm.get("extra_raw"),
                )
                session.add(loc)
                inserted += 1
            # flush per file to keep memory bounded
            session.commit()
        print(f"Inserted: {inserted}, Skipped(existing): {skipped}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()