"""Tests for checksum generation, resolution, and the public verify endpoint.

Covers the codex-flagged edge cases: known-vector hashing, path-traversal guard,
external URLs, slash-containing DOCiDs, and public/deleted access scoping.
"""
import hashlib
import os

import pytest

from app.models import (
    Publications, PublicationFiles, PublicationDocuments,
    UserAccount, ResourceTypes, PublicationTypes,
)
from app.utils_checksum import (
    compute_file_checksum,
    local_path_for_url,
    checksum_for_stored_file,
    checksum_fields_for_upload,
    external_checksum_fields,
    STATUS_VERIFIED,
    STATUS_EXTERNAL,
    STATUS_MISSING,
)


# --------------------------------------------------------------------------- #
# Pure helper tests (no DB / app context needed)
# --------------------------------------------------------------------------- #

def test_compute_file_checksum_known_vector(tmp_path):
    target = tmp_path / "hello.txt"
    target.write_bytes(b"hello world")
    digest, size = compute_file_checksum(str(target))
    assert digest == hashlib.sha256(b"hello world").hexdigest()
    assert size == 11


def test_local_path_for_url_external_returns_none():
    assert local_path_for_url("https://youtube.com/watch?v=abc") is None
    assert local_path_for_url("") is None
    assert local_path_for_url(None) is None


def test_local_path_for_url_rejects_traversal():
    assert local_path_for_url("https://x/uploads/../../etc/passwd") is None


def test_local_path_for_url_resolves_relative_uploads(monkeypatch, tmp_path):
    from app import utils_checksum
    monkeypatch.setattr(utils_checksum.Config, "UPLOADS_DIRECTORY", str(tmp_path))
    # Relative URL (no host) is always treated as local.
    resolved = local_path_for_url("/uploads/abc_report.pdf")
    assert resolved == os.path.join(str(tmp_path), "abc_report.pdf")


def test_local_path_for_url_matching_host(monkeypatch, tmp_path):
    from app import utils_checksum
    monkeypatch.setattr(utils_checksum.Config, "UPLOADS_DIRECTORY", str(tmp_path))
    monkeypatch.setattr(utils_checksum.Config, "UPLOADS_BASE_URL", "https://docid.example")
    resolved = local_path_for_url("https://docid.example/uploads/abc_report.pdf")
    assert resolved == os.path.join(str(tmp_path), "abc_report.pdf")


def test_local_path_for_url_foreign_host_is_external(monkeypatch, tmp_path):
    from app import utils_checksum
    monkeypatch.setattr(utils_checksum.Config, "UPLOADS_DIRECTORY", str(tmp_path))
    monkeypatch.setattr(utils_checksum.Config, "UPLOADS_BASE_URL", "https://docid.example")
    monkeypatch.setattr(utils_checksum.Config, "APPLICATION_BASE_URL", "https://docid.example")
    # Another site's /uploads/ must NOT resolve to our local directory.
    assert local_path_for_url("https://other.example/uploads/file.pdf") is None


def test_checksum_for_stored_file_external():
    result = checksum_for_stored_file("https://vimeo.com/123")
    assert result["checksum_status"] == STATUS_EXTERNAL
    assert result["checksum"] is None


def test_checksum_for_stored_file_missing(monkeypatch, tmp_path):
    from app import utils_checksum
    monkeypatch.setattr(utils_checksum.Config, "UPLOADS_DIRECTORY", str(tmp_path))
    # Relative URL → local; file doesn't exist → missing (not external).
    result = checksum_for_stored_file("/uploads/nope.pdf")
    assert result["checksum_status"] == STATUS_MISSING


def test_checksum_fields_for_upload_verified(tmp_path):
    target = tmp_path / "data.csv"
    target.write_bytes(b"a,b,c\n1,2,3\n")
    fields = checksum_fields_for_upload(str(target))
    assert fields["checksum_status"] == STATUS_VERIFIED
    assert fields["checksum"] == hashlib.sha256(b"a,b,c\n1,2,3\n").hexdigest()
    assert fields["file_size"] == 12
    assert fields["checksum_generated_at"] is not None


