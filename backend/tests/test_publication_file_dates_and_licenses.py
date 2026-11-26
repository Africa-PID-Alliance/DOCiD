"""
A publication file's own publication date and licence.

Only publication files (works uploaded in the assign form) carry them. A DOCiD's
own date is when it was created (created_at); DOCiDs and publication documents
have no publication date or licence.
"""

import json
from datetime import date, datetime, timedelta
from unittest.mock import patch

import pytest
from flask_jwt_extended import create_access_token

from app import db
from app.models import (
    Licenses, PublicationAuditTrail, PublicationDocuments, PublicationFiles, Publications,
    PublicationTypes, ResourceTypes, UserAccount,
)
from app.utils.licenses import ensure_license_catalogue, match_license, normalise_license_url
from app.utils.publication_dates import format_publication_date, parse_publication_date_input


@pytest.fixture(autouse=True)
def licence_catalogue(database_session):
    ensure_license_catalogue()
    db.session.commit()


def _licence(code):
    return Licenses.query.filter_by(code=code).one()


def _make_user(name):
    user = UserAccount(user_name=name, full_name=name.title(), email=f"{name}@example.test",
                       type="email", role="user", password="unused")
    db.session.add(user)
    db.session.commit()
    return user.user_id, {"Authorization": f"Bearer {create_access_token(identity=str(user.user_id))}"}


def _reference_ids():
    resource_type = ResourceTypes.query.first() or ResourceTypes(resource_type="Article")
    publication_type = PublicationTypes.query.first() or PublicationTypes(publication_type_name="Article")
    db.session.add_all([resource_type, publication_type])
    db.session.commit()
    return resource_type.id, publication_type.id


def _publish_form(docid, files=(), documents=0, declared=True):
    """A /publish form. files are dicts of extra per-file fields; items are video links."""
    resource_type_id, publication_type_id = _reference_ids()
    form = {
        "documentDocid": docid,
        "documentTitle": "Indigenous knowledge systems",
        "documentDescription": "A study",
        "resourceType": str(resource_type_id),
    }
    if declared:
        form["rightsDeclaration"] = "true"
    for index, extra in enumerate(files):
        form.update({
            f"filesPublications[{index}][title]": f"Publication {index + 1}",
            f"filesPublications[{index}][description]": "work",
            f"filesPublications[{index}][publication_type]": str(publication_type_id),
            f"filesPublications[{index}][video_url]": f"https://video.example/file/{index}",
        })
        form.update({f"filesPublications[{index}][{key}]": value for key, value in extra.items()})
    for index in range(documents):
        form.update({
            f"filesDocuments[{index}][title]": f"Dataset {index + 1}",
            f"filesDocuments[{index}][description]": "data",
            f"filesDocuments[{index}][publication_type]": str(publication_type_id),
            f"filesDocuments[{index}][video_url]": f"https://video.example/doc/{index}",
        })
    return form


def _make_publication(owner_id, docid):
    resource_type_id, _ = _reference_ids()
    publication = Publications(user_id=owner_id, document_docid=docid, document_title=docid,
                               document_description="fixture", resource_type_id=resource_type_id,
                               published=datetime(2026, 11, 20, 8, 30))
    db.session.add(publication)
    db.session.commit()
    return publication


def _add_file(publication, licence=None, **fields):
    _, publication_type_id = _reference_ids()
    publication_file = PublicationFiles(
        publication_id=publication.id, title="Article", description="d", publication_type_id=publication_type_id,
        file_name="a.pdf", file_type="application/pdf", file_url="/uploads/a.pdf", identifier="1",
        generated_identifier="20.500.14351/file1", license=licence, **fields)
    db.session.add(publication_file)
    db.session.commit()
    return publication_file


def _declarations(publication_id):
    rows = PublicationAuditTrail.query.filter_by(publication_id=publication_id, action="RIGHTS_DECLARED").all()
    return [json.loads(row.new_value) for row in rows]


# --- Dates: parsing and formatting -------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ("2019", (date(2019, 1, 1), "year")),
    ("2019-05", (date(2019, 5, 1), "month")),
    ("2019-05-14", (date(2019, 5, 14), "day")),
    (" 2019-05-14 ", (date(2019, 5, 14), "day")),
    ("", (None, None)),
    ("undefined", (None, None)),
    (None, (None, None)),
])
def test_dates_accept_year_month_or_day(raw, expected):
    assert parse_publication_date_input(raw) == expected


