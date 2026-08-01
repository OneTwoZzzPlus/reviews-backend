from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from faker import Faker
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.community.postgres import PostgresContainer

import models.content
import models.insights
import models.reviews  # noqa: F401
from core.database import Base, get_database
from main import app
from models.schemas import CONTENT_SCHEMA, GSPARSER_SCHEMA

# ==================================================
# UNIT TESTS (MOCKS)
# ==================================================


@pytest.fixture(scope="session", autouse=True)
def faker():
    return Faker()


@pytest.fixture
def mock_db():
    session = AsyncMock()

    # Автоматически генерируем id для новых ORM-моделей при добавлении в сессию
    def mock_add(instance):
        if hasattr(instance, "id") and getattr(instance, "id", None) is None:
            instance.id = 1

    session.add = MagicMock(side_effect=mock_add)
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.rollback = AsyncMock()

    def return_data(*values):
        def make_mock_result(val):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = val
            mock_result.scalar_one.return_value = val

            mock_scalars = MagicMock()
            mock_scalars.first.return_value = (
                val[0] if isinstance(val, list) and val else val
            )
            mock_scalars.all.return_value = (
                val if isinstance(val, list) else ([val] if val is not None else [])
            )
            mock_scalars.unique.return_value = mock_scalars
            mock_result.scalars.return_value = mock_scalars
            return mock_result

        def make_mock_scalars(val):
            mock_scalars = MagicMock()
            mock_scalars.first.return_value = (
                val[0] if isinstance(val, list) and val else val
            )
            mock_scalars.all.return_value = (
                val if isinstance(val, list) else ([val] if val is not None else [])
            )
            mock_scalars.unique.return_value = mock_scalars
            return mock_scalars

        if len(values) == 1:
            val = values[0]
            session.execute.return_value = make_mock_result(val)
            session.execute.side_effect = None
            session.scalars.return_value = make_mock_scalars(val)
            session.scalars.side_effect = None
        else:
            session.execute.side_effect = [make_mock_result(v) for v in values]
            session.scalars.side_effect = [make_mock_scalars(v) for v in values]

    session.return_data = return_data
    session.return_data(None)
    return session


# ==================================================
# INTEGRATION TESTS (TESTCONTAINERS)
# ==================================================


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def init_database_schema(postgres_container):
    sync_url = postgres_container.get_connection_url()
    async_url = sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    engine = create_async_engine(async_url, echo=False)

    async with engine.begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {CONTENT_SCHEMA}"))
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {GSPARSER_SCHEMA}"))
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_engine(postgres_container, init_database_schema):
    sync_url = postgres_container.get_connection_url()
    async_url = sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    engine = create_async_engine(async_url, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    async_session_maker = async_sessionmaker(bind=db_engine, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session

    async with db_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            table_fullname = (
                f"{table.schema}.{table.name}" if table.schema else table.name
            )
            await conn.execute(text(f"TRUNCATE TABLE {table_fullname} CASCADE;"))


@pytest_asyncio.fixture
async def client(db_session):
    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_database] = _get_db_override

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.pop(get_database, None)
