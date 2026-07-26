import logging
from fastapi import Request
from fastapi.security import APIKeyHeader
import jwt
from jwt import PyJWKClient

logger = logging.getLogger("uvicorn.error")

token_header = APIKeyHeader(name="token", auto_error=False)

JWKS_URI = "https://id.itmo.ru/auth/realms/itmo/protocol/openid-connect/certs"
JWT_ISSUER = "https://id.itmo.ru/auth/realms/itmo"
jwks_client = PyJWKClient(JWKS_URI)


class AuthMiddleware:
    def __init__(self, app, auth_verify: bool = True):
        self.app = app
        self.auth_verify = auth_verify

    async def __call__(self, scope, receive, send):
        # Skipping unnecessary requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Getting token from headers
        headers = dict(scope.get("headers", []))
        token = headers.get(b"token", b"").decode("utf-8")

        # Auth logic
        isu_value = await self.token_to_isu(token)

        # Adding ISU to state
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["isu"] = isu_value

        await self.app(scope, receive, send)

    async def token_to_isu(self, token: str) -> int | None:
        if token == "":
            return None

        payload = self.verify_itmo_id_token(token)

        if payload is None:
            return None

        return payload.get("isu")

    def verify_itmo_id_token(self, token: str):
        try:
            if self.auth_verify:
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                return jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["RS256", "PS256"],
                    issuer=JWT_ISSUER,
                    options={
                        "verify_signature": True,
                        "verify_exp": False,
                        "verify_iss": True,
                        "verify_aud": False
                    }
                )
            else:
                if token.isdigit() and len(token) == 6:
                    return {"isu": int(token)}
                return jwt.decode(
                    token,
                    options={"verify_signature": False}
                )

        except jwt.exceptions.ExpiredSignatureError:
            logger.info("JWT: Token has expired.")
        except jwt.exceptions.InvalidIssuerError:
            logger.error("JWT: Invalid issuer.")
        except jwt.exceptions.InvalidAudienceError:
            logger.error("JWT: Token is not intended for this application.")
        except jwt.exceptions.DecodeError:
            logger.error("JWT error: Invalid token structure (not enough segments).")
        except jwt.exceptions.PyJWKClientError as e:
            logger.critical(f"JWT: Could not fetch public keys from ITMO.ID. {e}")
        except Exception as e:
            logger.exception(f"Unexpected JWT validation error: {e}")

        return None


def get_isu(request: Request) -> int:
    return getattr(request.state, "isu", None)