@pytest.mark.parametrize("raw", [
    "19", "2019-5", "2019/05/14", "14-05-2019", "2019-13", "2019-02-30",
    "2019-05-14T10:00:00Z", "May 2019", str(date.today().year + 1),
    (date.today() + timedelta(days=1)).isoformat(),
])
def test_dates_reject_other_shapes_and_the_future(raw):
    with pytest.raises(ValueError, match="publication_date must be"):
        parse_publication_date_input(raw)


def test_dates_are_serialised_at_their_precision():
    assert format_publication_date(date(2019, 1, 1), "year") == "2019"
    assert format_publication_date(date(2019, 5, 1), "month") == "2019-05"
    assert format_publication_date(date(2019, 5, 14), "day") == "2019-05-14"
    assert format_publication_date(None, None) is None


# --- Licences: the list and matching -------------------------------------------------

def test_licence_list_offers_eight_licences_and_the_declaration(client):
    body = client.get("/api/v1/publications/get-list-licenses").get_json()
    assert [licence["code"] for licence in body["licenses"]] == [
        "CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0", "CC-BY-ND-4.0", "CC-BY-NC-4.0",
        "CC-BY-NC-SA-4.0", "CC-BY-NC-ND-4.0", "ALL-RIGHTS-RESERVED"]
    assert body["licenses"][1]["url"] == "https://creativecommons.org/licenses/by/4.0/"
    assert body["licenses"][4]["allows_commercial"] is False
    assert body["rights_declaration"]["version"] == "decl-v1"
    assert "cannot be withdrawn" in body["rights_declaration"]["text"]


def test_catalogue_seeding_is_idempotent():
    assert ensure_license_catalogue() == 0
    assert Licenses.query.filter_by(code="CC-BY-4.0").count() == 1


@pytest.mark.parametrize("url, expected", [
    ("https://creativecommons.org/licenses/by/4.0/legalcode.en", "CC-BY-4.0"),
    ("http://creativecommons.org/licenses/by/4.0/deed.fr", "CC-BY-4.0"),
    ("https://creativecommons.org/licenses/by-nc-sa/2.5/za/", "CC-BY-NC-SA-2.5"),  # South African port
    ("https://creativecommons.org/publicdomain/zero/1.0/legalcode", "CC0-1.0"),
    ("https://rightsstatements.org/page/InC/1.0/?language=en", "ALL-RIGHTS-RESERVED"),
    ("https://example.org/our-own-licence", None),
])
def test_licence_urls_match_their_row(url, expected):
    licence = match_license(url=url)
    assert (licence.code if licence else None) == expected
    assert normalise_license_url(None) == ""


# --- /publish ------------------------------------------------------------------------

def test_publish_saves_each_files_own_date_and_licence(client):
    _, headers = _make_user("file-publish")
    form = _publish_form("20.500.14351/filepub0001", documents=1, files=[
        {"publication_date": "2019-05-14", "license_id": "ALL-RIGHTS-RESERVED"},
        {"license_id": str(_licence("CC-BY-4.0").id)},  # no date: optional
    ])
    response = client.post("/api/v1/publications/publish", data=form, headers=headers)
    assert response.status_code == 200, response.get_json()
    publication_id = response.get_json()["publication_id"]
    assert "publication_date" not in response.get_json()["publication"]  # a DOCiD has no date of its own

    detail = client.get(f"/api/v1/publications/get-publication/{publication_id}").get_json()
    assert [(f["publication_date"], f["license"]["code"]) for f in detail["publications_files"]] == [
        ("2019-05-14", "ALL-RIGHTS-RESERVED"), (None, "CC-BY-4.0")]
    assert "publication_date" not in detail and "license" not in detail
    assert detail["created_at"].endswith("Z")  # the DOCiD's own date: when it was created
    document = detail["publication_documents"][0]
    assert "publication_date" not in document and "license" not in document

    assert _declarations(publication_id) == [
        {"declaration": "decl-v1", "files": {"1": "ALL-RIGHTS-RESERVED", "2": "CC-BY-4.0"}}]


