from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import HealthResponse

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
def health(database: Annotated[Session, Depends(get_db)]) -> HealthResponse:
    database.execute(text("SELECT 1"))
    return HealthResponse(status="ok", database="ok")
