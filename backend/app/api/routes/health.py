import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
def health(response: Response, database: Annotated[Session, Depends(get_db)]) -> HealthResponse:
    """Report API and database reachability.

    A dead database answers 503 with `database: "down"` rather than an unhandled
    500, so an uptime probe can tell "API is up, storage is not" from "API is
    gone" without parsing a stack trace.
    """
    try:
        database.execute(text("SELECT 1"))
    except SQLAlchemyError:
        # The connection string can carry credentials; log the type only.
        logger.warning("Health check could not reach the database")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="degraded", database="down")
    return HealthResponse(status="ok", database="ok")
