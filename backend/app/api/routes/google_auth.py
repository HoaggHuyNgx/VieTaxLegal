from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.auth import set_auth_cookies
from app.core.config import get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.models.user import User
from app.services import google_oauth
from app.services.oauth_accounts import link_google, sign_in_with_google
from app.services.refresh_tokens import issue_refresh_token

router = APIRouter(prefix="/auth/google", tags=["Authentication"])

STATE_COOKIE = "vietaxlegal_google_state"
STATE_COOKIE_PATH = f"{get_settings().api_prefix}/auth/google"


def _redirect_to_google(url: str, state_cookie: str) -> RedirectResponse:
    response = RedirectResponse(url, status_code=302)
    response.set_cookie(
        key=STATE_COOKIE,
        value=state_cookie,
        max_age=google_oauth.STATE_TTL_SECONDS,
        httponly=True,
        secure=get_settings().is_production,
        samesite="lax",  # Google comes back with a top-level GET, which Lax still carries
        path=STATE_COOKIE_PATH,
    )
    return response


def _back_to_app(path: str, **params: str) -> RedirectResponse:
    query = f"?{urlencode(params)}" if params else ""
    response = RedirectResponse(f"{get_settings().frontend_url}{path}{query}", status_code=302)
    response.delete_cookie(STATE_COOKIE, path=STATE_COOKIE_PATH, httponly=True, samesite="lax")
    return response


@router.get("/login")
def google_login() -> Response:
    url, state_cookie = google_oauth.start_flow("login")
    return _redirect_to_google(url, state_cookie)


@router.get("/link")
def google_link(current_user: Annotated[User, Depends(get_current_user)]) -> Response:
    url, state_cookie = google_oauth.start_flow("link", current_user.id)
    return _redirect_to_google(url, state_cookie)


@router.get("/callback")
def google_callback(
    database: Annotated[Session, Depends(get_db)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    state_cookie: Annotated[str | None, Cookie(alias=STATE_COOKIE)] = None,
) -> Response:
    failure_path = "/"
    try:
        flow = google_oauth.read_state_cookie(state_cookie, state)
        failure_path = "/settings" if flow.intent == "link" else "/"
        if error or not code:  # the user cancelled on Google's screen, or Google refused
            raise google_oauth.google_failed()
        claims = google_oauth.parse_id_token(google_oauth.exchange_code(code, flow), flow)

        if flow.intent == "link":
            user = database.get(User, flow.user_id) if flow.user_id else None
            if user is None:
                raise google_oauth.google_failed()
            link_google(database, user, claims)
            return _back_to_app("/settings", google="linked")

        user = sign_in_with_google(database, claims)
        response = _back_to_app("/chat")
        set_auth_cookies(response, user, issue_refresh_token(database, user, False), False)
        return response
    except AppError as failure:
        return _back_to_app(failure_path, authError=failure.code)
