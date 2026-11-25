"""backfill_publication_dates.py: reads each record's date from its source, dry run by default."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

import backfill_publication_dates as backfill_module
from backfill_publication_dates import (
    ERROR, NEEDS_UON_DIR, NO_DATE_AT_SOURCE, NOT_FOUND, REPOSITORY_UNREACHABLE, SET, UNKNOWN_REPOSITORY, WOULD_SET,
    RepositoryResolver, SourceReader, backfill,
)
from app import db
from app.models import DSpaceMapping, HarvestSource, HarvestSourceCollection, Publications, ResourceTypes, UserAccount


def _owner():
    user = UserAccount(user_name="backfill-owner", full_name="Backfill Owner", email="backfill@example.test",
                       type="email", role="user", password="unused")
    db.session.add(user)
    db.session.commit()
    return user.user_id


def _resource_type_id():
    resource_type = ResourceTypes.query.first()
    if resource_type is None:
        resource_type = ResourceTypes(resource_type="dataset")
        db.session.add(resource_type)
        db.session.flush()
    return resource_type.id


def _publication(owner_id, number, **fields):
    publication = Publications(user_id=owner_id, document_docid=f"20.500.14351/backfill{number:04d}",
                               document_title=f"Backfill {number}", document_description="fixture",
                               resource_type_id=_resource_type_id(), **fields)
    db.session.add(publication)
    db.session.flush()
    return publication


def _mapping(publication, uuid, dspace_url, collection=None):
    mapping = DSpaceMapping(dspace_handle=f"123/{uuid}", dspace_uuid=uuid, dspace_url=dspace_url,
                            publication_id=publication.id, harvest_source_collection=collection)
    db.session.add(mapping)
    db.session.flush()
    return mapping


def _source(name, base_url, api_type="modern", ui_base_url=None):
    source = HarvestSource(name=name, base_url=base_url, ui_base_url=ui_base_url, api_type=api_type, owner_name=name)
    db.session.add(source)
    db.session.flush()
    return source


class FakeReader:
    """Stands in for SourceReader: answers by publication id."""

    def __init__(self, answers, unreachable=()):
        self.answers = answers  # publication id -> raw date, or an exception to raise
        self.unreachable = set(unreachable)  # base URLs that are down
        self.dspace_calls = []

    def repository_reachable(self, api_type, base_url):
        return base_url not in self.unreachable

    def _answer(self, publication_id):
        answer = self.answers[publication_id]
        if isinstance(answer, Exception):
            raise answer
        return answer

    def dspace_date(self, api_type, base_url, mapping, user_id):
        self.dspace_calls.append((api_type, base_url, mapping.dspace_uuid))
        return self._answer(mapping.publication_id)

    def uon_date(self, mapping, user_id):
        return self._answer(mapping.publication_id)

    def figshare_date(self, publication):
        return self._answer(publication.id)

    def ojs_date(self, publication):
        return self._answer(publication.id)


def _quiet(*_args):
    pass


def test_resolver_finds_the_repository_for_each_kind_of_mapping():
    owner_id = _owner()
    unilag = _source("UNILAG", "https://api-ir.unilag.edu.ng/server", ui_base_url="https://ir.unilag.edu.ng")
    legacy = _source("Stellenbosch", "https://scholar.sun.ac.za", api_type="legacy")
    collection = HarvestSourceCollection(harvest_source_id=unilag.id, dspace_collection_uuid="c-1",
                                         resource_type_id=_resource_type_id())
    db.session.add(collection)
    db.session.flush()

    by_collection = _mapping(_publication(owner_id, 1), "u-1", "https://elsewhere.example/handle/1", collection)
    by_ui_host = _mapping(_publication(owner_id, 2), "u-2", "https://ir.unilag.edu.ng/handle/123/2")
    by_legacy_host = _mapping(_publication(owner_id, 3), "legacy-item-77", "https://scholar.sun.ac.za/handle/10019/3")
    by_env = _mapping(_publication(owner_id, 4), "u-4", "https://dspace.example/server")
    uon = _mapping(_publication(owner_id, 5), "u-5", "https://erepository.uonbi.ac.ke/items/u-5")
    unknown = _mapping(_publication(owner_id, 6), "u-6", "https://unknown.example/handle/6")

    resolver = RepositoryResolver(HarvestSource.query.all(), env_modern_url="https://dspace.example/server/")
    assert resolver.resolve(by_collection) == ("modern", "https://api-ir.unilag.edu.ng/server")
    assert resolver.resolve(by_ui_host) == ("modern", "https://api-ir.unilag.edu.ng/server")
    assert resolver.resolve(by_legacy_host) == ("legacy", "https://scholar.sun.ac.za")
    assert resolver.resolve(by_env) == ("modern", "https://dspace.example/server")
    assert resolver.resolve(uon) == ("uon", None)
    assert resolver.resolve(unknown) is None


def test_dry_run_reports_but_writes_nothing():
    owner_id = _owner()
    publication = _publication(owner_id, 10, figshare_article_id="555")
    db.session.commit()

    outcomes = backfill(apply=False, sources=("figshare",), reader=FakeReader({publication.id: "2019-05-14T10:00:00Z"}),
                        resolver=RepositoryResolver([]), log=_quiet)

    assert outcomes[("figshare", WOULD_SET)] == 1
    db.session.expire_all()
    assert db.session.get(Publications, publication.id).publication_date is None


def test_apply_sets_dates_at_their_precision_and_counts_every_outcome():
    owner_id = _owner()
    _source("UNILAG", "https://api-ir.unilag.edu.ng/server", ui_base_url="https://ir.unilag.edu.ng")
    year_only = _publication(owner_id, 20)
    _mapping(year_only, "u-20", "https://ir.unilag.edu.ng/handle/123/20")
    no_date = _publication(owner_id, 21)
    _mapping(no_date, "u-21", "https://ir.unilag.edu.ng/handle/123/21")
    gone = _publication(owner_id, 22)
    _mapping(gone, "u-22", "https://ir.unilag.edu.ng/handle/123/22")
    broken = _publication(owner_id, 23)
    _mapping(broken, "u-23", "https://ir.unilag.edu.ng/handle/123/23")
    unidentified = _publication(owner_id, 24)
    _mapping(unidentified, "u-24", None)
    already_dated = _publication(owner_id, 25, publication_date=date(2001, 1, 1), publication_date_precision="year")
    _mapping(already_dated, "u-25", "https://ir.unilag.edu.ng/handle/123/25")
    retired = _publication(owner_id, 26)
    retired.deleted_at = retired.published
    _mapping(retired, "u-26", "https://ir.unilag.edu.ng/handle/123/26")
    db.session.commit()

    reader = FakeReader({year_only.id: "2019", no_date.id: None, gone.id: LookupError("u-22"),
                         broken.id: ValueError("bad payload")})
    outcomes = backfill(apply=True, sources=("dspace",), reader=reader,
                        resolver=RepositoryResolver(HarvestSource.query.all()), log=_quiet)

    assert outcomes[("dspace", SET)] == 1
    assert outcomes[("dspace", NO_DATE_AT_SOURCE)] == 1
    assert outcomes[("dspace", NOT_FOUND)] == 1
    assert outcomes[("dspace", ERROR)] == 1
    assert outcomes[("dspace", UNKNOWN_REPOSITORY)] == 1
    # The dated and the retired records are never even fetched.
    assert {uuid for (_, _, uuid) in reader.dspace_calls} == {"u-20", "u-21", "u-22", "u-23"}

    db.session.expire_all()
    dated = db.session.get(Publications, year_only.id)
    assert (dated.publication_date, dated.publication_date_precision) == (date(2019, 1, 1), "year")
    assert db.session.get(Publications, already_dated.id).publication_date == date(2001, 1, 1)


def test_an_unreachable_repository_is_skipped_without_fetching_its_items():
    owner_id = _owner()
    _source("UNILAG", "https://api-ir.unilag.edu.ng/server", ui_base_url="https://ir.unilag.edu.ng")
    _source("Other", "https://repo.example/server")
    down = [_publication(owner_id, 50 + n) for n in range(3)]
    for n, publication in enumerate(down):
        _mapping(publication, f"u-down-{n}", f"https://ir.unilag.edu.ng/handle/123/{n}")
    up = _publication(owner_id, 60)
    _mapping(up, "u-up", "https://repo.example/handle/1/1")
    db.session.commit()

    reader = FakeReader({up.id: "2017"}, unreachable={"https://api-ir.unilag.edu.ng/server"})
    with patch.object(backfill_module.time, "sleep") as sleep:
        outcomes = backfill(apply=False, sources=("dspace",), delay_seconds=0.2, reader=reader,
                            resolver=RepositoryResolver(HarvestSource.query.all()), log=_quiet)

    assert outcomes[("dspace", REPOSITORY_UNREACHABLE)] == 3
    assert outcomes[("dspace", WOULD_SET)] == 1
    assert [uuid for (_, _, uuid) in reader.dspace_calls] == ["u-up"]  # no item requests to the dead host
    assert sleep.call_count == 1  # only after the one real request


def test_reachability_is_checked_once_per_repository():
    import requests

    messages = []
    reader = SourceReader(log=messages.append)
    calls = []

    def failing_get(url, timeout):
        calls.append(url)
        raise requests.exceptions.ConnectionError("Name or service not known")

    reader._dspace_clients[("modern", "https://down.example/server")] = SimpleNamespace(session=SimpleNamespace(get=failing_get))
    reader._dspace_clients[("legacy", "https://up.example")] = SimpleNamespace(
        session=SimpleNamespace(get=lambda url, timeout: calls.append(url) or SimpleNamespace(status_code=200)))

    assert reader.repository_reachable("modern", "https://down.example/server") is False
    assert reader.repository_reachable("modern", "https://down.example/server") is False
    assert reader.repository_reachable("legacy", "https://up.example") is True
    assert calls == ["https://down.example/server/api", "https://up.example/rest/status"]
    assert len(messages) == 1 and "https://down.example/server is unreachable" in messages[0]


def test_uon_records_need_the_excel_folder():
    owner_id = _owner()
    publication = _publication(owner_id, 30)
    _mapping(publication, "u-30", "https://erepository.uonbi.ac.ke/items/u-30")
    db.session.commit()
    reader = FakeReader({publication.id: "2016-03"})

    without_dir = backfill(apply=True, sources=("uon",), reader=reader, resolver=RepositoryResolver([]), log=_quiet)
    assert without_dir[("uon", NEEDS_UON_DIR)] == 1

    with_dir = backfill(apply=True, sources=("uon",), uon_source_dir="/exports", reader=reader,
                        resolver=RepositoryResolver([]), log=_quiet)
    assert with_dir[("uon", SET)] == 1
    db.session.expire_all()
    assert db.session.get(Publications, publication.id).publication_date_precision == "month"


def test_uon_records_are_not_counted_as_dspace():
    owner_id = _owner()
    publication = _publication(owner_id, 31)
    _mapping(publication, "u-31", "https://erepository.uonbi.ac.ke/items/u-31")
    db.session.commit()
    outcomes = backfill(apply=False, sources=("dspace",), reader=FakeReader({}), resolver=RepositoryResolver([]), log=_quiet)
    assert sum(outcomes.values()) == 0


def test_repush_cordra_is_opt_in_and_only_requeues_records_already_in_cordra():
    owner_id = _owner()
    in_cordra = _publication(owner_id, 40, ojs_submission_id="7", cordra_synced=True)
    not_yet_pushed = _publication(owner_id, 41, ojs_submission_id="8", cordra_synced=False)
    left_alone = _publication(owner_id, 42, ojs_submission_id="9", cordra_synced=True)
    db.session.commit()
    answers = {in_cordra.id: "2020-01-02", not_yet_pushed.id: "2020-01-03", left_alone.id: "2020-01-04"}

    backfill(apply=True, sources=("ojs",), publication_id=left_alone.id, reader=FakeReader(answers),
             resolver=RepositoryResolver([]), log=_quiet)
    backfill(apply=True, sources=("ojs",), repush_cordra=True, reader=FakeReader(answers),
             resolver=RepositoryResolver([]), log=_quiet)

    db.session.expire_all()
    assert db.session.get(Publications, in_cordra.id).cordra_synced is False
    assert db.session.get(Publications, not_yet_pushed.id).cordra_synced is False
    assert db.session.get(Publications, left_alone.id).cordra_synced is True  # dated without --repush-cordra


# --- The real readers use the importers' own mappers ------------------------

def test_reader_reads_dc_date_issued_from_dspace7_and_legacy_items():
    reader = SourceReader()
    modern_client = SimpleNamespace(get_item=lambda uuid: {
        "uuid": uuid, "handle": "123/1", "metadata": {"dc.title": [{"value": "T"}], "dc.date.issued": [{"value": "2019-05"}]}})
    legacy_client = SimpleNamespace(get_item=lambda item_id: {
        "uuid": None, "id": item_id, "handle": "10019/1",
        "metadata": [{"key": "dc.title", "value": "T"}, {"key": "dc.date.issued", "value": "2008"}]} if item_id == "77" else None)
    reader._dspace_clients[("modern", "https://modern.example/server")] = modern_client
    reader._dspace_clients[("legacy", "https://legacy.example")] = legacy_client

    modern_mapping = SimpleNamespace(dspace_uuid="u-1")
    legacy_mapping = SimpleNamespace(dspace_uuid="legacy-item-77")
    assert reader.dspace_date("modern", "https://modern.example/server", modern_mapping, 1) == "2019-05"
    assert reader.dspace_date("legacy", "https://legacy.example", legacy_mapping, 1) == "2008"


def test_reader_reads_figshare_and_ojs_dates():
    reader = SourceReader()
    figshare_client = SimpleNamespace(get_article=lambda article_id: {
        "id": article_id, "title": "T", "description": "", "published_date": "2021-07-01T09:00:00Z", "authors": []})
    ojs_client = SimpleNamespace(get_submission=lambda submission_id: {
        "id": submission_id, "publications": [{"title": {"en_US": "T"}, "datePublished": "2018-11-30", "authors": []}]})
    publication = SimpleNamespace(id=1, user_id=1, figshare_article_id="9", ojs_submission_id="5")

    with patch("app.routes.figshare.get_figshare_client", return_value=figshare_client), \
            patch("app.routes.ojs.get_ojs_client", return_value=ojs_client):
        assert reader.figshare_date(publication) == "2021-07-01T09:00:00Z"
        assert reader.ojs_date(publication) == "2018-11-30"


def test_reader_reads_uon_dates_from_the_excel_exports(tmp_path):
    import openpyxl

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["id", "collection", "dc.title[en]", "dc.date.issued", "dc.date.issued[]"])
    sheet.append(["u-uon-1", "11295/1", "A UoN thesis", None, "2014"])  # value sits in a language-qualified column
    workbook.save(tmp_path / "Traditional Knowledge (Theses) search-results.xlsx")

    reader = SourceReader(uon_source_dir=str(tmp_path))
    assert reader.uon_date(SimpleNamespace(dspace_uuid="u-uon-1"), 1) == "2014"
    try:
        reader.uon_date(SimpleNamespace(dspace_uuid="not-in-the-exports"), 1)
        raise AssertionError("expected LookupError")
    except LookupError:
        pass


def test_cli_rejects_repush_without_apply(capsys):
    with patch("sys.argv", ["backfill_publication_dates.py", "--repush-cordra"]):
        try:
            backfill_module.main()
        except SystemExit as exit_signal:
            assert exit_signal.code == 2
    assert "--repush-cordra needs --apply" in capsys.readouterr().err


def test_an_empty_fetch_is_retried_once():
    answers = iter([None, {"found": True}])
    with patch.object(backfill_module.time, "sleep") as sleep:
        assert backfill_module.fetch_with_one_retry(lambda item_id: next(answers), "x") == {"found": True}
    assert sleep.call_count == 1

    calls = []
    with patch.object(backfill_module.time, "sleep"):
        assert backfill_module.fetch_with_one_retry(lambda item_id: calls.append(item_id), "missing") is None
    assert calls == ["missing", "missing"]  # exactly one retry, then give up
