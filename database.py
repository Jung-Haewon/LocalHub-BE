from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


DATABASE_URL = "sqlite:///./localhub.db"

engine = create_engine(
	DATABASE_URL,
	connect_args={"check_same_thread": False},  # SQLite specific
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
	"""Create all tables registered on the Base metadata."""
	Base.metadata.create_all(bind=engine)


def get_db():
	"""Yield a database session; use in FastAPI dependencies."""
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

