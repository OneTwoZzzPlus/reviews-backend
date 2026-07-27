from collections.abc import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

DATABASE_URL = f"postgresql+asyncpg://{settings.PG_USERNAME}:{settings.PG_PASSWORD}@{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DATABASE}"

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.PG_ECHO,
    pool_pre_ping=True,
    pool_recycle=3600,
)

async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    metadata = MetaData()


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
