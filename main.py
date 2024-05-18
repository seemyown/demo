import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
import redis.asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from config import settings, setup_logging
from database.models import create_tables
from endpoints.routers import profile, service


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    redis = aioredis.from_url(f"redis://{settings.REDIS_HOST}", encoding="utf-8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    yield

app = FastAPI(
    debug=settings.mode,
    title=settings.TITLE,
    version=f"{settings.VERSION}",
    lifespan=lifespan
)

setup_logging()
logger = logging.getLogger(__name__)


app.include_router(profile, prefix="/v2/users")
app.include_router(service, prefix="/v2/service")


@app.get("/")
async def root():
    return {"title": app.__getattribute__("title"),
            "service-version": app.__getattribute__("version")[:5],
            "application-version": settings.ORIGIN_VERSION}


if __name__ == "__main__":
    uvicorn.run(app, port=8001)
