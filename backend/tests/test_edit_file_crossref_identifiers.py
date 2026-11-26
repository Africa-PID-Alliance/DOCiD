"""Edit mode stores a Crossref file the same way the create flow does.

The public page labels a file from `identifier` (1 = APA Handle iD,
3 = CrossRef) and shows `generated_identifier`. Edit mode used to write
1 + the minted handle even when the user picked Crossref, so the DOI never
appeared publicly.
"""

import io

import pytest
from flask_jwt_extended import create_access_token

import backfill_file_crossref_identifiers as backfill
from app import db
from app.models import (
    PublicationFiles,
    Publications,
    PublicationTypes,
    ResourceTypes,
    UserAccount,
)
from app.service_identifiers import IdentifierService

DOI = "10.1234/soil.2026.001"
EXISTING_HANDLE = "20.500.14351/existinghandle"
MINTED_HANDLE = "20.500.14351/freshlyminted"


@pytest.fixture
def mint(monkeypatch):
    """Stub Cordra: record each mint and return MINTED_HANDLE (or None when failing)."""
    calls = []
    state = {"handle": MINTED_HANDLE}

    def fake_generate_handle():
        calls.append(1)
        return state["handle"]

    monkeypatch.setattr(IdentifierService, "generate_handle", staticmethod(fake_generate_handle))
    state["calls"] = calls
    return state


