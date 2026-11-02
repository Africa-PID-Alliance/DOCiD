"""Replacing a file in edit mode keeps the row's title and identifiers."""

import hashlib
import io
from datetime import datetime, timedelta

import pytest
from flask_jwt_extended import create_access_token

from app import db
from app.models import (
    PublicationAuditTrail,
    PublicationFiles,
    Publications,
    PublicationTypes,
    ResourceTypes,
    UserAccount,
)

ORIGINAL_TITLE = "Soil carbon in Kenyan drylands"
CROSSREF_DOI = "10.1234/soil.2026.001"
HANDLE = "20.500.14351/replacetest"
NEW_BYTES = b"%PDF-1.4 the corrected manuscript"


def _make_user(name):
    user = UserAccount(
        user_name=name,
        full_name=name,
        email=f"{name}@example.test",
        type="email",
        role="user",
        password="unused",
    )
    db.session.add(user)
    db.session.flush()
    return user


def _headers(user_id):
    return {"Authorization": f"Bearer {create_access_token(identity=str(user_id))}"}


@pytest.fixture
def uploads_dir(tmp_path, monkeypatch):
    # The edit routes save into a relative "uploads/" directory.
    monkeypatch.chdir(tmp_path)
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    return uploads


@pytest.fixture
def seeded_file(uploads_dir):
    owner = _make_user("replace-owner")
    resource_type = ResourceTypes(resource_type="dataset")
    publication_type = PublicationTypes(publication_type_name="article")
    db.session.add_all([resource_type, publication_type])
    db.session.flush()
    publication = Publications(
        user_id=owner.user_id,
        document_docid="20.500.14351/replaceparent",
        document_title=ORIGINAL_TITLE,
        document_description="fixture",
        resource_type_id=resource_type.id,
        updated_at=datetime.utcnow() - timedelta(days=30),
    )
    db.session.add(publication)
    db.session.flush()

    old_name = "aaaaaaaaaaaa_draft.pdf"
    (uploads_dir / old_name).write_bytes(b"old draft")
    pub_file = PublicationFiles(
        publication_id=publication.id,
        title=ORIGINAL_TITLE,
        description="<p>Accepted manuscript</p>",
        publication_type_id=publication_type.id,
        file_name=old_name,
        file_type="application/pdf",
        file_url=f"/uploads/{old_name}",
        identifier="3",
        generated_identifier=CROSSREF_DOI,
        handle_identifier=HANDLE,
        external_identifier=CROSSREF_DOI,
        external_identifier_type="DOI",
    )
    db.session.add(pub_file)
    db.session.commit()
    return owner.user_id, publication.id, pub_file.id, old_name


def _replace(client, user_id, publication_id, file_id, filename, data=NEW_BYTES):
    return client.post(
        f"/api/v1/publications/{publication_id}/files/{file_id}/replace",
        data={"file": (io.BytesIO(data), filename, "application/pdf")},
        content_type="multipart/form-data",
        headers=_headers(user_id),
    )


def test_replace_swaps_the_file_and_keeps_title_and_identifiers(client, uploads_dir, seeded_file):
    owner_id, publication_id, file_id, old_name = seeded_file

    response = _replace(client, owner_id, publication_id, file_id, "final.pdf")

    assert response.status_code == 200, response.get_json()
    row = db.session.get(PublicationFiles, file_id)
    db.session.refresh(row)
    # Everything that identifies the record is untouched.
    assert row.title == ORIGINAL_TITLE
    assert row.description == "<p>Accepted manuscript</p>"
    assert row.identifier == "3"
    assert row.generated_identifier == CROSSREF_DOI
    assert row.handle_identifier == HANDLE
    assert row.external_identifier == CROSSREF_DOI
    assert row.external_identifier_type == "DOI"
    # Only the stored file changed.
    assert row.file_name.endswith("_final.pdf")
    assert row.file_url.endswith(f"/uploads/{row.file_name}")
    assert row.checksum == hashlib.sha256(NEW_BYTES).hexdigest()
    assert (uploads_dir / row.file_name).read_bytes() == NEW_BYTES
    assert not (uploads_dir / old_name).exists()


def test_replace_brings_the_record_into_the_next_cordra_sync(client, seeded_file):
    owner_id, publication_id, file_id, _ = seeded_file

    _replace(client, owner_id, publication_id, file_id, "final.pdf")

    publication = db.session.get(Publications, publication_id)
    db.session.refresh(publication)
    assert publication.updated_at > datetime.utcnow() - timedelta(minutes=5)
    assert PublicationAuditTrail.query.filter_by(
        publication_id=publication_id, action="REPLACE_FILE"
    ).count() == 1


def test_replace_is_owner_only(client, uploads_dir, seeded_file):
    _, publication_id, file_id, old_name = seeded_file
    stranger = _make_user("replace-stranger")
    db.session.commit()

    response = _replace(client, stranger.user_id, publication_id, file_id, "final.pdf")

    assert response.status_code == 403
    row = db.session.get(PublicationFiles, file_id)
    assert row.file_name == old_name
    assert (uploads_dir / old_name).exists()


def test_replace_rejects_blocked_file_types_without_touching_the_row(client, uploads_dir, seeded_file):
    owner_id, publication_id, file_id, old_name = seeded_file

    response = _replace(client, owner_id, publication_id, file_id, "payload.sh")

    assert response.status_code == 400
    row = db.session.get(PublicationFiles, file_id)
    assert row.file_name == old_name
    assert sorted(p.name for p in uploads_dir.iterdir()) == [old_name]


def test_replace_404s_for_a_file_on_another_publication(client, seeded_file):
    owner_id, publication_id, file_id, _ = seeded_file

    response = _replace(client, owner_id, publication_id + 999, file_id, "final.pdf")

    assert response.status_code == 404
