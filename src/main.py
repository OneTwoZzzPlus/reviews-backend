import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from contextlib import asynccontextmanager
from importlib import import_module
from pathlib import Path
from sqlalchemy import text
from core.config import settings
from core.database import engine, Base
from core.auth import AuthMiddleware
from api.reviews import router as reviews_router
from api.mod import router as mod_router
from api.authp import router as authp_router

logging.basicConfig(
    encoding="utf-8",
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(levelname)s:[%(asctime)s]:%(name)s: %(message)s",
)

instrumentator = Instrumentator()


@asynccontextmanager
async def lifespan(application: FastAPI):
    async with engine.begin() as conn:
        from models.schemas import PUBLIC_SCHEMA, CONTENT_SCHEMA, GSPARSER_SCHEMA

        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {PUBLIC_SCHEMA}"))
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {CONTENT_SCHEMA}"))
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {GSPARSER_SCHEMA}"))
        import_module("models")
        await conn.run_sync(Base.metadata.create_all)
    instrumentator.expose(application)
    yield


app = FastAPI(lifespan=lifespan)

instrumentator.instrument(app)

app.add_middleware(AuthMiddleware, auth_verify=settings.AUTH_VERIFY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reviews_router)
app.include_router(authp_router)
app.include_router(mod_router)

STATIC_DIR = Path(__file__).resolve().parent.parent / "public"
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
