"""Retiring a publication from My Account (DELETE /api/v1/publications/<id>)."""

from flask_jwt_extended import create_access_token

from app import db
from app.models import Publications, PublicationAuditTrail, ResourceTypes, UserAccount


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
    return user.user_id, create_access_token(identity=str(user.user_id))


def _make_publication(owner_id, docid):
    resource_type = ResourceTypes.query.first()
    if resource_type is None:
        resource_type = ResourceTypes(resource_type="dataset")
        db.session.add(resource_type)
        db.session.flush()
    publication = Publications(
        user_id=owner_id,
        document_docid=docid,
        document_title=f"Title for {docid}",
        document_description="fixture",
        resource_type_id=resource_type.id,
    )
    db.session.add(publication)
    db.session.commit()
    return publication.id


def test_owner_retires_publication_and_my_account_labels_it(client):
    owner_id, token = _make_user("retire-owner")
    retired_id = _make_publication(owner_id, "20.500.14351/retiretest0000000001")
    active_id = _make_publication(owner_id, "20.500.14351/retiretest0000000002")
    auth_headers = {"Authorization": f"Bearer {token}"}

    response = client.delete(f"/api/v1/publications/{retired_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["deleted_at"]

    retired = db.session.get(Publications, retired_id)
    assert retired.deleted_at is not None
    assert retired.deleted_by == owner_id
    assert PublicationAuditTrail.query.filter_by(publication_id=retired_id, action="SOFT_DELETE").count() == 1

    # My Account keeps the retired record, flagged with deleted_at
    listing = client.get(f"/api/v1/user-profile/{owner_id}/publications", headers=auth_headers).get_json()
    deleted_at_by_id = {pub["id"]: pub["deleted_at"] for pub in listing["publications"]}
    assert deleted_at_by_id[retired_id] is not None
    assert deleted_at_by_id[active_id] is None

    # Statistics count only active publications
    statistics = client.get(f"/api/v1/user-profile/{owner_id}/statistics", headers=auth_headers).get_json()
    assert statistics["total_publications"] == 1


def test_non_owner_cannot_retire_publication(client):
    owner_id, _ = _make_user("retire-victim")
    _, attacker_token = _make_user("retire-attacker")
    publication_id = _make_publication(owner_id, "20.500.14351/retiretest0000000003")

    response = client.delete(
        f"/api/v1/publications/{publication_id}",
        headers={"Authorization": f"Bearer {attacker_token}"},
    )
    assert response.status_code == 403
    assert db.session.get(Publications, publication_id).deleted_at is None
