"""Security regression tests for unauthenticated account bootstrap flows."""

import hashlib

from app import db, limiter
from app.models import MutationAudit, PasswordResets, RegistrationTokens, UserAccount
from werkzeug.security import check_password_hash, generate_password_hash


BOOTSTRAP_HEADERS = {"X-Auth-Bootstrap-Secret": "test-bootstrap-secret"}


def _user():
    user = UserAccount(
        user_name="reset-user",
        full_name="Reset User",
        email="reset@example.test",
        type="email",
        role="user",
        password=generate_password_hash("old-password"),
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_direct_registration_and_reset_initiation_are_rejected(app, client):
    app.config["AUTH_BOOTSTRAP_SECRET"] = "test-bootstrap-secret"
    limiter.reset()
    registration = client.post("/api/v1/auth/register", json={"type": "email"})
    reset = client.post(
        "/api/v1/auth/request-password-reset",
        json={"email": "victim@example.test", "token": "attacker-token"},
    )
    assert registration.status_code == 403
    assert reset.status_code == 403


def test_legacy_social_auth_routes_are_retired(client):
    assert client.post("/api/v1/auth/social_auth", json={}).status_code == 410
    assert client.post("/api/v1/auth/social-auth-register", json={}).status_code == 410
    assert client.post("/api/v1/auth/set-password-social", json={}).status_code == 401


def test_registration_token_is_hashed_and_validated(app, client):
    app.config["AUTH_BOOTSTRAP_SECRET"] = "test-bootstrap-secret"
    raw_token = "registration-token-with-enough-entropy"
    response = client.post(
        "/api/v1/auth/store-registration-token",
        json={
            "email": "new-user@example.test",
            "token": raw_token,
            "expires_at": "2026-08-01T12:00:00",
        },
        headers=BOOTSTRAP_HEADERS,
    )
    assert response.status_code == 201
    stored = RegistrationTokens.query.one()
    assert stored.token == hashlib.sha256(raw_token.encode()).hexdigest()
    assert raw_token not in stored.token
    verified = client.get(f"/api/v1/auth/verify-registration-token/{raw_token}")
    assert verified.status_code == 200


def test_password_reset_token_is_hashed_single_use(app, client):
    app.config["AUTH_BOOTSTRAP_SECRET"] = "test-bootstrap-secret"
    user = _user()
    raw_token = "reset-token-with-enough-entropy"
    initiated = client.post(
        "/api/v1/auth/request-password-reset",
        json={"email": user.email, "token": raw_token},
        headers=BOOTSTRAP_HEADERS,
    )
    assert initiated.status_code == 200
    stored = PasswordResets.query.one()
    assert stored.token == hashlib.sha256(raw_token.encode()).hexdigest()
    assert raw_token not in initiated.get_data(as_text=True)

    completed = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "password": "new-secure-password"},
    )
    assert completed.status_code == 200
    assert PasswordResets.query.count() == 0
    assert check_password_hash(db.session.get(UserAccount, user.user_id).password, "new-secure-password")
    assert client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "password": "another-password"},
    ).status_code == 400


def test_mutation_audit_records_failed_anonymous_write(app, client):
    app.config["MUTATION_AUDIT_ENABLED"] = True
    response = client.post(
        "/api/v1/cordoi/assign-doi/container-id",
        json={"title": "blocked", "description": "blocked"},
    )
    assert response.status_code == 401
    event = MutationAudit.query.one()
    assert event.method == "POST"
    assert event.response_status == 401
    assert event.outcome == "failed"
    assert event.user_id is None
    assert len(event.payload_sha256) == 64