@pytest.mark.parametrize("change, message", [
    ({"filesPublications[1][license_id]": None}, "Publication 2: license_id is required"),
    ({"filesPublications[0][license_id]": "CC-BY-3.0"}, "Publication 1: license_id must be"),  # import-only row
    ({"filesPublications[0][license_id]": "9999"}, "Publication 1: license_id must be"),
    ({"filesPublications[1][publication_date]": "2019-13"}, "Publication 2: publication_date must be"),
    ({"rightsDeclaration": None}, "rights declaration must be confirmed"),
])
def test_publish_rejects_a_missing_or_invalid_file_licence_or_date(client, change, message):
    _, headers = _make_user("file-reject")
    form = _publish_form("20.500.14351/filerej0001", files=[{"license_id": "CC-BY-4.0"}, {"license_id": "CC0-1.0"}])
    for key, value in change.items():
        if value is None:
            form.pop(key)
        else:
            form[key] = value
    response = client.post("/api/v1/publications/publish", data=form, headers=headers)
    assert response.status_code == 400
    assert message in response.get_json()["message"]
    assert Publications.query.filter_by(document_docid="20.500.14351/filerej0001").count() == 0


def test_publish_without_files_needs_no_licence_or_declaration(client):
    _, headers = _make_user("file-none")
    form = _publish_form("20.500.14351/filenone001", documents=1, declared=False)
    form["licenseId"] = "CC-BY-4.0"         # DOCiD-level fields no longer exist and are ignored
    form["publicationDate"] = "2019"
    response = client.post("/api/v1/publications/publish", data=form, headers=headers)
    assert response.status_code == 200, response.get_json()
    assert _declarations(response.get_json()["publication_id"]) == []


def test_a_version_needs_each_files_licence_and_never_copies_dates(client):
    owner_id, headers = _make_user("file-version")
    parent = _make_publication(owner_id, "20.500.14351/filever0001")
    _add_file(parent, licence=_licence("CC-BY-4.0"), publication_date=date(2019, 1, 1), publication_date_precision="year")
    form = {"parentId": str(parent.id), **_publish_form("20.500.14351/filever0002", files=[{}])}

    response = client.post("/api/v1/publications/version", data=form, headers=headers)
    assert response.status_code == 400
    assert "license_id is required" in response.get_json()["message"]

    form["filesPublications[0][license_id]"] = "CC-BY-NC-4.0"
    response = client.post("/api/v1/publications/version", data=form, headers=headers)
    assert response.status_code == 200, response.get_json()
    version_file = db.session.get(Publications, response.get_json()["publication_id"]).publications_files[0]
    assert (version_file.license.code, version_file.publication_date) == ("CC-BY-NC-4.0", None)


# --- Edit routes for publication files ----------------------------------------------------

def test_adding_a_file_needs_a_licence_and_the_declaration_before_minting(client):
    owner_id, headers = _make_user("file-add")
    publication = _make_publication(owner_id, "20.500.14351/fileadd0001")
    _, publication_type_id = _reference_ids()
    url = f"/api/v1/publications/{publication.id}/files"
    form = {"title": "Slides", "publication_type_id": str(publication_type_id),
            "video_url": "https://video.example/1", "publication_date": "2024-02"}

    with patch("app.routes.publication_edit.IdentifierService.generate_handle",
               return_value="20.500.14351/minted01") as mint:
        assert "license_id is required" in client.post(url, data=form, headers=headers).get_json()["error"]
        response = client.post(url, data={**form, "license_id": "CC-BY-4.0"}, headers=headers)
        assert "rights declaration" in response.get_json()["error"]
        assert mint.call_count == 0  # both checked before a handle is minted

        response = client.post(url, data={**form, "license_id": "CC-BY-4.0", "rights_declaration": "true"},
                               headers=headers)
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    assert (body["publication_date"], body["license"]["code"]) == ("2024-02", "CC-BY-4.0")
    assert _declarations(publication.id) == [{"declaration": "decl-v1", "files": {str(body["id"]): "CC-BY-4.0"}}]


