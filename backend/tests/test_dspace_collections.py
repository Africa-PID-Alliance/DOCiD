"""
Watched DSpace collections: anonymous harvest, typing by collection, write-back
of the DOCiD URL, and hiding records the holding repository restricts.

DSpace is stubbed with `responses`; the request shapes match what DSpace 10.2
returned in the local walk-through (see the "Life of a DSpace record" doc).
"""
import json
import logging
import re
from datetime import datetime, timezone
from itertools import count
from urllib.parse import parse_qs, urlparse

import pytest
import responses
from flask_jwt_extended import create_access_token

import harvest_repositories
from app import db
from app.models import (
    DSpaceMapping,
    EnrichmentRun,
    HarvestSource,
    HarvestSourceCollection,
    Publications,
    ResourceTypes,
    UserAccount,
)
from app.service_dspace import DSpaceClient
from app.service_dspace_collections import (
    CHANGE_CHECK_ERROR_PREFIX,
    CHANGE_CHECK_OVERLAP,
    WITHHELD_REASONS,
    apply_dspace_status,
    check_collection_connection,
    check_watched_collections_for_changes,
    harvest_watched_collections,
    source_lock,
)
from app.service_identifiers import IdentifierService
from app.utils_crypto import encrypt_value

BASE = "https://repo.test/server"
API = f"{BASE}/api"
DISCOVER = f"{API}/discover/search/objects"
COLLECTION_UUID = "35369f97-dd65-43ab-b18b-d00072353de3"
ITEM_UUID = "3a2d8132-4dbc-44e5-8c07-737f2748e70a"
ITEM_HANDLE = "123456789/1151"
NEW_UUID = "7c1e5a40-2f7d-4b8e-9a61-0d3c2b1a9f88"
NEW_HANDLE = "123456789/1160"
RESTRICTED_UUID = "11111111-1111-1111-1111-111111111111"
JWT = "Bearer dspace-jwt"


def _now_iso():
    """Now, written the way DSpace writes lastModified."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


# ---------------------------------------------------------------- fixtures

@pytest.fixture(autouse=True)
def no_politeness_delay(monkeypatch):
    """The harvester waits 1 s between requests to a repository; pointless against a stub."""
    monkeypatch.setattr("app.service_dspace.time.sleep", lambda seconds: None)


@pytest.fixture(autouse=True)
def private_lock_dir(monkeypatch, tmp_path):
    """Per-source harvest locks go in a directory of the test's own."""
    monkeypatch.setattr("app.service_dspace_collections.SOURCE_LOCK_DIR", str(tmp_path))


@pytest.fixture
def secret_key(app):
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = "test-secret-for-dspace-collections"
    return app.config["SECRET_KEY"]


@pytest.fixture
def institution(secret_key):
    """The institution's DOCiD owner account, its DSpace source and one watched IK collection."""
    owner = UserAccount(user_name="ik-institution", full_name="IK Institution",
                        email="repository@institution.test", type="email", role="user", password="unused")
    indigenous_knowledge = ResourceTypes(resource_type="Indigeneous Knowledge")
    db.session.add_all([owner, indigenous_knowledge])
    db.session.flush()

    source = HarvestSource(
        name="Test University", base_url=BASE, ui_base_url="https://repo.test", api_type="modern",
        auth_required=True, owner_name="Test University", owner_email=owner.email,
        encrypted_username=encrypt_value("dspace-integration@africapidalliance.test", secret_key),
        encrypted_password=encrypt_value("long-random-password", secret_key),
        harvest_frequency="daily",
    )
    db.session.add(source)
    db.session.flush()
    collection = HarvestSourceCollection(
        harvest_source_id=source.id, dspace_collection_uuid=COLLECTION_UUID,
        dspace_collection_handle="123456789/1149", collection_name="Indigenous Knowledge",
        resource_type_id=indigenous_knowledge.id,
    )
    db.session.add(collection)
    db.session.commit()
    return {"owner_id": owner.user_id, "source": source, "collection": collection,
            "ik_type_id": indigenous_knowledge.id}


