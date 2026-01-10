import base64
import hashlib
import httpx
import jwt
import logging
import re
import secrets
import time
import urllib

from src.models import *

logger = logging.getLogger("uvicorn.error")

AUTH_CLIENT_ID = "student-personal-cabinet"
AUTH_REDIRECT_URI = "https://my.itmo.ru/login/callback"
AUTH_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/143.0.0.0 Safari/537.36"
AUTH_SCOPES = "openid profile"
AUTH_EXP_TIMEOUT = 300


class AuthItmoIdService:
    class MainException(Exception):
        pass

    class InvalidCredentials(MainException):
        pass

    def __init__(self, **kwargs):
        self._scopes = kwargs.get("scopes", AUTH_SCOPES)
        self._client_id = kwargs.get("client_id", AUTH_CLIENT_ID)
        self._redirect_uri = kwargs.get("redirect_uri", AUTH_REDIRECT_URI)
        self._exp_timeout = kwargs.get("exp_timeout", AUTH_EXP_TIMEOUT)

        self._refresh_token: str | None = None
        self._access_token: str | None = None
        self._access_token_expires_at: float = 0

        self._session = httpx.AsyncClient(
            base_url="https://id.itmo.ru/auth/realms/itmo/protocol/openid-connect",
            headers={"User-Agent": kwargs.get("user_agent", AUTH_USER_AGENT)}
        )

    async def login(self, username: str, password: str) -> TokenResponse:
        self.__username = username
        self.__password = password
        if not self._refresh_token or self._is_refresh_token_expired():
            await self._fetch_login()
        return TokenResponse(
            refresh_token=self._refresh_token,
            access_token=self._access_token
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        self._refresh_token = refresh_token
        if not self._access_token or self._is_access_token_expired():
            await self._fetch_refresh()
        return TokenResponse(
            refresh_token=self._refresh_token,
            access_token=self._access_token
        )

    def _is_access_token_expired(self) -> bool:
        """Check if access token is expired"""
        return time.time() > (self._access_token_expires_at - self._exp_timeout)

    def _set_access_token(self, access_token: str | None) -> float:
        """Save access token and update expires_at"""
        self._access_token = access_token
        if access_token:
            decoded = jwt.decode(self._access_token, options={"verify_signature": False})
            self._access_token_expires_at = decoded.get("exp", 0)

    async def _fetch_refresh(self):
        """Refresh access token using refresh token"""
        payload = {
            "refresh_token": self._refresh_token,
            "client_id": self._client_id,
            "grant_type": "refresh_token",
            "scope": self._scopes
        }
        response = await self._session.post("/token", data=payload)
        if not response.is_success:
            print(self._refresh_token)
            logger.error(response.json())
            raise self.MainException(f"Refresh failed: with status code {response.status_code}")
        data = response.json()
        self._set_access_token(data.get("access_token"))

    @staticmethod
    def _generate_pkce():
        """Generate code_verifier & code_challenge"""
        verifier = secrets.token_urlsafe(32)
        challenge_hash = hashlib.sha256(verifier.encode('utf-8')).digest()
        challenge = base64.urlsafe_b64encode(challenge_hash).decode('utf-8').replace('=', '')
        return verifier, challenge

    async def _fetch_login(self):
        """Login and get access_token and refresh_token with PKCE"""
        # self.logger.log("Step 1")
        verifier, challenge = self._generate_pkce()

        params = {
            "protocol": "oauth2",
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "scope": self._scopes,
            "state": "im_not_a_browser",
            "code_challenge_method": "S256",
            "code_challenge": challenge
        }

        initial_resp = await self._session.get("/auth", params=params, follow_redirects=True)
        # self.logger.log_response(initial_resp)
        if not initial_resp.is_success:
            raise self.MainException(f"Login step 1 failed: with status code {initial_resp.status_code}")

        html = initial_resp.text
        match = re.search(r'"loginAction"\s*:\s*"([^"]+)"', html)
        if not match:
            raise self.MainException("Login step 1 failed: could not find loginActionUrl in page source")

        login_action_url = match.group(1).replace("\\u002f", "/")

        # self.logger.log("Step 2")
        auth_data = {
            "username": self.__username,
            "password": self.__password,
            "rememberMe": "on"
        }

        auth_resp = await self._session.post(login_action_url, data=auth_data, follow_redirects=False)
        # self.logger.log_response(auth_resp)
        if auth_resp.status_code != 302:
            raise self.InvalidCredentials("Invalid credentials!")

        location = auth_resp.headers.get("Location")
        if not location:
            raise self.MainException("Login step 2 failed: 'Location' header is missing (check credentials)")

        parsed_url = urllib.parse.urlparse(location)
        code = urllib.parse.parse_qs(parsed_url.query).get("code")
        if not code:
            raise self.MainException("Login step 2 failed: auth code not found in redirect URL")

        # self.logger.log("Step 3")
        token_payload = {
            "code": code[0],
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": verifier
        }

        token_resp = await self._session.post("/token", data=token_payload)
        # self.logger.log_response(token_resp)
        if not token_resp.is_success:
            raise self.MainException(f"Login step 3 failed: with status code {token_resp.status_code}")

        data = token_resp.json()
        self._set_access_token(data.get("access_token"))
        self._refresh_token = data.get("refresh_token")
