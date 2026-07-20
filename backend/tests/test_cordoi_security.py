"""Security regression tests for Cordra/PID namespace routes."""

import uuid
from unittest.mock import patch

import pytest
from flask_jwt_extended import create_access_token

from app import db, limiter
from app.models import PidMintAudit, UserAccount


CONTAINER_ENDPOINT = "/api/v1/cordoi/assign-doi/container-id"


@pytest.fixture(autouse=True)
def enable_test_minting(app):
    limiter.reset()
    previous = {
        "PID_MINTING_ENABLED": app.config.get("PID_MINTING_ENABLED"),
        "CORDRA_DEBUG_ROUTES_ENABLED": app.config.get("CORDRA_DEBUG_ROUTES_ENABLED"),
        "RATELIMIT_ENABLED": app.config.get("RATELIMIT_ENABLED"),
    }
    app.config.update(
        PID_MINTING_ENABLED=True,
        CORDRA_DEBUG_ROUTES_ENABLED=False,
        RATELIMIT_ENABLED=False,
    )
    yield
    limiter.reset()
    app.config.update(previous)


def _headers_for(app, role, *, idempotency_key=None):
    unique = uuid.uuid4().hex
    with app.app_context():
        user = UserAccount(
            user_name=f"user-{unique[:8]}",
            full_name=f"Test {role}",
            email=f"{unique}@example.test",
            type="email",
            role=role,
            password="not-used-in-route-tests",
        )
        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity=str(user.user_id))
        user_id = user.user_id

    headers = {"Authorization": f"Bearer {token}"}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return headers, user_id


def _container_payload():
    return {
        "title": "Secure Research Container",
        "description": "A container created by an authorized PID minter.",
    }


def test_anonymous_container_mint_is_rejected(client):
    with patch("app.routes.cordoi.assign_doi_container_id") as service:
        response = client.post(CONTAINER_ENDPOINT, json=_container_payload())

    assert response.status_code == 401
    service.assert_not_called()


def test_normal_user_cannot_mint_container(app, client):
    headers, _ = _headers_for(app, "user", idempotency_key="normal-user-attempt")

    with patch("app.routes.cordoi.assign_doi_container_id") as service:
        response = client.post(CONTAINER_ENDPOINT, json=_container_payload(), headers=headers)

    assert response.status_code == 403
    assert response.get_json()["error"] == "Insufficient permissions"
    service.assert_not_called()


def test_pid_minter_requires_idempotency_key(app, client):
    headers, _ = _headers_for(app, "pid_minter")

    with patch("app.routes.cordoi.assign_doi_container_id") as service:
        response = client.post(CONTAINER_ENDPOINT, json=_container_payload(), headers=headers)

    assert response.status_code == 400
    assert "Idempotency-Key" in response.get_json()["error"]
    service.assert_not_called()


def test_pid_minter_can_mint_and_creates_sanitized_audit(app, client):
    headers, user_id = _headers_for(
        app, "pid_minter", idempotency_key="container-success-0001"
    )

    with patch(
        "app.routes.cordoi.assign_doi_container_id",
        return_value={
            "success": True,
            "message": "Object created successfully",
            "id": "20.500.14351/secure-test",
        },
    ) as service:
        response = client.post(CONTAINER_ENDPOINT, json=_container_payload(), headers=headers)

    assert response.status_code == 200
    assert response.get_json()["id"] == "20.500.14351/secure-test"
    assert response.headers.get("X-Request-ID")
    service.assert_called_once_with(
        title="Secure Research Container",
        description="A container created by an authorized PID minter.",
    )

    with app.app_context():
        audit = PidMintAudit.query.filter_by(
            user_id=user_id,
            operation="assign_container_id",
            idempotency_key="container-success-0001",
        ).one()
        assert audit.status == "success"
        assert audit.identifier == "20.500.14351/secure-test"
        assert audit.payload_sha256 and len(audit.payload_sha256) == 64
        assert "Secure Research Container" not in (audit.response_body or "")


def test_same_idempotency_key_replays_without_second_mint(app, client):
    headers, _ = _headers_for(
        app, "pid_minter", idempotency_key="container-replay-0001"
    )

    with patch(
        "app.routes.cordoi.assign_doi_container_id",
        return_value={"success": True, "id": "20.500.14351/one-object"},
    ) as service:
        first = client.post(CONTAINER_ENDPOINT, json=_container_payload(), headers=headers)
        second = client.post(CONTAINER_ENDPOINT, json=_container_payload(), headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.get_json()["id"] == "20.500.14351/one-object"
    assert second.headers.get("X-Idempotent-Replay") == "true"
    service.assert_called_once()


def test_failed_mint_is_audited_without_upstream_details(app, client):
    headers, user_id = _headers_for(
        app, "pid_minter", idempotency_key="container-failure-0001"
    )
    with patch(
        "app.routes.cordoi.assign_doi_container_id",
        return_value={
            "success": False,
            "status_code": 500,
            "error": "Cordra at http://internal:8080 rejected secret-token",
        },
    ):
        response = client.post(CONTAINER_ENDPOINT, json=_container_payload(), headers=headers)

    assert response.status_code == 502
    assert "internal" not in response.get_data(as_text=True)
    with app.app_context():
        audit = PidMintAudit.query.filter_by(user_id=user_id).one()
        assert audit.status == "failed"
        assert "internal" not in (audit.response_body or "")


def test_pid_mint_rate_limit_returns_429(app, client):
    app.config.update(RATELIMIT_ENABLED=True, PID_MINT_RATE_LIMIT="1 per minute")
    headers, _ = _headers_for(app, "pid_minter", idempotency_key="rate-limit-one")
    with patch(
        "app.routes.cordoi.assign_doi_container_id",
        return_value={"success": True, "id": "20.500.14351/rate-one"},
    ):
        first = client.post(CONTAINER_ENDPOINT, json=_container_payload(), headers=headers)
        headers["Idempotency-Key"] = "rate-limit-two"
        second = client.post(CONTAINER_ENDPOINT, json=_container_payload(), headers=headers)

    assert first.status_code == 200
    assert second.status_code == 429


def test_minting_switch_fails_closed(app, client):
    app.config["PID_MINTING_ENABLED"] = False
    headers, _ = _headers_for(
        app, "pid_minter", idempotency_key="container-disabled-0001"
    )

    with patch("app.routes.cordoi.assign_doi_container_id") as service:
        response = client.post(CONTAINER_ENDPOINT, json=_container_payload(), headers=headers)

    assert response.status_code == 503
    assert response.get_json()["error_code"] == "PID_MINTING_DISABLED"
    service.assert_not_called()


def test_user_pid_endpoint_is_disabled_even_for_admin(app, client):
    headers, _ = _headers_for(app, "admin", idempotency_key="user-endpoint-disabled")
    response = client.post(
        "/api/v1/cordoi/assign-doi/user",
        json={
            "username": "attacker-controlled",
            "password": "must-not-be-forwarded",
            "email": "target@example.test",
            "role": "admin",
        },
        headers=headers,
    )

    assert response.status_code == 410
    assert response.get_json()["error_code"] == "USER_PID_ENDPOINT_DISABLED"