@pytest.fixture
def minting(monkeypatch):
    """Cordra stub: hands out 20.500.14351/test... handles; set .fail = True to make minting fail."""
    class Minter:
        fail = False
        numbers = count(1)

        def __call__(self):
            if self.fail:
                return None
            return f"20.500.14351/test{next(self.numbers):016d}"

    minter = Minter()
    monkeypatch.setattr(IdentifierService, "generate_handle", minter)
    monkeypatch.setattr("app.service_dspace_collections.generate_dspace_thumbnail", lambda *args: None)
    return minter


def _item(uuid=ITEM_UUID, handle=ITEM_HANDLE, title="Seed-saving practices", withdrawn=False,
          discoverable=True, uris=None, last_modified="2026-11-04T14:03:05.538Z"):
    return {
        "uuid": uuid, "handle": handle, "name": title, "type": "item",
        "withdrawn": withdrawn, "discoverable": discoverable,
        "lastModified": last_modified,
        "metadata": {
            "dc.title": [{"value": title}],
            "dc.contributor.author": [{"value": "Curator, Test"}],
            "dc.identifier.uri": [{"value": value} for value in (uris or [f"https://repo.test/handle/{handle}"])],
        },
    }


def _listing(*items):
    return {"_embedded": {"searchResult": {
        "_embedded": {"objects": [{"_embedded": {"indexableObject": item}} for item in items]},
        "page": {"size": 100, "totalElements": len(items), "totalPages": 1 if items else 0, "number": 0},
    }}}


class FakeDSpace:
    """
    Stateful DSpace stub: anonymous visitors see only public items; the DOCiD account sees all.

    CSRF works like DSpace 10: a session without the DSPACE-XSRF-COOKIE is
    issued a token (header + cookie); later responses carry no header; login
    rotates the token; a write whose X-XSRF-TOKEN does not match is refused.
    Search honours a lastModified:[<time> TO *] query, and a metadata PATCH
    updates the item's lastModified, as DSpace does.
    """

    def __init__(self, rsps):
        self.rsps = rsps
        self.items = {}            # uuid -> item json
        self.anonymous_state = {}  # uuid -> 'public' | 'restricted' | 'deleted'
        self.patch_statuses = []   # queued PATCH status codes, default 200
        self.logins = 0
        self.tokens_issued = count(1)
        rsps.add_callback(responses.GET, DISCOVER, callback=self._discover)
        rsps.add_callback(responses.GET, f"{API}/authn/status", callback=self._status)
        rsps.add_callback(responses.POST, f"{API}/authn/login", callback=self._login)
        item_url = re.compile(rf"{API}/core/items/[0-9a-f-]+$")
        rsps.add_callback(responses.GET, item_url, callback=self._get_item)
        rsps.add_callback(responses.PATCH, item_url, callback=self._patch_item)

    @staticmethod
    def _cookie_token(request):
        for part in (request.headers.get("Cookie") or "").split(";"):
            name, _, value = part.strip().partition("=")
            if name == "DSPACE-XSRF-COOKIE":
                return value
        return None

    def _issue_token(self):
        token = f"csrf-{next(self.tokens_issued)}"
        return {"DSPACE-XSRF-TOKEN": token, "Set-Cookie": f"DSPACE-XSRF-COOKIE={token}; Path=/"}

    def _csrf_headers(self, request):
        return {} if self._cookie_token(request) else self._issue_token()

    def _csrf_ok(self, request):
        token = self._cookie_token(request)
        return token is not None and request.headers.get("X-XSRF-TOKEN") == token

    def add(self, item, anonymous_state="public"):
        self.items[item["uuid"]] = item
        self.anonymous_state[item["uuid"]] = anonymous_state

    def _anonymously_listed(self, item):
        return (self.anonymous_state[item["uuid"]] == "public"
                and not item["withdrawn"] and item["discoverable"])

    def _discover(self, request):
        listed = [item for item in self.items.values() if self._anonymously_listed(item)]
        query = parse_qs(urlparse(request.url).query).get("query", [""])[0]
        changed_since = re.fullmatch(r"lastModified:\[(\S+) TO \*\]", query)
        if changed_since:
            cutoff = _parse_time(changed_since.group(1))
            listed = [item for item in listed if _parse_time(item["lastModified"]) >= cutoff]
        return 200, self._csrf_headers(request), json.dumps(_listing(*listed))

    def _status(self, request):
        return 200, self._csrf_headers(request), json.dumps({"authenticated": False})

    def _login(self, request):
        if not self._csrf_ok(request):
            return 403, self._issue_token(), json.dumps({"message": "Invalid CSRF token"})
        self.logins += 1
        return 200, {"Authorization": JWT, **self._issue_token()}, ""

    def _get_item(self, request):
        uuid = request.url.rsplit("/", 1)[1]
        authenticated = request.headers.get("Authorization") == JWT
        state = self.anonymous_state.get(uuid, "deleted")
        if uuid not in self.items or (state == "deleted" and not authenticated):
            return 404, self._csrf_headers(request), "{}"
        if state == "restricted" and not authenticated:
            return 401, self._csrf_headers(request), "{}"
        return 200, self._csrf_headers(request), json.dumps(self.items[uuid])

    def _patch_item(self, request):
        if request.headers.get("Authorization") != JWT:
            return 401, {}, "{}"
        if not self._csrf_ok(request):
            return 403, self._issue_token(), json.dumps({"message": "Invalid CSRF token"})
        status = self.patch_statuses.pop(0) if self.patch_statuses else 200
        if status != 200:
            return status, {}, json.dumps({"message": f"refused {status}"})
        uuid = request.url.rsplit("/", 1)[1]
        for operation in json.loads(request.body):
            values = operation["value"] if isinstance(operation["value"], list) else [operation["value"]]
            self.items[uuid]["metadata"].setdefault("dc.identifier.uri", []).extend(values)
        self.items[uuid]["lastModified"] = _now_iso()
        return 200, {}, json.dumps(self.items[uuid])

    def calls(self, method, url_part):
        return [call for call in self.rsps.calls
                if call.request.method == method and url_part in call.request.url]


