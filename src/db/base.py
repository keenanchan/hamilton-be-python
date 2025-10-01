from sqlalchemy.orm import DeclarativeBase, sessionmaker, scoped_session
from sqlalchemy import create_engine
from src.core.config import config

class Base(DeclarativeBase):
    pass


engine = create_engine(config.DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
db_session = scoped_session(SessionLocal)


def get_db():
    db = db_session()
    try:
        yield db
    finally:
        db.close()