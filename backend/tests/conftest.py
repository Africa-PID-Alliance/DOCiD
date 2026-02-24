"""
Shared test fixtures for RRID backend tests.

Uses an in-memory SQLite database with a fresh schema per test session
and provides a Flask test client with a fake JWT identity.
"""

import pytest
from unittest.mock import patch

from app import create_app, db as _db


@pytest.fixture(scope="session")
def app():
    """Create a Flask application configured for testing."""
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "JWT_SECRET_KEY": "test-secret-key",
        "SCICRUNCH_API_KEY": "test-api-key-12345",
        "CACHE_TYPE": "null",
    }

    application = create_app()
    application.config.update(test_config)

    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(autouse=True)
def database_session(app):
    """Provide a clean database session for each test."""
    with app.app_context():
        _db.session.begin_nested()
        yield _db.session
        _db.session.rollback()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def authenticated_client(client):
    """Flask test client with JWT authentication bypassed.

    Patches ``jwt_required`` so every request appears authenticated
    as user ID 1 without needing real tokens.
    """
    with patch(
        "flask_jwt_extended.view_decorators.verify_jwt_in_request"
    ):
        with patch(
            "flask_jwt_extended.utils.get_jwt_identity", return_value=1
        ):
            yield client
