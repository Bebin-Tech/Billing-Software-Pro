from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import settings
from fastapi import HTTPException
import os


class Base(DeclarativeBase):
    pass


options = {'pool_pre_ping': True}
if settings.database_url.startswith('mysql'):
    options['connect_args'] = {'connect_timeout': 10}
    if os.environ.get('VERCEL'):
        options.update(pool_size=1, max_overflow=0, pool_timeout=10, pool_recycle=300)
engine = create_engine(settings.database_url, **options) if settings.database_url else None
SessionLocal = sessionmaker(engine, expire_on_commit=False) if engine is not None else None


def get_db():
    if SessionLocal is None:
        raise HTTPException(503, 'MySQL is not connected. Configure DATABASE_URL in Vercel and apply the migrations.')
    with SessionLocal() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
