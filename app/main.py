"""FastAPI 入口：lifespan 建表 + 种子账号 + 路由装配。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1 import auth, chat, kb_admin, reimburse
from app.core.config import get_settings
from app.db.session import async_session, engine
from app.models.base import Base
from app.services import user_service


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        if settings.DATABASE_URL.startswith("postgresql"):
            # 建表前先确保 pgvector 扩展存在（SQLite 演示模式跳过）
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as db:
        await user_service.seed_default_users(db)
    yield


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["ops"])
async def health() -> dict:
    return {"status": "ok", "app": settings.APP_NAME}


app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(reimburse.router, prefix="/api/v1")
app.include_router(kb_admin.router, prefix="/api/v1")