@pytest.fixture
def dspace():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield FakeDSpace(rsps)


def _harvest(institution, secret_key):
    source = db.session.get(HarvestSource, institution["source"].id)
    return harvest_watched_collections(source, secret_key)


def _mapping():
    return DSpaceMapping.query.filter_by(dspace_uuid=ITEM_UUID).one()


# ---------------------------------------------------------------- harvest + write-back

def test_new_public_record_gets_docid_of_collection_type_and_link_in_dspace(institution, dspace, minting, secret_key):
    dspace.add(_item())

    totals = _harvest(institution, secret_key)

    assert totals["created"] == 1 and totals["written_back"] == 1
    mapping = _mapping()
    publication = mapping.publication
    assert publication.resource_type_id == institution["ik_type_id"]
    assert publication.document_docid == "20.500.14351/test0000000000000001"
    assert publication.user_id == institution["owner_id"]
    assert publication.handle_url == f"https://repo.test/handle/{ITEM_HANDLE}"
    assert mapping.harvest_source_collection_id == institution["collection"].id
    assert mapping.dspace_status == "public"
    assert mapping.writeback_status == "done" and mapping.written_back_at is not None

    patches = dspace.calls("PATCH", ITEM_UUID)
    assert len(patches) == 1
    assert json.loads(patches[0].request.body) == [{
        "op": "add", "path": "/metadata/dc.identifier.uri/-",
        "value": {"value": "https://docid.africapidalliance.org/docid/20.500.14351/test0000000000000001"},
    }]
    # The handle stays first; the DOCiD URL is appended after it.
    uris = [value["value"] for value in dspace.items[ITEM_UUID]["metadata"]["dc.identifier.uri"]]
    assert uris == [f"https://repo.test/handle/{ITEM_HANDLE}",
                    "https://docid.africapidalliance.org/docid/20.500.14351/test0000000000000001"]


