from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import settings

engine = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
)

sync_engine = create_engine(
    url=settings.DATABASE_URL_psycopg,
    echo=False,
)

async_session = async_sessionmaker(bind=engine, autoflush=False, autocommit=False)


async def get_db():
    db = async_session()
    try:
        yield db
    finally:
        await db.close()


