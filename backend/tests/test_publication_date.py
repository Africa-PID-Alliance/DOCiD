"""The work's own publication date, kept apart from the DOCiD record's creation time."""

from datetime import date, datetime, timedelta
from unittest.mock import patch

import pytest
from flask_jwt_extended import create_access_token

from app import db
from app.models import Publications, ResourceTypes, UserAccount
from app.service_dspace import DSpaceMetadataMapper
from app.utils.publication_dates import (
    apply_source_publication_date,
    format_publication_date,
    parse_publication_date_input,
    parse_source_publication_date,
)


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
    return user.user_id, {"Authorization": f"Bearer {create_access_token(identity=str(user.user_id))}"}


def _make_publication(owner_id, docid, **fields):
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
        published=datetime(2026, 11, 20, 8, 30, 0),
        **fields,
    )
    db.session.add(publication)
    db.session.commit()
    return publication.id


# --- Parsing and formatting -------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ("2019", (date(2019, 1, 1), "year")),
    ("2019-05", (date(2019, 5, 1), "month")),
    ("2019-05-14", (date(2019, 5, 14), "day")),
    (" 2019-05-14 ", (date(2019, 5, 14), "day")),
    ("", (None, None)),
    (None, (None, None)),
])
def test_api_input_accepts_year_month_or_day(raw, expected):
    assert parse_publication_date_input(raw) == expected


@pytest.mark.parametrize("raw", [
    "19", "2019-5", "2019/05/14", "14-05-2019", "2019-13", "2019-02-30",
    "2019-05-14T10:00:00Z", "May 2019", str(date.today().year + 1),
    (date.today() + timedelta(days=1)).isoformat(),
])
def test_api_input_rejects_other_shapes_and_future_dates(raw):
    with pytest.raises(ValueError):
        parse_publication_date_input(raw)


def test_api_input_allows_the_current_year_and_month():
    today = date.today()
    assert parse_publication_date_input(str(today.year))[1] == "year"
    assert parse_publication_date_input(today.strftime("%Y-%m"))[1] == "month"
    assert parse_publication_date_input(today.isoformat())[1] == "day"


@pytest.mark.parametrize("raw, expected", [
    ("2019", (date(2019, 1, 1), "year")),
    ("2019-05", (date(2019, 5, 1), "month")),
    ("2019-05-14T10:00:00Z", (date(2019, 5, 14), "day")),  # Figshare
    ("2019-05-14 10:00:00", (date(2019, 5, 14), "day")),
    (datetime(2019, 5, 14, 10, 0), (date(2019, 5, 14), "day")),
    ("n.d.", (None, None)),
    ("2019-13-01", (None, None)),
    (str(date.today().year + 2), (None, None)),  # an embargo date is not a publication date
    (None, (None, None)),
])
def test_source_dates_are_read_leniently(raw, expected):
    assert parse_source_publication_date(raw) == expected


def test_dates_are_serialised_at_their_precision():
    assert format_publication_date(date(2019, 1, 1), "year") == "2019"
    assert format_publication_date(date(2019, 5, 1), "month") == "2019-05"
    assert format_publication_date(date(2019, 5, 14), "day") == "2019-05-14"
    assert format_publication_date(None, None) is None


def test_a_source_without_a_date_never_clears_an_existing_one():
    publication = Publications(publication_date=date(2018, 1, 1), publication_date_precision="year")
    assert apply_source_publication_date(publication, None) is False
    assert apply_source_publication_date(publication, "not a date") is False
    assert (publication.publication_date, publication.publication_date_precision) == (date(2018, 1, 1), "year")

    assert apply_source_publication_date(publication, "2019-05") is True
    assert (publication.publication_date, publication.publication_date_precision) == (date(2019, 5, 1), "month")