def test_harvest_reads_anonymously_and_logs_in_only_to_write(institution, dspace, minting, secret_key):
    dspace.add(_item())
    _harvest(institution, secret_key)

    for call in dspace.calls("GET", "/discover/search/objects"):
        assert "Authorization" not in call.request.headers
    first_item_read = dspace.calls("GET", f"/core/items/{ITEM_UUID}")[0]
    assert "Authorization" not in first_item_read.request.headers
    assert dspace.calls("PATCH", ITEM_UUID)[0].request.headers["Authorization"] == JWT


def test_restricted_record_never_reaches_docid(institution, dspace, minting, secret_key):
    dspace.add(_item(uuid="11111111-1111-1111-1111-111111111111", title="Restricted ceremony"),
               anonymous_state="restricted")

    totals = _harvest(institution, secret_key)

    assert totals["created"] == 0
    assert Publications.query.count() == 0


def test_second_run_adds_nothing_and_writes_nothing(institution, dspace, minting, secret_key):
    dspace.add(_item())
    _harvest(institution, secret_key)
    totals = _harvest(institution, secret_key)

    assert totals["created"] == 0
    assert Publications.query.count() == 1
    assert len(dspace.calls("PATCH", ITEM_UUID)) == 1


def test_write_back_skips_patch_when_link_already_in_dspace(institution, dspace, minting, secret_key):
    docid_url = "https://docid.africapidalliance.org/docid/20.500.14351/test0000000000000001"
    dspace.add(_item(uris=[f"https://repo.test/handle/{ITEM_HANDLE}", docid_url]))

    _harvest(institution, secret_key)

    assert _mapping().writeback_status == "done"
    assert dspace.calls("PATCH", ITEM_UUID) == []


def test_failed_mint_never_writes_back_and_is_retried(institution, dspace, minting, secret_key):
    dspace.add(_item())
    minting.fail = True
    _harvest(institution, secret_key)

    mapping = _mapping()
    assert mapping.writeback_status == "waiting_for_docid"
    assert mapping.publication.document_docid == ITEM_HANDLE
    assert dspace.calls("PATCH", ITEM_UUID) == []

    minting.fail = False
    _harvest(institution, secret_key)

    mapping = _mapping()
    assert mapping.publication.document_docid.startswith("20.500.14351/test")
    assert mapping.writeback_status == "done"
    assert len(dspace.calls("PATCH", ITEM_UUID)) == 1


def test_refused_write_marks_failed_and_collection_not_writable(institution, dspace, minting, secret_key):
    dspace.add(_item())
    dspace.patch_statuses = [403]

    totals = _harvest(institution, secret_key)

    mapping = _mapping()
    assert totals["writeback_failed"] == 1
    assert mapping.writeback_status == "failed"
    assert mapping.writeback_attempts == 1
    assert "403" in mapping.writeback_error
    assert db.session.get(HarvestSourceCollection, institution["collection"].id).write_back_ok is False

    # Retried on the next run once the role is back.
    _harvest(institution, secret_key)
    assert _mapping().writeback_status == "done"


def test_expired_login_logs_in_again_once(institution, dspace, minting, secret_key):
    dspace.add(_item())
    dspace.patch_statuses = [401]

    _harvest(institution, secret_key)

    assert _mapping().writeback_status == "done"
    assert dspace.logins == 2


def test_login_works_after_an_anonymous_request_on_the_same_session(dspace):
    """DSpace stops sending the CSRF header once the session holds its cookie; login must use the cookie."""
    dspace.add(_item())
    writer = DSpaceClient(BASE, username="dspace-integration@africapidalliance.test", password="pw")
    assert writer.get_public_item_state(ITEM_UUID)[0] == "public"   # sets the CSRF cookie

    assert writer.add_identifier_uri(ITEM_UUID, "https://docid.africapidalliance.org/docid/x/y") == "added"
    assert dspace.logins == 1