def test_updating_a_file_sets_keeps_and_clears_its_date_and_changes_its_licence(client):
    owner_id, headers = _make_user("file-update")
    publication = _make_publication(owner_id, "20.500.14351/fileupd0001")
    publication_file = _add_file(publication, licence=_licence("CC-BY-4.0"))
    url = f"/api/v1/publications/{publication.id}/files/{publication_file.id}"

    assert client.put(url, json={"publication_date": "2015"}, headers=headers).get_json()["publication_date"] == "2015"
    assert client.put(url, json={"title": "Renamed"}, headers=headers).get_json()["publication_date"] == "2015"
    assert client.put(url, json={"publication_date": "undefined"}, headers=headers).get_json()["publication_date"] == "2015"
    assert client.put(url, json={"publication_date": ""}, headers=headers).get_json()["publication_date"] is None
    assert client.put(url, json={"publication_date": "2999"}, headers=headers).status_code == 400

    assert client.put(url, json={"license_id": "ALL-RIGHTS-RESERVED"}, headers=headers).status_code == 400
    body = client.put(url, json={"license_id": "ALL-RIGHTS-RESERVED", "rights_declaration": True},
                      headers=headers).get_json()
    assert body["license"]["code"] == "ALL-RIGHTS-RESERVED"
    # A blank licence keeps it: a file's licence can't be cleared.
    assert client.put(url, json={"license_id": ""}, headers=headers).get_json()["license"]["code"] == "ALL-RIGHTS-RESERVED"
    audit = PublicationAuditTrail.query.filter_by(publication_id=publication.id, field_name="file.license").one()
    assert (audit.old_value, audit.new_value) == ("CC-BY-4.0", "ALL-RIGHTS-RESERVED")
    assert _declarations(publication.id) == [
        {"declaration": "decl-v1", "files": {str(publication_file.id): "ALL-RIGHTS-RESERVED"}}]


def test_document_routes_ignore_dates_and_licences(client):
    owner_id, headers = _make_user("doc-untouched")
    publication = _make_publication(owner_id, "20.500.14351/docunt0001")
    _, publication_type_id = _reference_ids()
    document = PublicationDocuments(publication_id=publication.id, title="Survey data", description="d",
                                    publication_type_id=publication_type_id, file_url="/uploads/d.csv")
    db.session.add(document)
    db.session.commit()
    body = client.put(f"/api/v1/publications/{publication.id}/documents/{document.id}",
                      json={"publication_date": "2015", "license_id": "CC0-1.0"}, headers=headers).get_json()
    assert body["changes"] == []
    assert not hasattr(PublicationDocuments, "license_id") and not hasattr(PublicationDocuments, "publication_date")


# --- Outputs: JSON-LD and Cordra --------------------------------------------------------

def test_jsonld_lists_each_file_with_its_own_date_and_licence(client):
    owner_id, _ = _make_user("file-jsonld")
    publication = _make_publication(owner_id, "20.500.14351/filejld001")
    publication_file = _add_file(publication, licence=_licence("CC0-1.0"), publication_date=date(2019, 5, 1),
                                 publication_date_precision="month", handle_identifier="20.500.14351/file1")

    body = client.get(f"/api/v1/publications/{publication.id}/jsonld").get_json()
    assert body["datePublished"] == "2026-11-20T08:30:00"  # the DOCiD's own date: when it was created
    assert "license" not in body
    assert body["hasPart"] == [{
        "@type": "CreativeWork", "name": publication_file.title,
        "identifier": "https://hdl.handle.net/20.500.14351/file1",
        "datePublished": "2019-05", "license": "https://creativecommons.org/publicdomain/zero/1.0/"}]


def test_cordra_sends_date_and_licence_only_on_the_file():
    import push_to_cordra

    owner_id, _ = _make_user("file-cordra")
    publication = _make_publication(owner_id, "20.500.14351/filecor001")
    _add_file(publication, licence=_licence("ALL-RIGHTS-RESERVED"), publication_date=date(2019, 1, 1),
              publication_date_precision="year", handle_identifier="20.500.14351/file1")

    with patch.object(push_to_cordra, "update_object", return_value={}) as update_object, \
            patch.object(push_to_cordra, "build_openalex_external_metadata", return_value=(None, [])):
        push_to_cordra.push_publication_to_cordra(publication)
        push_to_cordra.push_publication_files_to_cordra(publication)

    docid_content = update_object.call_args_list[0].args[1]["attributes"]["content"]
    file_content = update_object.call_args_list[1].args[1]["attributes"]["content"]
    assert "publication_date" not in docid_content and "license" not in docid_content
    assert docid_content["created_on"] == int(datetime(2026, 11, 20, 8, 30).timestamp())
    assert (file_content["publication_date"], file_content["license"]["code"]) == ("2019", "ALL-RIGHTS-RESERVED")