def test_dspace_year_only_issued_date_keeps_year_precision():
    item = {"uuid": "u-1", "handle": "123/1", "metadata": {
        "dc.title": [{"value": "A thesis"}],
        "dc.date.issued": [{"value": "2019"}],
    }}
    mapped = DSpaceMetadataMapper.dspace_to_docid(item, user_id=1)
    publication = Publications()
    apply_source_publication_date(publication, mapped["publication"]["publication_date"])
    assert (publication.publication_date, publication.publication_date_precision) == (date(2019, 1, 1), "year")


# --- API --------------------------------------------------------------------

def test_detail_endpoints_return_publication_date_and_created_at(client):
    owner_id, _ = _make_user("pubdate-detail")
    with_date = _make_publication(owner_id, "20.500.14351/pubdate0000000001",
                                  publication_date=date(2019, 5, 1), publication_date_precision="month")
    without_date = _make_publication(owner_id, "20.500.14351/pubdate0000000002")

    body = client.get(f"/api/v1/publications/get-publication/{with_date}").get_json()
    assert body["publication_date"] == "2019-05"
    assert body["created_at"] == "2026-11-20T08:30:00Z"
    assert body["published"] == int(datetime(2026, 11, 20, 8, 30, 0).timestamp())  # deprecated key unchanged

    body = client.get("/api/v1/publications/docid?docid=20.500.14351/pubdate0000000002").get_json()
    assert body["publication_date"] is None
    assert body["created_at"] == "2026-11-20T08:30:00Z"
    assert without_date


def test_list_returns_the_fields_and_sorts_unknown_dates_last(client):
    owner_id, _ = _make_user("pubdate-list")
    _make_publication(owner_id, "20.500.14351/pubdatelist01", publication_date=date(2015, 1, 1), publication_date_precision="year")
    _make_publication(owner_id, "20.500.14351/pubdatelist02")
    _make_publication(owner_id, "20.500.14351/pubdatelist03", publication_date=date(2020, 3, 9), publication_date_precision="day")

    for order, expected in (("desc", ["2020-03-09", "2015", None]), ("asc", ["2015", "2020-03-09", None])):
        body = client.get(f"/api/v1/publications/get-publications?sort=publication_date&order={order}").get_json()
        assert [item["publication_date"] for item in body["data"]] == expected
        assert all(item["created_at"] == "2026-11-20T08:30:00Z" for item in body["data"])


def test_user_profile_list_returns_and_sorts_by_publication_date(client):
    owner_id, headers = _make_user("pubdate-profile")
    _make_publication(owner_id, "20.500.14351/pubdateprof01")
    _make_publication(owner_id, "20.500.14351/pubdateprof02", publication_date=date(2011, 1, 1), publication_date_precision="year")

    body = client.get(f"/api/v1/user-profile/{owner_id}/publications?sort=publication_date", headers=headers).get_json()
    assert [item["publication_date"] for item in body["publications"]] == ["2011", None]
    assert body["publications"][0]["created_at"] == "2026-11-20T08:30:00Z"


def test_update_sets_keeps_and_clears_the_date(client):
    owner_id, headers = _make_user("pubdate-update")
    publication_id = _make_publication(owner_id, "20.500.14351/pubdateupd01")
    url = f"/api/v1/publications/update-publication/{publication_id}"

    assert client.put(url, data={"publicationDate": "2019-05-14"}, headers=headers).status_code == 200
    assert db.session.get(Publications, publication_id).publication_date == date(2019, 5, 14)

    # Leaving the field out (or the frontend's "undefined") keeps it.
    assert client.put(url, data={"documentTitle": "Renamed"}, headers=headers).status_code == 200
    assert client.put(url, data={"publicationDate": "undefined"}, headers=headers).status_code == 200
    db.session.expire_all()
    assert db.session.get(Publications, publication_id).publication_date == date(2019, 5, 14)

    # An empty string clears it.
    assert client.put(url, data={"publicationDate": ""}, headers=headers).status_code == 200
    db.session.expire_all()
    cleared = db.session.get(Publications, publication_id)
    assert (cleared.publication_date, cleared.publication_date_precision) == (None, None)


