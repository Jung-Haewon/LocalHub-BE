import json
import glob
import os
from database import SessionLocal, init_db
from models import Location


def load_and_seed():
    init_db()
    db = SessionLocal()
    try:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        files = glob.glob(os.path.join(data_dir, "*.json"))
        for fp in files:
            with open(fp, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                items = data.get("items") or data.get("list") or data
                if isinstance(items, dict) and "items" in items:
                    items = items["items"]
                if not isinstance(items, list):
                    continue
                for it in items:
                    contentid = it.get("contentid") or it.get("id")
                    if contentid:
                        exists = db.query(Location).filter(Location.contentid == contentid).first()
                        if exists:
                            continue
                    loc = Location(
                        contentid=str(contentid) if contentid is not None else None,
                        title=it.get("title") or it.get("name"),
                        region=data.get("region"),
                        contenttypeid=it.get("contenttypeid"),
                        contenttype=data.get("contentType") or data.get("contentType"),
                        addr1=it.get("addr1"),
                        addr2=it.get("addr2"),
                        zipcode=it.get("zipcode"),
                        tel=it.get("tel"),
                        mapx=it.get("mapx"),
                        mapy=it.get("mapy"),
                        mlevel=it.get("mlevel"),
                        areacode=it.get("areacode"),
                        sigungucode=it.get("sigungucode"),
                        lDongRegnCd=it.get("lDongRegnCd"),
                        lDongSignguCd=it.get("lDongSignguCd"),
                        cat1=it.get("cat1"),
                        cat2=it.get("cat2"),
                        cat3=it.get("cat3"),
                        lclsSystm1=it.get("lclsSystm1"),
                        lclsSystm2=it.get("lclsSystm2"),
                        lclsSystm3=it.get("lclsSystm3"),
                        firstimage=it.get("firstimage"),
                        firstimage2=it.get("firstimage2"),
                        cpyrhtDivCd=it.get("cpyrhtDivCd"),
                        createdtime=it.get("createdtime"),
                        modifiedtime=it.get("modifiedtime"),
                        raw=it,
                    )
                    db.add(loc)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    load_and_seed()
    print("Seeding complete")
