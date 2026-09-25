"""Authorization regressions for account and draft reads on /api/v1."""

import pytest
from flask_jwt_extended import create_access_token

from app import db
from app.models import NationalIdResearcher, UserAccount

BOOTSTRAP_SECRET = "test-bootstrap-secret"

ANONYMOUS_BLOCKED_PATHS = (
    "/api/v1/auth/user/1",
    "/api/v1/auth/user/id/1",
    "/api/v1/auth/user/username/alice",
    "/api/v1/publications/draft/alice@example.test",
    "/api/v1/publications/draft/alice@example.test/1",
    "/api/v1/publications/draft/by-user/1",
    "/api/v1/publications/my-docids/1",
    "/api/v1/user-profile/1",
    "/api/v1/user-profile/1/publications",
    "/api/v1/user-profile/1/statistics",
    "/api/v1/national-id/researchers/1",
    "/api/v1/national-id/researchers/lookup/123456",
    "/api/v1/national-id/researchers/search?q=ali",
    "/api/v1/localcontexts/audit-log",
)


@pytest.fixture
def bootstrap_secret(app):
    previous = app.config.get("AUTH_BOOTSTRAP_SECRET", "")
    app.config["AUTH_BOOTSTRAP_SECRET"] = BOOTSTRAP_SECRET
    yield BOOTSTRAP_SECRET
    app.config["AUTH_BOOTSTRAP_SECRET"] = previous


def _make_user(app, name, role="user"):
    with app.app_context():
        user = UserAccount(
            user_name=name,
            full_name=name.title(),
            email=f"{name}@example.test",
            type="email",
            role=role,
            password="unused",
        )
        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity=str(user.user_id))
        return user.user_id, {"Authorization": f"Bearer {token}"}


def test_user_data_reads_reject_anonymous_requests(client):
    for path in ANONYMOUS_BLOCKED_PATHS:
        response = client.get(path)
        assert response.status_code == 401, f"{path} -> {response.status_code}"


def test_draft_reads_are_owner_or_admin_only(app, client):
    owner_id, owner_headers = _make_user(app, "draft-owner")
    other_id, other_headers = _make_user(app, "draft-other")
    _, admin_headers = _make_user(app, "draft-admin", role="admin")
    assert owner_id != other_id

    owner_email = "draft-owner@example.test"
    path = f"/api/v1/publications/draft/{owner_email}"

    assert client.get(path, headers=owner_headers).status_code == 200
    assert client.get(path, headers=other_headers).status_code == 403
    assert client.get(path, headers=admin_headers).status_code == 200

    assert client.get(f"{path}/1", headers=owner_headers).status_code == 200
    assert client.get(f"{path}/1", headers=other_headers).status_code == 403


def test_user_id_scoped_reads_are_owner_or_admin_only(app, client):
    owner_id, owner_headers = _make_user(app, "reader-owner")
    other_id, other_headers = _make_user(app, "reader-other")
    admin_id, admin_headers = _make_user(app, "reader-admin", role="admin")

    paths = (
        f"/api/v1/publications/draft/by-user/{owner_id}",
        f"/api/v1/publications/my-docids/{owner_id}",
        f"/api/v1/user-profile/{owner_id}",
        f"/api/v1/user-profile/{owner_id}/publications",
        f"/api/v1/user-profile/{owner_id}/statistics",
        f"/api/v1/auth/user/{owner_id}",
        f"/api/v1/auth/user/id/{owner_id}",
    )

    for path in paths:
        assert client.get(path, headers=owner_headers).status_code == 200, path
        assert client.get(path, headers=other_headers).status_code == 403, path
        assert client.get(path, headers=admin_headers).status_code == 200, path


def test_username_lookup_is_owner_or_admin_only(app, client):
    owner_id, owner_headers = _make_user(app, "name-owner")
    _, other_headers = _make_user(app, "name-other")

    path = "/api/v1/auth/user/username/name-owner"
    assert client.get(path, headers=owner_headers).status_code == 200
    assert client.get(path, headers=other_headers).status_code == 403
    assert client.get(path).status_code == 401


def test_identity_lookup_routes_require_the_service_secret(app, client, bootstrap_secret):
    _make_user(app, "lookup-user")

    email_path = "/api/v1/auth/user/email/lookup-user@example.test"
    social_path = "/api/v1/auth/user/social/lookup-social"

    assert client.get(email_path).status_code == 403
    assert client.get(social_path).status_code == 403
    assert (
        client.get(email_path, headers={"X-Auth-Bootstrap-Secret": "wrong"})
        .status_code
        == 403
    )

    trusted = {"X-Auth-Bootstrap-Secret": bootstrap_secret}
    email_response = client.get(email_path, headers=trusted)
    assert email_response.status_code == 200
    assert email_response.get_json()["email"] == "lookup-user@example.test"
    assert "date_joined" not in email_response.get_json()

    assert client.get(social_path, headers=trusted).status_code == 404


def test_identity_lookup_routes_reject_untrusted_service_calls(app, client):
    previous = app.config.get("AUTH_BOOTSTRAP_SECRET", "")
    app.config["AUTH_BOOTSTRAP_SECRET"] = ""
    try:
        response = client.get(
            "/api/v1/auth/user/email/anyone@example.test",
            headers={"X-Auth-Bootstrap-Secret": ""},
        )
        assert response.status_code == 403
    finally:
        app.config["AUTH_BOOTSTRAP_SECRET"] = previous


def test_audit_log_requires_an_admin_account(app, client):
    _, user_headers = _make_user(app, "audit-user")
    _, admin_headers = _make_user(app, "audit-admin", role="admin")

    path = "/api/v1/localcontexts/audit-log"
    assert client.get(path, headers=user_headers).status_code == 403
    assert client.get(path, headers=admin_headers).status_code == 200


def test_national_id_reads_require_an_authenticated_account(app, client):
    _, user_headers = _make_user(app, "nid-user")
    _, admin_headers = _make_user(app, "nid-admin", role="admin")

    with app.app_context():
        db.session.add(NationalIdResearcher(
            name="Sensitive Researcher",
            national_id_number="987654321",
            country="Kenya",
        ))
        db.session.commit()

    assert (
        client.get("/api/v1/national-id/researchers/lookup/123456", headers=user_headers)
        .status_code
        == 200
    )
    assert (
        client.get(
            "/api/v1/national-id/researchers/search?q=ali", headers=user_headers
        ).status_code
        == 200
    )
    assert client.get(
        "/api/v1/national-id/researchers/search", headers=user_headers
    ).status_code == 400
    assert client.get(
        "/api/v1/national-id/researchers/search?q=%25", headers=user_headers
    ).status_code == 400
    id_search = client.get(
        "/api/v1/national-id/researchers/search?q=987654", headers=user_headers
    )
    assert id_search.status_code == 200
    assert id_search.get_json()["total"] == 0
    assert client.get(
        "/api/v1/national-id/researchers/1", headers=user_headers
    ).status_code == 403
    admin_response = client.get(
        "/api/v1/national-id/researchers/1", headers=admin_headers
    )
    assert admin_response.status_code == 200
    assert admin_response.get_json()["national_id_number"] == "987654321"


def test_login_returns_social_identity_without_public_lookup(app, client):
    from werkzeug.security import generate_password_hash

    with app.app_context():
        user = UserAccount(
            user_name="credential-user",
            full_name="Credential User",
            email="credential@example.test",
            type="email",
            role="user",
            password=generate_password_hash("correct horse battery staple"),
            social_id="linked-social-id",
        )
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "credential@example.test",
            "password": "correct horse battery staple",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["social_id"] == "linked-social-id"
