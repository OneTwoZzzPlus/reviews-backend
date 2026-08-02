import logging
from contextlib import asynccontextmanager
from importlib import import_module
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from admin.setup import seed_initial_admin, setup_admin
from api.reviews import router as reviews_router
from core.config import settings
from core.database import Base, engine
from core.etag import ETagMiddleware

logging.basicConfig(
    encoding="utf-8",
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(levelname)s:[%(asctime)s]:%(name)s: %(message)s",
)
STATIC_DIR = Path(__file__).resolve().parent.parent / "public"
instrumentator = Instrumentator()


@asynccontextmanager
async def lifespan(application: FastAPI):
    async with engine.begin() as conn:
        from models.schemas import CONTENT_SCHEMA, GSPARSER_SCHEMA

        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {CONTENT_SCHEMA}"))
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {GSPARSER_SCHEMA}"))
        import_module("models")
        await conn.run_sync(Base.metadata.create_all)
    await seed_initial_admin()
    instrumentator.expose(application)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(ETagMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["ETag"],
)

instrumentator.instrument(app)
admin = setup_admin(app, engine)

app.include_router(reviews_router)
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
