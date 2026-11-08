from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.routes.auth import client_host
from app.db.session import get_db
from app.schemas.auth import EmailCodeRequest, EmailCodeVerifyRequest, EmailProofResponse
from app.services import email_otp
from app.services.login_throttle import get_email_code_throttle

router = APIRouter(prefix="/auth/email-code", tags=["Authentication"])


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
def send_email_code(
    payload: EmailCodeRequest,
    request: Request,
    database: Annotated[Session, Depends(get_db)],
) -> Response:
    get_email_code_throttle().acquire(client_host(request))  # every request counts
    email_otp.send_code(database, payload.email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/verify", response_model=EmailProofResponse)
def verify_email_code(
    payload: EmailCodeVerifyRequest,
    database: Annotated[Session, Depends(get_db)],
) -> EmailProofResponse:
    return EmailProofResponse(proof=email_otp.verify_code(database, payload.email, payload.code))