def test_update_rejects_an_invalid_date_without_changing_anything(client):
    owner_id, headers = _make_user("pubdate-invalid")
    publication_id = _make_publication(owner_id, "20.500.14351/pubdateinv01")
    url = f"/api/v1/publications/update-publication/{publication_id}"

    response = client.put(url, data={"publicationDate": "2019-13", "documentTitle": "Should not stick"}, headers=headers)
    assert response.status_code == 400
    assert "publicationDate" in response.get_json()["message"]
    db.session.expire_all()
    unchanged = db.session.get(Publications, publication_id)
    assert unchanged.publication_date is None
    assert unchanged.document_title == "Title for 20.500.14351/pubdateinv01"


def test_jsonld_uses_the_real_date_and_omits_it_when_unknown(client):
    owner_id, _ = _make_user("pubdate-jsonld")
    dated = _make_publication(owner_id, "20.500.14351/pubdatejld01", publication_date=date(2019, 1, 1), publication_date_precision="year")
    undated = _make_publication(owner_id, "20.500.14351/pubdatejld02")

    assert client.get(f"/api/v1/publications/{dated}/jsonld").get_json()["datePublished"] == "2019"
    body = client.get(f"/api/v1/publications/{undated}/jsonld").get_json()
    assert "datePublished" not in body
    assert "dateCreated" not in body


def test_cordra_payload_adds_publication_date_and_keeps_created_on():
    import push_to_cordra

    owner_id, _ = _make_user("pubdate-cordra")
    dated = db.session.get(Publications, _make_publication(
        owner_id, "20.500.14351/pubdatecor01", publication_date=date(2019, 5, 1), publication_date_precision="month"))
    undated = db.session.get(Publications, _make_publication(owner_id, "20.500.14351/pubdatecor02"))

    with patch.object(push_to_cordra, "update_object", return_value={}) as update_object, \
            patch.object(push_to_cordra, "build_openalex_external_metadata", return_value=(None, [])):
        assert push_to_cordra.push_publication_to_cordra(dated)
        assert push_to_cordra.push_publication_to_cordra(undated)

    dated_content = update_object.call_args_list[0].args[1]["attributes"]["content"]
    undated_content = update_object.call_args_list[1].args[1]["attributes"]["content"]
    assert dated_content["publication_date"] == "2019-05"
    assert dated_content["created_on"] == int(datetime(2026, 11, 20, 8, 30, 0).timestamp())
    assert "publication_date" not in undated_content


# --- DSpace: dc.date.issued, else dc.date.created ------------------------------

@pytest.mark.parametrize("dates, expected", [
    ({"dc.date.issued": "2019", "dc.date.created": "1924"}, "2019"),     # issued wins
    ({"dc.date.created": "1924"}, "1924"),                              # heritage item: only created
    ({"dc.date.issued": "n.d.", "dc.date.created": "1924"}, "1924"),     # unusable issued falls back
    ({"dc.date.accessioned": "2016-04-04T10:00:58Z",
      "dc.date.available": "2016-04-04T10:00:58Z"}, None),              # repository dates never used
])
def test_dspace_mappers_fall_back_to_dc_date_created(dates, expected):
    from app.service_dspace_legacy import DSpaceLegacyMetadataMapper

    modern_item = {"uuid": "u", "handle": "1/1", "metadata": {
        "dc.title": [{"value": "Photo"}], **{key: [{"value": value}] for key, value in dates.items()}}}
    legacy_item = {"uuid": "u", "handle": "1/1", "metadata": [
        {"key": "dc.title", "value": "Photo"}, *({"key": key, "value": value} for key, value in dates.items())]}

    assert DSpaceMetadataMapper.dspace_to_docid(modern_item, user_id=1)["publication"]["publication_date"] == expected
    assert DSpaceLegacyMetadataMapper.dspace_to_docid(legacy_item, user_id=1)["publication"]["publication_date"] == expected