def test_failed_listing_changes_nothing(institution, dspace, minting, secret_key):
    dspace.add(_item())
    _harvest(institution, secret_key)

    dspace.rsps.replace(responses.GET, DISCOVER, status=500)
    totals = _harvest(institution, secret_key)

    assert totals["errors"] == 1
    assert _mapping().dspace_status == "public"
    assert _mapping().publication.deleted_at is None
    assert "Harvest failed" in db.session.get(HarvestSourceCollection, institution["collection"].id).last_error_message


# ---------------------------------------------------------------- status check + DOCiD page

def test_record_restricted_later_is_tombstoned_then_restored(institution, dspace, minting, secret_key, client):
    dspace.add(_item())
    _harvest(institution, secret_key)
    docid = _mapping().publication.document_docid

    dspace.anonymous_state[ITEM_UUID] = "restricted"
    totals = _harvest(institution, secret_key)

    assert totals["status_changed"] == 1
    publication = _mapping().publication
    assert _mapping().dspace_status == "restricted"
    assert publication.deleted_at is not None and publication.deleted_by is None
    assert publication.deletion_reason == WITHHELD_REASONS["restricted"]

    page = client.get(f"/api/v1/publications/docid?docid={docid}").get_json()
    assert page["deleted"] is True
    assert page["repository_status"]["status"] == "restricted"
    assert page["repository_status"]["institution"] == "Test University"
    assert "document_title" not in page

    dspace.anonymous_state[ITEM_UUID] = "public"
    _harvest(institution, secret_key)

    assert _mapping().dspace_status == "public"
    assert _mapping().publication.deleted_at is None
    page = client.get(f"/api/v1/publications/docid?docid={docid}").get_json()
    assert page["document_title"] == "Seed-saving practices"
    assert page["repository_status"] is None


@pytest.mark.parametrize("change, expected_status", [
    ({"discoverable": False}, "private"),
    ({"anonymous_state": "deleted"}, "deleted"),
])
def test_hidden_or_deleted_records_are_tombstoned(institution, dspace, minting, secret_key, change, expected_status):
    dspace.add(_item())
    _harvest(institution, secret_key)

    if "anonymous_state" in change:
        dspace.anonymous_state[ITEM_UUID] = change["anonymous_state"]
    else:
        dspace.items[ITEM_UUID].update(change)
    _harvest(institution, secret_key)

    assert _mapping().dspace_status == expected_status
    assert _mapping().publication.deletion_reason == WITHHELD_REASONS[expected_status]


def test_withdrawn_record_keeps_metadata_with_status(institution, dspace, minting, secret_key, client):
    dspace.add(_item())
    _harvest(institution, secret_key)
    docid = _mapping().publication.document_docid

    dspace.items[ITEM_UUID]["withdrawn"] = True
    _harvest(institution, secret_key)

    assert _mapping().dspace_status == "withdrawn"
    assert _mapping().publication.deleted_at is None
    page = client.get(f"/api/v1/publications/docid?docid={docid}").get_json()
    assert page["document_title"] == "Seed-saving practices"
    assert page["repository_status"]["status"] == "withdrawn"
    assert page["repository_status"]["changed_at"]


def test_owner_retirement_is_never_lifted_by_status_check(institution, dspace, minting, secret_key):
    dspace.add(_item())
    _harvest(institution, secret_key)
    publication = _mapping().publication
    publication.deleted_at = publication.published
    publication.deleted_by = institution["owner_id"]
    publication.deletion_reason = "Duplicate record"
    db.session.commit()

    apply_dspace_status(_mapping(), "restricted")
    apply_dspace_status(_mapping(), "public")
    db.session.commit()

    publication = _mapping().publication
    assert publication.deleted_at is not None
    assert publication.deletion_reason == "Duplicate record"


