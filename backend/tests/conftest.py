import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test_bootstrap.db")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production-0123456789")
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

from app.core.config import Settings

# Never read the developer's backend/.env: it holds real API keys and local switches
# (e.g. RAG_ENABLED=true) that would make tests depend on the machine. Set before anything
# calls get_settings().
Settings.model_config["env_file"] = None

from app.db.base import Base  # noqa: E402 (after the env_file override)
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.services.login_throttle import (  # noqa: E402
    get_email_code_throttle,
    get_login_throttle,
    get_register_throttle,
)


@pytest.fixture(autouse=True)
def fresh_login_throttle() -> Generator[None, None, None]:
    """The throttle is process-wide state; start every test with an empty one."""
    for throttle in (get_login_throttle, get_register_throttle, get_email_code_throttle):
        throttle.cache_clear()
    yield
    for throttle in (get_login_throttle, get_register_throttle, get_email_code_throttle):
        throttle.cache_clear()


@pytest.fixture
def database_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def client(database_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield database_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def qdrant_memory() -> Generator[QdrantClient, None, None]:
    """In-memory Qdrant: tests never need the Docker server."""
    qdrant = QdrantClient(":memory:")
    try:
        yield qdrant
    finally:
        qdrant.close()
