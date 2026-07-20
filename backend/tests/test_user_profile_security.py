"""Authorization regressions for account mutation routes."""

from flask_jwt_extended import create_access_token

from app import db
from app.models import UserAccount


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
        return user.user_id, create_access_token(identity=str(user.user_id))


def test_user_cannot_update_another_profile(app, client):
    attacker_id, token = _make_user(app, "profile-attacker")
    victim_id, _ = _make_user(app, "profile-victim")
    assert attacker_id != victim_id

    response = client.patch(
        f"/api/v1/user-profile/{victim_id}",
        json={"full_name": "Taken Over"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_user_cannot_promote_own_role(app, client):
    user_id, token = _make_user(app, "profile-normal")
    response = client.patch(
        f"/api/v1/user-profile/{user_id}",
        json={"full_name": "Still Normal", "role": "admin"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    with app.app_context():
        user = db.session.get(UserAccount, user_id)
        assert user.role == "user"
        assert user.full_name == "Still Normal"