def test_owner_cannot_restore_a_record_restricted_in_dspace(institution, dspace, minting, secret_key, client):
    dspace.add(_item())
    _harvest(institution, secret_key)
    dspace.anonymous_state[ITEM_UUID] = "restricted"
    _harvest(institution, secret_key)

    token = create_access_token(identity=str(institution["owner_id"]))
    response = client.post(f"/api/v1/publications/{_mapping().publication_id}/restore",
                           headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 409
    assert _mapping().publication.deleted_at is not None


# ---------------------------------------------------------------- every-minute change check

def _check(institution, secret_key):
    source = db.session.get(HarvestSource, institution["source"].id)
    return check_watched_collections_for_changes(source, secret_key)


def _collection(institution):
    return db.session.get(HarvestSourceCollection, institution["collection"].id)


def _new_item():
    return _item(uuid=NEW_UUID, handle=NEW_HANDLE, title="Rainmaking song", last_modified=_now_iso())


def test_change_check_harvests_new_record_links_it_back_and_records_the_run(
        institution, dspace, minting, secret_key):
    dspace.add(_item())
    _harvest(institution, secret_key)
    dspace.add(_new_item())
    dspace.add(_item(uuid=RESTRICTED_UUID, handle="123456789/1161", title="Restricted ceremony",
                     last_modified=_now_iso()), anonymous_state="restricted")

    harvest_repositories.check_all_sources_for_changes()

    mapping = DSpaceMapping.query.filter_by(dspace_uuid=NEW_UUID).one()
    assert mapping.publication.resource_type_id == institution["ik_type_id"]
    assert mapping.writeback_status == "done"
    assert len(dspace.calls("PATCH", NEW_UUID)) == 1
    assert DSpaceMapping.query.filter_by(dspace_uuid=RESTRICTED_UUID).first() is None
    run = EnrichmentRun.query.one()
    assert run.run_type == "harvest_changes" and run.publications_enriched == 1
    assert db.session.get(HarvestSource, institution["source"].id).total_items_synced == 1


def test_change_check_with_nothing_new_is_one_search_and_leaves_no_trace(
        institution, dspace, minting, secret_key, caplog):
    dspace.add(_item())
    _harvest(institution, secret_key)
    last_checked = _collection(institution).last_checked_at
    calls_before = len(dspace.rsps.calls)
    caplog.clear()

    with caplog.at_level(logging.INFO):
        harvest_repositories.check_all_sources_for_changes()

    new_calls = list(dspace.rsps.calls)[calls_before:]
    assert [call.request.method for call in new_calls] == ["GET"]
    since = (last_checked - CHANGE_CHECK_OVERLAP).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert parse_qs(urlparse(new_calls[0].request.url).query)["query"] == [f"lastModified:[{since} TO *]"]
    assert EnrichmentRun.query.count() == 0
    assert caplog.records == []
    assert _collection(institution).last_checked_at > last_checked


def test_change_check_leaves_a_collections_first_harvest_to_the_daily_pass(
        institution, dspace, minting, secret_key):
    dspace.add(_item(last_modified=_now_iso()))
    source = db.session.get(HarvestSource, institution["source"].id)
    source.last_harvested_at = datetime.utcnow()  # harvested before this collection was added
    db.session.commit()

    totals = _check(institution, secret_key)

    assert totals["created"] == 0
    assert dspace.calls("GET", "/discover/search/objects") == []
    assert harvest_repositories.is_due_for_harvest(source) is True


def test_failed_change_check_keeps_its_place_and_is_logged_once(
        institution, dspace, minting, secret_key, caplog):
    dspace.add(_item())
    _harvest(institution, secret_key)
    last_checked = _collection(institution).last_checked_at

    dspace.rsps.replace(responses.GET, DISCOVER, status=503)
    with caplog.at_level(logging.ERROR, logger="app.service_dspace_collections"):
        assert _check(institution, secret_key)["check_failures"] == 1
        assert _check(institution, secret_key)["check_failures"] == 1
    assert len([record for record in caplog.records
                if CHANGE_CHECK_ERROR_PREFIX in record.getMessage()]) == 1
    assert _collection(institution).last_checked_at == last_checked
    assert _collection(institution).last_error_message.startswith(CHANGE_CHECK_ERROR_PREFIX)

    dspace.rsps.remove(responses.GET, DISCOVER)
    dspace.rsps.add_callback(responses.GET, DISCOVER, callback=dspace._discover)
    _check(institution, secret_key)

    assert _collection(institution).last_error_message is None
    assert _collection(institution).last_checked_at > last_checked


def test_change_check_does_not_retry_old_write_back_failures(institution, dspace, minting, secret_key):
    dspace.add(_item())
    dspace.patch_statuses = [403]
    _harvest(institution, secret_key)
    dspace.add(_new_item())

    _check(institution, secret_key)

    assert len(dspace.calls("PATCH", ITEM_UUID)) == 1  # the daily pass's refused attempt only
    assert _mapping().writeback_status == "failed" and _mapping().writeback_attempts == 1
    assert DSpaceMapping.query.filter_by(dspace_uuid=NEW_UUID).one().writeback_status == "done"


def test_change_check_brings_back_a_record_made_public_again(institution, dspace, minting, secret_key):
    dspace.add(_item())
    _harvest(institution, secret_key)
    dspace.anonymous_state[ITEM_UUID] = "restricted"
    _harvest(institution, secret_key)
    assert _mapping().publication.deleted_at is not None

    dspace.anonymous_state[ITEM_UUID] = "public"
    dspace.items[ITEM_UUID]["lastModified"] = _now_iso()
    totals = _check(institution, secret_key)

    assert totals["status_changed"] == 1
    assert _mapping().dspace_status == "public"
    assert _mapping().publication.deleted_at is None


def test_change_check_skips_a_source_while_its_daily_pass_runs(institution, dspace, minting, secret_key):
    dspace.add(_item())
    _harvest(institution, secret_key)
    dspace.add(_new_item())

    with source_lock(institution["source"].id, wait=True):
        assert _check(institution, secret_key) is None
    assert DSpaceMapping.query.filter_by(dspace_uuid=NEW_UUID).first() is None

    assert _check(institution, secret_key)["created"] == 1


@pytest.mark.parametrize("frequency, last_harvested, now, due", [
    ("daily", datetime(2026, 11, 5, 2, 5), datetime(2026, 11, 6, 2, 0), True),
    ("daily", datetime(2026, 11, 6, 0, 30), datetime(2026, 11, 6, 23, 59), False),
    ("weekly", datetime(2026, 10, 31, 2, 5), datetime(2026, 11, 6, 2, 0), False),
    ("weekly", datetime(2026, 10, 30, 2, 5), datetime(2026, 11, 6, 2, 0), True),
])
def test_schedule_counts_calendar_days(frequency, last_harvested, now, due):
    source = HarvestSource(name="Schedule test", base_url=BASE, api_type="modern", owner_name="Test",
                           harvest_frequency=frequency, last_harvested_at=last_harvested)
    assert harvest_repositories.is_due_for_harvest(source, now=now) is due


# ---------------------------------------------------------------- admin API

@pytest.fixture
def admin_headers():
    admin = UserAccount(user_name="docid-admin", full_name="DOCiD Admin", email="admin@docid.test",
                        type="email", role="admin", password="unused")
    db.session.add(admin)
    db.session.commit()
    return {"Authorization": f"Bearer {create_access_token(identity=str(admin.user_id))}"}


def test_admin_adds_collection_by_handle_link(institution, admin_headers, client):
    other_uuid = "8a97b0dc-1dc0-4625-9d88-5c054da76cba"
    cultural_heritage = ResourceTypes(resource_type="Cultural Heritage")
    db.session.add(cultural_heritage)
    db.session.commit()
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, f"{API}/pid/find", json={
            "type": "collection", "uuid": other_uuid, "handle": "123456789/1150", "name": "Cultural Heritage",
        })
        response = client.post(
            f"/api/v1/admin/harvest-sources/{institution['source'].id}/collections",
            json={"collection": "https://repo.test/handle/123456789/1150/", "resource_type_id": cultural_heritage.id},
            headers=admin_headers,
        )
        assert rsps.calls[0].request.params == {"id": "123456789/1150"}

    assert response.status_code == 201
    body = response.get_json()
    assert body["dspace_collection_uuid"] == other_uuid
    assert body["collection_name"] == "Cultural Heritage"
    assert body["resource_type"] == "Cultural Heritage"
    assert body["write_back_enabled"] is True

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, f"{API}/pid/find", json={
            "type": "collection", "uuid": other_uuid, "handle": "123456789/1150", "name": "Cultural Heritage",
        })
        duplicate = client.post(
            f"/api/v1/admin/harvest-sources/{institution['source'].id}/collections",
            json={"collection": "123456789/1150", "resource_type_id": cultural_heritage.id},
            headers=admin_headers,
        )
    assert duplicate.status_code == 409


