import bcrypt
from fastapi import Request
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select

from core.database import async_session_maker
from models.content import Moderator


def _safe_bytes(password: str) -> bytes:
    if not password:
        return b""
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    pwd_bytes = _safe_bytes(password)
    hashed = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        pwd_bytes = _safe_bytes(plain_password)
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:  # noqa: BLE001
        return False


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if not username or not password:
            return False

        async with async_session_maker() as session:
            if username.isdigit():
                stmt = select(Moderator).where(Moderator.isu == int(username))
            else:
                stmt = select(Moderator).where(Moderator.name == username)

            result = await session.execute(stmt)
            moderator = result.scalar_one_or_none()

            if (
                moderator
                and moderator.access is True
                and moderator.password_hash
                and verify_password(password, moderator.password_hash)
            ):
                request.session.update(
                    {
                        "token": f"isu_{moderator.isu}",
                        "user_isu": moderator.isu,
                        "user_name": moderator.name,
                    }
                )
                return True

        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return "token" in request.session
