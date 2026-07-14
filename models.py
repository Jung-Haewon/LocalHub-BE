from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from database import Base


class Location(Base):
    __tablename__ = "locations"

    contentid = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=True)
    region = Column(String, nullable=True)
    contenttypeid = Column(String, nullable=True)
    contenttype = Column(String, nullable=True)
    addr1 = Column(String, nullable=True)
    addr2 = Column(String, nullable=True)
    zipcode = Column(String, nullable=True)
    tel = Column(String, nullable=True)
    mapx = Column(String, nullable=True)
    mapy = Column(String, nullable=True)
    mlevel = Column(String, nullable=True)
    areacode = Column(String, nullable=True)
    sigungucode = Column(String, nullable=True)
    lDongRegnCd = Column(String, nullable=True)
    lDongSignguCd = Column(String, nullable=True)
    cat1 = Column(String, nullable=True)
    cat2 = Column(String, nullable=True)
    cat3 = Column(String, nullable=True)
    lclsSystm1 = Column(String, nullable=True)
    lclsSystm2 = Column(String, nullable=True)
    lclsSystm3 = Column(String, nullable=True)
    firstimage = Column(String, nullable=True)
    firstimage2 = Column(String, nullable=True)
    cpyrhtDivCd = Column(String, nullable=True)
    createdtime = Column(String, nullable=True)
    modifiedtime = Column(String, nullable=True)
    raw = Column(JSON, nullable=True)


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=True)
    password = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
