import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from contextlib import asynccontextmanager
from pathlib import Path

from src.postgres import Postgres
from src.auth import AuthMiddleware
from src.routes import router as main_router
from src.content import root_html

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

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

app.add_middleware(AuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router)


@app.get("/favicon.ico", response_class=FileResponse)
async def favicon():
    return FileResponse(STATIC_DIR / "favicon.ico")


@app.get("/", response_class=HTMLResponse)
def root():
    return HTMLResponse(content=root_html, status_code=200)
