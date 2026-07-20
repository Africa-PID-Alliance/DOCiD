"""
Shared test fixtures for RRID backend tests.

Uses an in-memory SQLite database with a fresh schema per test session
and provides a Flask test client with a fake JWT identity.
"""

import pytest
from unittest.mock import patch

from app import create_app, db as _db
from app.models import UserAccount


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
        "MUTATION_AUDIT_ENABLED": False,
    }

    application = create_app(test_config)

    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(autouse=True)
def database_session(app):
    """Provide a clean database session for each test."""
    with app.app_context():
        _db.drop_all()
        _db.create_all()
        yield _db.session
        _db.session.rollback()
        _db.session.remove()


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
    user = _db.session.get(UserAccount, 1)
    if user is None:
        user = UserAccount(
            user_id=1,
            user_name="test-auth-user",
            full_name="Test Auth User",
            email="test-auth-user@example.test",
            type="email",
            role="user",
            password="unused",
        )
        _db.session.add(user)
        _db.session.flush()

    with patch(
        "flask_jwt_extended.view_decorators.verify_jwt_in_request"
    ):
        with patch(
            "flask_jwt_extended.utils.get_jwt_identity", return_value=1
        ):
            with patch("app.authz.get_jwt_identity", return_value=1):
                yield client