def test_admin_collection_link_that_is_not_a_collection_is_rejected(institution, admin_headers, client):
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, f"{API}/pid/find", json={"type": "item", "uuid": ITEM_UUID})
        response = client.post(
            f"/api/v1/admin/harvest-sources/{institution['source'].id}/collections",
            json={"collection": ITEM_HANDLE, "resource_type_id": institution["ik_type_id"]},
            headers=admin_headers,
        )
    assert response.status_code == 404


def test_collection_endpoints_require_admin(institution, client):
    user = db.session.get(UserAccount, institution["owner_id"])
    token = create_access_token(identity=str(user.user_id))
    response = client.get(f"/api/v1/admin/harvest-sources/{institution['source'].id}/collections",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_connection_check_records_whether_account_may_write(institution, secret_key):
    source = db.session.get(HarvestSource, institution["source"].id)
    collection = db.session.get(HarvestSourceCollection, institution["collection"].id)
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, DISCOVER, json=_listing(_item()))
        rsps.add(responses.GET, f"{API}/core/collections/{COLLECTION_UUID}",
                 json={"uuid": COLLECTION_UUID, "_links": {"self": {"href": f"{API}/core/collections/{COLLECTION_UUID}"}}})
        rsps.add(responses.GET, f"{API}/authn/status", headers={"DSPACE-XSRF-TOKEN": "csrf-1"}, json={})
        rsps.add(responses.POST, f"{API}/authn/login", headers={"Authorization": JWT})
        rsps.add(responses.GET, f"{API}/authz/authorizations/search/object",
                 json={"page": {"totalElements": 1}})

        report = check_collection_connection(source, collection, secret_key)

    assert report == {"listed_public_items": 1, "login_ok": True, "can_edit_metadata": True, "error": None}
    assert db.session.get(HarvestSourceCollection, institution["collection"].id).write_back_ok is True


