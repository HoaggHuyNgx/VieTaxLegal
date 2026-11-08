"""Google OpenID Connect (authorization code + PKCE), handled entirely on the backend.

Flow state (state, nonce, PKCE verifier, intent) lives in a short-lived signed cookie, so no
server-side store is needed. Google's tokens never reach the browser.
"""

import base64
import hashlib
import secrets
import time
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlencode
from uuid import UUID

import httpx
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import get_settings
from app.core.errors import AppError

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
ISSUERS = ("https://accounts.google.com", "accounts.google.com")
STATE_TTL_SECONDS = 600
STATE_TYPE = "google_oauth_state"  # keeps this JWT from ever passing as an access token

Intent = Literal["login", "link"]


@dataclass(frozen=True)
class FlowState:
    state: str
    nonce: str
    verifier: str
    intent: Intent
    user_id: UUID | None


@dataclass(frozen=True)
class GoogleClaims:
    subject: str
    email: str
    name: str | None


def google_failed() -> AppError:
    return AppError(401, "GOOGLE_AUTH_FAILED", "Đăng nhập bằng Google không thành công.")


def require_google_enabled() -> None:
    if not get_settings().google_enabled:
        raise AppError(503, "GOOGLE_NOT_CONFIGURED", "Đăng nhập Google chưa được cấu hình.")


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def start_flow(intent: Intent, user_id: UUID | None = None) -> tuple[str, str]:
    """Return (authorization URL, signed state cookie value)."""
    require_google_enabled()
    settings = get_settings()
    state, nonce, verifier = (secrets.token_urlsafe(32) for _ in range(3))
    cookie = jwt.encode(
        {
            "type": STATE_TYPE,
            "state": state,
            "nonce": nonce,
            "verifier": verifier,
            "intent": intent,
            "uid": str(user_id) if user_id else None,
            "exp": int(time.time()) + STATE_TTL_SECONDS,
        },
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
            "code_challenge": _pkce_challenge(verifier),
            "code_challenge_method": "S256",
            "prompt": "select_account",
        }
    )
    return f"{AUTHORIZE_URL}?{query}", cookie


def read_state_cookie(cookie: str | None, returned_state: str | None) -> FlowState:
    settings = get_settings()
    if not cookie or not returned_state:
        raise google_failed()
    try:
        payload = jwt.decode(
            cookie, settings.jwt_secret.get_secret_value(), algorithms=[settings.jwt_algorithm]
        )
        if payload.get("type") != STATE_TYPE:
            raise google_failed()
        if not secrets.compare_digest(str(payload["state"]), returned_state):
            raise google_failed()
        user_id = UUID(payload["uid"]) if payload.get("uid") else None
        return FlowState(
            payload["state"], payload["nonce"], payload["verifier"], payload["intent"], user_id
        )
    except (InvalidTokenError, KeyError, ValueError):
        raise google_failed() from None


def exchange_code(code: str, flow: FlowState) -> str:
    """Trade the authorization code for an ID token (server to server, over TLS)."""
    settings = get_settings()
    if settings.google_client_secret is None:  # only reachable if config changed mid-flow
        raise google_failed()
    try:
        response = httpx.post(
            TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret.get_secret_value(),
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
                "code_verifier": flow.verifier,
            },
            timeout=10,
        )
        response.raise_for_status()
        return str(response.json()["id_token"])
    except (httpx.HTTPError, KeyError, ValueError):
        raise google_failed() from None


def parse_id_token(id_token: str, flow: FlowState) -> GoogleClaims:
    """Validate the claims of an ID token received straight from Google's token endpoint.

    OIDC Core 3.1.3.7 lets a client rely on the TLS channel to the token endpoint instead of
    checking the JWT signature, which is why no key set (or cryptography package) is needed.
    """
    settings = get_settings()
    try:
        claims = jwt.decode(id_token, options={"verify_signature": False})
    except InvalidTokenError:
        raise google_failed() from None

    email_verified = claims.get("email_verified") in (True, "true")
    audience = claims.get("aud")
    audiences = audience if isinstance(audience, list) else [audience]
    valid = (
        claims.get("iss") in ISSUERS
        and settings.google_client_id in audiences
        and isinstance(claims.get("exp"), int | float)
        and claims["exp"] > time.time()
        and claims.get("nonce") == flow.nonce
        and bool(claims.get("sub"))
        and bool(claims.get("email"))
        and email_verified
    )
    if not valid:
        raise google_failed()
    return GoogleClaims(str(claims["sub"]), str(claims["email"]).lower(), claims.get("name"))
