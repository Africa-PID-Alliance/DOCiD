"""Malformed or wrongly signed JWTs are rejected with 401 (not flask_jwt_extended's default 422)."""

import time

import jwt as pyjwt
from flask_jwt_extended import create_access_token

from app import db
from app.models import UserAccount


def _make_user(name):
    user = UserAccount(
        user_name=name,
        full_name=name.title(),
        email=f"{name}@example.test",
        type="email",
        role="user",
        password="unused",
    )
    db.session.add(user)
    db.session.commit()
    return user.user_id


def _statistics(client, user_id, token):
    return client.get(
        f"/api/v1/user-profile/{user_id}/statistics",
        headers={"Authorization": f"Bearer {token}"},
    )


def test_valid_token_is_accepted(client):
    user_id = _make_user("jwt-valid")
    assert _statistics(client, user_id, create_access_token(identity=str(user_id))).status_code == 200


def test_malformed_token_is_rejected_with_401(client):
    user_id = _make_user("jwt-malformed")
    assert _statistics(client, user_id, "not-a-valid-token").status_code == 401


def test_token_signed_with_another_secret_is_rejected_with_401(client):
    user_id = _make_user("jwt-foreign")
    now = int(time.time())
    foreign_token = pyjwt.encode(
        {"sub": str(user_id), "type": "access", "fresh": False, "jti": "foreign-jti",
         "iat": now, "nbf": now, "exp": now + 600},
        "some-other-secret",
        algorithm="HS256",
    )
    assert _statistics(client, user_id, foreign_token).status_code == 401
