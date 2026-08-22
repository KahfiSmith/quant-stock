import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.base import Base
from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    settings = Settings(
        app_env="test",
        database_url="sqlite+pysqlite:///:memory:",
        frontend_origin="http://localhost:3000",
        jwt_secret="test-jwt-secret-that-is-at-least-32-characters",
        refresh_token_hmac_key="test-refresh-key-that-is-at-least-32-characters",
    )
    app = create_app(settings)
    Base.metadata.create_all(app.state.database.engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(app.state.database.engine)