@pytest.fixture
def owner_and_publication(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # edit routes save uploads into ./uploads
    owner = UserAccount(
        user_name="crossref-owner",
        full_name="Crossref Owner",
        email="crossref-owner@example.test",
        type="email",
        role="user",
        password="unused",
    )
    resource_type = ResourceTypes(resource_type="dataset")
    publication_type = PublicationTypes(publication_type_name="article")
    db.session.add_all([owner, resource_type, publication_type])
    db.session.flush()
    publication = Publications(
        user_id=owner.user_id,
        document_docid="20.500.14351/crossrefparent",
        document_title="Crossref parent",
        document_description="fixture",
        resource_type_id=resource_type.id,
    )
    db.session.add(publication)
    db.session.commit()
    return owner.user_id, publication.id, publication_type.id


def _headers(user_id):
    return {"Authorization": f"Bearer {create_access_token(identity=str(user_id))}"}


def _add_file_row(publication_id, publication_type_id, **columns):
    row = PublicationFiles(
        publication_id=publication_id,
        title="Article PDF",
        description="",
        publication_type_id=publication_type_id,
        file_name="article.pdf",
        file_type="application/pdf",
        file_url="/uploads/article.pdf",
        **columns,
    )
    db.session.add(row)
    db.session.commit()
    return row.id


def _reload(file_id):
    row = db.session.get(PublicationFiles, file_id)
    db.session.refresh(row)
    return row


def _post_file(client, owner_id, publication_id, publication_type_id, **extra_form):
    # Every new publication file needs a licence and the rights declaration.
    from app.utils.licenses import ensure_license_catalogue
    ensure_license_catalogue()
    db.session.commit()
    return client.post(
        f"/api/v1/publications/{publication_id}/files",
        data={
            "title": "Article PDF",
            "publication_type_id": str(publication_type_id),
            "file": (io.BytesIO(b"%PDF-1.4 article"), "article.pdf", "application/pdf"),
            "license_id": "CC-BY-4.0",
            "rights_declaration": "true",
            **extra_form,
        },
        content_type="multipart/form-data",
        headers=_headers(owner_id),
    )


# --------------------------------------------------------------------- add


def test_adding_a_file_with_a_doi_saves_it_as_crossref(client, owner_and_publication, mint):
    owner_id, publication_id, type_id = owner_and_publication

    response = _post_file(
        client, owner_id, publication_id, type_id,
        external_identifier_type="DOI",
        external_identifier_value=f"https://doi.org/{DOI}",
    )

    assert response.status_code == 201, response.get_json()
    row = _reload(response.get_json()["id"])
    assert row.identifier == "3"
    assert row.generated_identifier == DOI
    assert row.external_identifier == DOI
    assert row.external_identifier_type == "DOI"
    # The Cordra child handle is still minted and kept alongside the DOI.
    assert row.handle_identifier == MINTED_HANDLE


def test_public_read_shows_crossref_and_the_doi(client, owner_and_publication, mint):
    owner_id, publication_id, type_id = owner_and_publication
    _post_file(
        client, owner_id, publication_id, type_id,
        external_identifier_type="DOI", external_identifier_value=DOI,
    )

    payload = client.get(f"/api/v1/publications/get-publication/{publication_id}").get_json()

    [public_file] = payload["publications_files"]
    assert public_file["identifier"] == "3"
    assert public_file["generated_identifier"] == DOI


def test_adding_a_file_without_a_doi_stays_apa_handle(client, owner_and_publication, mint):
    owner_id, publication_id, type_id = owner_and_publication

    response = _post_file(client, owner_id, publication_id, type_id)

    assert response.status_code == 201, response.get_json()
    row = _reload(response.get_json()["id"])
    assert row.identifier == "1"
    assert row.generated_identifier == MINTED_HANDLE
    assert row.external_identifier is None


# ------------------------------------------------------------------ update


def test_tagging_an_existing_file_with_a_doi_switches_it_to_crossref(client, owner_and_publication, mint):
    owner_id, publication_id, type_id = owner_and_publication
    file_id = _add_file_row(
        publication_id, type_id,
        identifier="1", generated_identifier=EXISTING_HANDLE, handle_identifier=EXISTING_HANDLE,
    )

    response = client.put(
        f"/api/v1/publications/{publication_id}/files/{file_id}",
        json={"external_identifier_type": "DOI", "external_identifier_value": DOI},
        headers=_headers(owner_id),
    )

    assert response.status_code == 200, response.get_json()
    row = _reload(file_id)
    assert (row.identifier, row.generated_identifier) == ("3", DOI)
    assert (row.external_identifier, row.external_identifier_type) == (DOI, "DOI")
    assert row.handle_identifier == EXISTING_HANDLE
    assert mint["calls"] == []


def test_clearing_the_doi_switches_back_to_the_files_own_handle(client, owner_and_publication, mint):
    owner_id, publication_id, type_id = owner_and_publication
    file_id = _add_file_row(
        publication_id, type_id,
        identifier="3", generated_identifier=DOI, handle_identifier=EXISTING_HANDLE,
        external_identifier=DOI, external_identifier_type="DOI",
    )

    response = client.put(
        f"/api/v1/publications/{publication_id}/files/{file_id}",
        json={"external_identifier_type": "", "external_identifier_value": ""},
        headers=_headers(owner_id),
    )

    assert response.status_code == 200, response.get_json()
    row = _reload(file_id)
    assert (row.identifier, row.generated_identifier) == ("1", EXISTING_HANDLE)
    assert row.external_identifier is None
    assert mint["calls"] == []


def test_clearing_the_doi_on_an_older_row_without_a_handle_mints_one(client, owner_and_publication, mint):
    owner_id, publication_id, type_id = owner_and_publication
    file_id = _add_file_row(
        publication_id, type_id,
        identifier="3", generated_identifier=DOI, handle_identifier=None,
    )

    response = client.put(
        f"/api/v1/publications/{publication_id}/files/{file_id}",
        json={"external_identifier_type": "", "external_identifier_value": ""},
        headers=_headers(owner_id),
    )

    assert response.status_code == 200, response.get_json()
    row = _reload(file_id)
    assert (row.identifier, row.generated_identifier) == ("1", MINTED_HANDLE)
    assert row.handle_identifier == MINTED_HANDLE
    assert len(mint["calls"]) == 1


def test_clearing_reuses_a_handle_kept_only_in_generated_identifier(client, owner_and_publication, mint):
    owner_id, publication_id, type_id = owner_and_publication
    file_id = _add_file_row(
        publication_id, type_id,
        identifier=EXISTING_HANDLE, generated_identifier=EXISTING_HANDLE, handle_identifier=None,
    )

    response = client.put(
        f"/api/v1/publications/{publication_id}/files/{file_id}",
        json={"external_identifier_type": "", "external_identifier_value": ""},
        headers=_headers(owner_id),
    )

    assert response.status_code == 200, response.get_json()
    row = _reload(file_id)
    assert (row.identifier, row.generated_identifier, row.handle_identifier) == ("1", EXISTING_HANDLE, EXISTING_HANDLE)
    assert mint["calls"] == []


def test_a_failed_mint_leaves_the_row_untouched(client, owner_and_publication, mint):
    owner_id, publication_id, type_id = owner_and_publication
    file_id = _add_file_row(
        publication_id, type_id,
        identifier="3", generated_identifier=DOI, handle_identifier=None,
    )
    mint["handle"] = None

    response = client.put(
        f"/api/v1/publications/{publication_id}/files/{file_id}",
        json={"title": "Renamed", "external_identifier_type": "", "external_identifier_value": ""},
        headers=_headers(owner_id),
    )

    assert response.status_code == 502
    row = _reload(file_id)
    assert (row.title, row.identifier, row.generated_identifier) == ("Article PDF", "3", DOI)


def test_a_title_only_edit_leaves_identifiers_alone(client, owner_and_publication, mint):
    owner_id, publication_id, type_id = owner_and_publication
    file_id = _add_file_row(
        publication_id, type_id,
        identifier="3", generated_identifier=DOI, handle_identifier=None,
    )

    response = client.put(
        f"/api/v1/publications/{publication_id}/files/{file_id}",
        json={"title": "Renamed"},
        headers=_headers(owner_id),
    )

    assert response.status_code == 200
    row = _reload(file_id)
    assert (row.title, row.identifier, row.generated_identifier) == ("Renamed", "3", DOI)
    assert mint["calls"] == []


def test_an_existing_file_cannot_be_saved_with_a_blank_title(client, owner_and_publication, mint):
    owner_id, publication_id, type_id = owner_and_publication
    file_id = _add_file_row(
        publication_id, type_id,
        identifier="1", generated_identifier=EXISTING_HANDLE, handle_identifier=EXISTING_HANDLE,
    )

    response = client.put(
        f"/api/v1/publications/{publication_id}/files/{file_id}",
        json={"title": "  ", "external_identifier_type": "DOI", "external_identifier_value": DOI},
        headers=_headers(owner_id),
    )

    assert response.status_code == 400
    row = _reload(file_id)
    assert (row.title, row.identifier) == ("Article PDF", "1")


# ---------------------------------------------------------------- backfill


def test_backfill_repairs_both_inconsistent_shapes_and_is_idempotent(owner_and_publication):
    _, publication_id, type_id = owner_and_publication
    saved_by_old_edit_mode = _add_file_row(
        publication_id, type_id,
        identifier="1", generated_identifier=EXISTING_HANDLE, handle_identifier=EXISTING_HANDLE,
        external_identifier=DOI, external_identifier_type="DOI",
    )
    older_crossref = _add_file_row(
        publication_id, type_id,
        identifier="3", generated_identifier=f"https://doi.org/{DOI}", handle_identifier=None,
    )
    already_correct = _add_file_row(
        publication_id, type_id,
        identifier="3", generated_identifier=DOI, handle_identifier=EXISTING_HANDLE,
        external_identifier=DOI, external_identifier_type="DOI",
    )
    type_3_without_a_doi = _add_file_row(
        publication_id, type_id,
        identifier="3", generated_identifier="not-a-doi", handle_identifier=None,
    )
    plain_handle = _add_file_row(
        publication_id, type_id,
        identifier="1", generated_identifier=EXISTING_HANDLE, handle_identifier=EXISTING_HANDLE,
    )

    assert backfill.run(apply=False) == 2
    assert _reload(saved_by_old_edit_mode).identifier == "1"  # dry run writes nothing

    assert backfill.run(apply=True) == 2

    row = _reload(saved_by_old_edit_mode)
    assert (row.identifier, row.generated_identifier, row.handle_identifier) == ("3", DOI, EXISTING_HANDLE)
    row = _reload(older_crossref)
    assert (row.external_identifier, row.external_identifier_type, row.generated_identifier) == (DOI, "DOI", DOI)
    assert _reload(already_correct).identifier == "3"
    assert _reload(type_3_without_a_doi).external_identifier is None
    assert _reload(plain_handle).generated_identifier == EXISTING_HANDLE

    assert backfill.run(apply=True) == 0


def test_backfill_leaves_datacite_files_and_unsaved_handles_alone(owner_and_publication):
    _, publication_id, type_id = owner_and_publication
    datacite_doi = "10.5555/datacite.0001"
    # The create flow stores a DataCite file with its DOI in external_identifier too.
    datacite = _add_file_row(
        publication_id, type_id,
        identifier="2", generated_identifier=datacite_doi, handle_identifier=EXISTING_HANDLE,
        external_identifier=datacite_doi, external_identifier_type="DOI",
    )
    # Overwriting generated_identifier here would lose the only copy of the handle.
    handle_not_saved = _add_file_row(
        publication_id, type_id,
        identifier="1", generated_identifier=EXISTING_HANDLE, handle_identifier=None,
        external_identifier=DOI, external_identifier_type="DOI",
    )
    shows_a_different_handle = _add_file_row(
        publication_id, type_id,
        identifier="1", generated_identifier="20.500.14351/anotherhandle", handle_identifier=EXISTING_HANDLE,
        external_identifier=DOI, external_identifier_type="DOI",
    )

    assert backfill.run(apply=True) == 0

    row = _reload(datacite)
    assert (row.identifier, row.generated_identifier) == ("2", datacite_doi)
    row = _reload(handle_not_saved)
    assert (row.identifier, row.generated_identifier) == ("1", EXISTING_HANDLE)
    row = _reload(shows_a_different_handle)
    assert (row.identifier, row.generated_identifier) == ("1", "20.500.14351/anotherhandle")
