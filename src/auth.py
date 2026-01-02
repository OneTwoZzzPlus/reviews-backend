from fastapi import Request
from fastapi.security import APIKeyHeader
import jwt

token_header = APIKeyHeader(name="token", auto_error=False)


class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Skipping unnecessary requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Getting token from headers
        headers = dict(scope.get("headers", []))
        token = headers.get(b"token", b"").decode("utf-8")

        # Auth logic
        isu_value = await token_to_isu(token)

        # Adding ISU to state
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["isu"] = isu_value

        await self.app(scope, receive, send)


async def token_to_isu(token: str) -> int | None:
    if token == "":
        return None

    payload = decode_token(token)

    if payload is None:
        return None

    return payload.get("isu")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            jwt=token,
            options={"verify_signature": False}
        )
    except jwt.PyJWTError as jwt_error:
        return None


def get_isu(request: Request) -> int:
    return getattr(request.state, "isu", None)
