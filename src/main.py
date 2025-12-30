import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
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


@app.get("/", response_class=PlainTextResponse)
def root():
    return "Reviews API"


@app.get("/favicon.ico", response_class=FileResponse)
def favicon():
    return FileResponse(os.path.join("../static", "favicon.ico"))
