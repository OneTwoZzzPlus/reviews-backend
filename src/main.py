import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

from src.database.postgres import Postgres
from src.auth import AuthMiddleware
from src.routes.reviews import router as reviews_router
from src.routes.auxiliary import router as auxiliary_router
from src.routes.authp import router as authp_router


# ENV DATABASE="postgresql://user:password@localhost:port/db_name"
conn_str = os.getenv("DATABASE")
if conn_str is None:
    raise Exception("DATABASE environment variable not set")

# ENV AUTH_VERIFY: bool
env_str = os.getenv("AUTH_VERIFY", "TRUE")
auth_verify = env_str in ['true', 'True', 'TRUE', '1']


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.database = Postgres(conn_str)
    await application.state.database.connect()
    yield
    await application.state.database.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(AuthMiddleware, auth_verify=auth_verify)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reviews_router)
app.include_router(authp_router)
app.include_router(auxiliary_router)