def test_inconclusive_connection_check_keeps_previous_answer(institution, secret_key):
    collection = db.session.get(HarvestSourceCollection, institution["collection"].id)
    collection.write_back_ok = True
    db.session.commit()
    source = db.session.get(HarvestSource, institution["source"].id)
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, DISCOVER, json=_listing(_item()))
        rsps.add(responses.GET, f"{API}/core/collections/{COLLECTION_UUID}", status=503)
        report = check_collection_connection(source, collection, secret_key)

    assert report["error"].startswith("Permission check failed")
    assert db.session.get(HarvestSourceCollection, institution["collection"].id).write_back_ok is True


def test_listing_falls_back_when_site_has_no_accessioned_sort():
    client = DSpaceClient(BASE)
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, DISCOVER, status=400,
                 match=[responses.matchers.query_param_matcher({"sort": "dc.date.accessioned,ASC"}, strict_match=False)])
        rsps.add(responses.GET, DISCOVER, json=_listing(_item()))
        items = client.list_public_collection_items(COLLECTION_UUID)
        assert "sort" not in rsps.calls[1].request.params
    assert [item["uuid"] for item in items] == [ITEM_UUID]


def test_find_collection_accepts_uuid_links_without_lookup_by_handle():
    client = DSpaceClient(BASE)
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, f"{API}/core/collections/{COLLECTION_UUID}",
                 json={"type": "collection", "uuid": COLLECTION_UUID, "name": "Indigenous Knowledge"})
        found = client.find_collection(f"https://repo.test/collections/{COLLECTION_UUID}?tab=browse")
    assert found["uuid"] == COLLECTION_UUID
