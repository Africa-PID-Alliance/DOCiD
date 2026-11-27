"""Related DOCiDs from URAAS (GET /api/v1/publications/<id>/related-docids)."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import requests

from app import db
from app.models import PublicationCreators, Publications, ResourceTypes, UserAccount

URAAS_GET = "app.service_uraas.requests.get"
AUTO = object()


@pytest.fixture(autouse=True)
def uraas_config(app, monkeypatch):
    monkeypatch.setitem(app.config, "URAAS_API_KEY", "test-uraas-key")
    monkeypatch.setitem(app.config, "URAAS_BASE_URL", "https://uraas.example.test")


def _docid(publication_id):
    return f"20.500.14351/p{publication_id}"


def _make_owner():
    user = UserAccount(
        user_name="related-owner",
        full_name="Related Owner",
        email="related-owner@example.test",
        type="email",
        role="user",
        password="unused",
    )
    db.session.add(user)
    resource_type = ResourceTypes(resource_type="dataset")
    db.session.add(resource_type)
    db.session.flush()
    return user.user_id, resource_type.id


def _make_publication(publication_id, owner_id, resource_type_id, docid=AUTO, deleted=False,
                      owner="University of Lagos", creators=()):
    """creators: (given_name, family_name, orcid or None) tuples, in order."""
    db.session.add(Publications(
        id=publication_id,
        user_id=owner_id,
        document_docid=_docid(publication_id) if docid is AUTO else docid,
        document_title=f"Paper {publication_id}",
        document_description="fixture",
        resource_type_id=resource_type_id,
        owner=owner,
        deleted_at=datetime.utcnow() if deleted else None,
    ))
    for given_name, family_name, orcid in creators:
        db.session.add(PublicationCreators(
            publication_id=publication_id,
            given_name=given_name,
            family_name=family_name,
            identifier=f"https://orcid.org/{orcid}" if orcid else None,
            identifier_type="orcid" if orcid else None,
            role_id="1",
        ))
    db.session.commit()


def _related_item(publication_id, type_id, owner="University of Lagos"):
    return {
        "id": publication_id,
        "document_title": f"Paper {publication_id}",
        "document_docid": _docid(publication_id),
        "resource_type_id": type_id,
        "resource_type": "dataset",
        "owner": owner,
        "shared_authors": [],
    }


def _uraas_response(related_ids=(), page_id=10, page_docid=AUTO, items=None, status_code=200):
    """URAAS's /api/docid/enrichment/<id>/related answer.

    Each related id comes back the way URAAS sends it: docid_publication_id as
    a string, its own item id (deliberately different) in "id".
    """
    response = MagicMock(status_code=status_code)
    if items is None:
        items = [{"id": 9000 + rid, "docid_publication_id": str(rid), "docid": _docid(rid),
                  "title": f"URAAS {rid}", "overlap_score": 0.1, "shared_keywords": ["x"]}
                 for rid in related_ids]
    response.json.return_value = {
        "count": len(items),
        "docid": _docid(page_id) if page_docid is AUTO else page_docid,
        "docid_publication_id": str(page_id),
        "uraas_item_id": 9000 + page_id,
        "related": items,
    }
    return response


def test_lists_live_docids_in_uraas_order(client):
    owner_id, type_id = _make_owner()
    _make_publication(10, owner_id, type_id)
    _make_publication(20, owner_id, type_id)
    _make_publication(30, owner_id, type_id, owner=None)
    _make_publication(40, owner_id, type_id, deleted=True)
    _make_publication(50, owner_id, type_id, docid=None)

    # 60 isn't in DOCiD, 10 is the page itself, 40 is retired, 50 has no DOCiD.
    with patch(URAAS_GET, return_value=_uraas_response(related_ids=[30, 60, 10, 40, 20, 50])) as uraas_get:
        response = client.get("/api/v1/publications/10/related-docids")

    assert response.status_code == 200
    body = response.get_json()
    assert body["publication_id"] == 10
    assert body["related"] == [
        _related_item(30, type_id, owner=None),
        _related_item(20, type_id),
    ]
    uraas_get.assert_called_once()
    assert uraas_get.call_args.args[0] == "https://uraas.example.test/api/docid/enrichment/10/related"
    assert uraas_get.call_args.kwargs["params"] == {"limit": 10, "docid_only": 1}
    assert uraas_get.call_args.kwargs["headers"] == {"X-API-Key": "test-uraas-key"}


def test_uses_docid_publication_id_not_uraas_item_id(client):
    owner_id, type_id = _make_owner()
    _make_publication(10, owner_id, type_id)
    _make_publication(20, owner_id, type_id)
    _make_publication(30, owner_id, type_id)
    # URAAS's own item id 20 must not be read as DOCiD publication 20.
    items = [{"id": 20, "docid_publication_id": "30", "docid": _docid(30)}]

    with patch(URAAS_GET, return_value=_uraas_response(items=items)):
        response = client.get("/api/v1/publications/10/related-docids")

    assert [item["id"] for item in response.get_json()["related"]] == [30]


def test_record_uraas_holds_under_another_docid_shows_nothing(client):
    # e.g. a production id that URAAS, which only knows docid-demo, reads as another record.
    owner_id, type_id = _make_owner()
    _make_publication(10, owner_id, type_id)
    _make_publication(20, owner_id, type_id)

    with patch(URAAS_GET, return_value=_uraas_response(related_ids=[20], page_docid="20.500.14351/elsewhere")):
        response = client.get("/api/v1/publications/10/related-docids")

    assert response.status_code == 200
    assert response.get_json()["related"] == []


def test_related_id_whose_docid_differs_from_ours_is_skipped(client):
    owner_id, type_id = _make_owner()
    _make_publication(10, owner_id, type_id)
    _make_publication(20, owner_id, type_id)
    _make_publication(30, owner_id, type_id)
    items = [
        {"id": 1, "docid_publication_id": "20", "docid": "20.500.14351/not-ours"},
        {"id": 2, "docid_publication_id": "30", "docid": _docid(30)},
    ]

    with patch(URAAS_GET, return_value=_uraas_response(items=items)):
        response = client.get("/api/v1/publications/10/related-docids")

    assert [item["id"] for item in response.get_json()["related"]] == [30]


def test_items_without_a_usable_id_or_docid_are_skipped(client):
    owner_id, type_id = _make_owner()
    _make_publication(10, owner_id, type_id)
    _make_publication(20, owner_id, type_id)
    items = [
        {"id": 1, "docid_publication_id": None, "docid": _docid(20)},
        {"id": 2, "docid_publication_id": "abc", "docid": _docid(20)},
        {"id": 3, "docid_publication_id": "20", "docid": ""},
        "not an object",
        {"id": 4, "docid_publication_id": "20", "docid": _docid(20)},
        {"id": 5, "docid_publication_id": "20", "docid": _docid(20)},
    ]

    with patch(URAAS_GET, return_value=_uraas_response(items=items)):
        response = client.get("/api/v1/publications/10/related-docids")

    assert [item["id"] for item in response.get_json()["related"]] == [20]


def test_record_not_ingested_by_uraas_gives_empty_list(client):
    owner_id, type_id = _make_owner()
    _make_publication(10, owner_id, type_id)

    with patch(URAAS_GET, return_value=_uraas_response(status_code=404)):
        response = client.get("/api/v1/publications/10/related-docids")

    assert response.status_code == 200
    assert response.get_json()["related"] == []


def test_uraas_failure_is_503(client):
    owner_id, type_id = _make_owner()
    _make_publication(10, owner_id, type_id)

    with patch(URAAS_GET, side_effect=requests.Timeout()):
        response = client.get("/api/v1/publications/10/related-docids")

    assert response.status_code == 503
    assert response.get_json()["related"] == []


def test_missing_key_is_503_without_calling_uraas(app, client, monkeypatch):
    monkeypatch.setitem(app.config, "URAAS_API_KEY", "")
    owner_id, type_id = _make_owner()
    _make_publication(10, owner_id, type_id)

    with patch(URAAS_GET) as uraas_get:
        response = client.get("/api/v1/publications/10/related-docids")

    assert response.status_code == 503
    uraas_get.assert_not_called()


@pytest.mark.parametrize("deleted", [False, True])
def test_unknown_or_retired_publication_is_404_without_calling_uraas(client, deleted):
    if deleted:
        owner_id, type_id = _make_owner()
        _make_publication(10, owner_id, type_id, deleted=True)

    with patch(URAAS_GET) as uraas_get:
        response = client.get("/api/v1/publications/10/related-docids")

    assert response.status_code == 404
    uraas_get.assert_not_called()


ORCID_MARY = "0000-0002-1825-0097"
ORCID_OTHER = "0000-0001-5109-3700"


@pytest.mark.parametrize("page_creator, related_creator, shared_authors", [
    # The same ORCID is the same person, however the name is written.
    (("Mary", "Abukutsa-Onyango", ORCID_MARY), ("M. A.", "Onyango", ORCID_MARY), ["Mary Abukutsa-Onyango"]),
    # Two different ORCIDs are two people, even with the same name.
    (("Mary", "Abukutsa-Onyango", ORCID_MARY), ("Mary", "Abukutsa-Onyango", ORCID_OTHER), []),
    # Without ORCIDs on both sides: surname + first initial, ignoring case, accents and dots.
    (("Bénédicte", "Naudé", None), ("b.", "NAUDE", None), ["Bénédicte Naudé"]),
    (("Bénédicte", "Naudé", ORCID_MARY), ("B", "Naude", None), ["Bénédicte Naudé"]),
    (("Bénédicte", "Naudé", None), ("Carl", "Naudé", None), []),
    # Organisations have no given name and never match by name.
    ((None, "Manuscripts Section", None), (None, "Manuscripts Section", None), []),
])
def test_shared_author_matching(client, page_creator, related_creator, shared_authors):
    owner_id, type_id = _make_owner()
    _make_publication(10, owner_id, type_id, creators=[page_creator])
    _make_publication(20, owner_id, type_id, creators=[related_creator])

    with patch(URAAS_GET, return_value=_uraas_response(related_ids=[20])):
        response = client.get("/api/v1/publications/10/related-docids")

    [item] = response.get_json()["related"]
    assert item["shared_authors"] == shared_authors


def test_lists_every_shared_author_in_the_page_records_order(client):
    owner_id, type_id = _make_owner()
    _make_publication(10, owner_id, type_id, creators=[
        ("Ada", "Obi", None), ("Bola", "Ade", None), ("Chidi", "Eze", None), ("Ada", "Obi", None),
    ])
    _make_publication(20, owner_id, type_id, creators=[
        ("C.", "Eze", None), ("Zainab", "Bello", None), ("A", "Obi", None),
    ])

    with patch(URAAS_GET, return_value=_uraas_response(related_ids=[20])):
        response = client.get("/api/v1/publications/10/related-docids")

    [item] = response.get_json()["related"]
    assert item["shared_authors"] == ["Ada Obi", "Chidi Eze"]


def test_items_keep_uraas_order_whether_or_not_they_share_authors(client):
    owner_id, type_id = _make_owner()
    author = ("Mary", "Abukutsa-Onyango", ORCID_MARY)
    stranger = ("Zainab", "Bello", None)
    _make_publication(10, owner_id, type_id, creators=[author])
    _make_publication(20, owner_id, type_id, creators=[stranger])
    _make_publication(30, owner_id, type_id, creators=[author])
    _make_publication(40, owner_id, type_id)
    _make_publication(50, owner_id, type_id, creators=[stranger, author])

    with patch(URAAS_GET, return_value=_uraas_response(related_ids=[20, 30, 40, 50])):
        response = client.get("/api/v1/publications/10/related-docids")

    related = response.get_json()["related"]
    assert [(item["id"], item["shared_authors"]) for item in related] == [
        (20, []), (30, ["Mary Abukutsa-Onyango"]), (40, []), (50, ["Mary Abukutsa-Onyango"]),
    ]