def test_external_checksum_fields():
    fields = external_checksum_fields()
    assert fields["checksum_status"] == STATUS_EXTERNAL
    assert fields["checksum"] is None
    assert fields["checksum_generated_at"] is None


# --------------------------------------------------------------------------- #
# Verify-endpoint integration tests
# --------------------------------------------------------------------------- #

DOCID_WITH_SLASH = "20.500.14351/abc123def456"


def _checksum_columns_present():
    """The integration tests need the checksum migration applied to the DB."""
    from sqlalchemy import inspect as sa_inspect
    from app import db
    columns = {c["name"] for c in sa_inspect(db.engine).get_columns("publications_files")}
    return "checksum" in columns


def _seed_user_and_resource_type(session):
    """Reuse existing seed rows if present, else create minimal ones. Works both
    against a populated DB and a fresh create_all() schema (local test DB)."""
    user = UserAccount.query.first()
    if not user:
        user = UserAccount(
            user_name="checksum_tester",
            full_name="Checksum Tester",
            email="checksum-tester@example.com",
            type="local",
        )
        session.add(user)
        session.flush()
    resource_type = ResourceTypes.query.first()
    if not resource_type:
        resource_type = ResourceTypes(resource_type="dataset")
        session.add(resource_type)
        session.flush()
    publication_type = PublicationTypes.query.first()
    if not publication_type:
        publication_type = PublicationTypes(publication_type_name="dataset")
        session.add(publication_type)
        session.flush()
    return user, resource_type, publication_type


@pytest.fixture
def sample_publication(database_session):
    if not _checksum_columns_present():
        pytest.skip("checksum migration not applied to this database yet")

    existing_user, existing_resource_type, existing_publication_type = \
        _seed_user_and_resource_type(database_session)

    pub = Publications(
        user_id=existing_user.user_id,
        document_docid=DOCID_WITH_SLASH,
        document_title="Checksum Test Publication",
        document_description="fixture",
        resource_type_id=existing_resource_type.id,
    )
    database_session.add(pub)
    database_session.flush()

    database_session.add(PublicationFiles(
        publication_id=pub.id,
        title="dataset.csv",
        description="a dataset",
        publication_type_id=existing_publication_type.id,
        file_name="dataset.csv",
        file_type="text/csv",
        file_url="https://docid.example/uploads/dataset.csv",
        identifier="1",
        generated_identifier="20.500.14351/file1",
        checksum="a" * 64,
        checksum_algorithm="SHA-256",
        file_size=1234,
        checksum_status=STATUS_VERIFIED,
    ))
    database_session.add(PublicationDocuments(
        publication_id=pub.id,
        title="external video",
        description="a video",
        publication_type_id=existing_publication_type.id,
        file_url="https://youtube.com/watch?v=x",
        checksum_status=STATUS_EXTERNAL,
    ))
    database_session.flush()
    return pub


def test_verify_requires_identifier(client):
    resp = client.get("/api/v1/verify")
    assert resp.status_code == 400


def test_verify_unknown_docid(client):
    if not _checksum_columns_present():
        pytest.skip("checksum migration not applied to this database yet")
    resp = client.get("/api/v1/verify", query_string={"identifier": "20.500.9999/none"})
    assert resp.status_code == 404


def test_verify_returns_checksums_query_param(client, sample_publication):
    resp = client.get("/api/v1/verify", query_string={"identifier": DOCID_WITH_SLASH})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["docid"] == DOCID_WITH_SLASH
    assert body["object_count"] == 2
    assert body["verifiable_object_count"] == 1
    statuses = {o["checksum_status"] for o in body["objects"]}
    assert STATUS_VERIFIED in statuses
    assert STATUS_EXTERNAL in statuses


def test_verify_slash_in_path_route(client, sample_publication):
    resp = client.get(f"/api/v1/verify/{DOCID_WITH_SLASH}")
    assert resp.status_code == 200
    assert resp.get_json()["docid"] == DOCID_WITH_SLASH


def test_verify_deleted_publication_is_scoped_out(client, database_session, sample_publication):
    from datetime import datetime
    sample_publication.deleted_at = datetime.utcnow()
    database_session.flush()
    resp = client.get("/api/v1/verify", query_string={"identifier": DOCID_WITH_SLASH})
    assert resp.status_code == 410
