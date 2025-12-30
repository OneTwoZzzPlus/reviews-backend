import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager

from src.postgres import Postgres
from src.routes import router as main_router

# ENV DATABASE="postgresql://user:password@localhost:port/db_name"
conn_str = os.getenv("DATABASE")
if conn_str is None:
    raise Exception("DATABASE environment variable not set")


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.database = Postgres(conn_str)
    await application.state.database.connect()
    yield
    await application.state.database.disconnect()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(main_router)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=PlainTextResponse)
def root():
    return "Reviews API"
