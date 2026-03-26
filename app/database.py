from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .settings import DATABASE_URL


def _normalize_database_url(url: str) -> str:
    if url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql+psycopg://', 1)
    if url.startswith('postgresql://'):
        return url.replace('postgresql://', 'postgresql+psycopg://', 1)
    return url


resolved_database_url = _normalize_database_url(DATABASE_URL)
connect_args = {'check_same_thread': False} if resolved_database_url.startswith('sqlite') else {}

engine = create_engine(
    resolved_database_url,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
