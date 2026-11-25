#!/usr/bin/env python3
"""
Backfill publications.publication_date for records imported before the column existed.

Each record's date is read again from where it came from, through the same mapper
its importer uses, so a backfilled date is exactly what a fresh import would store:

  dspace    DSpace 7 or legacy DSpace item (dc.date.issued, else dc.date.created),
            fetched anonymously
  uon       University of Nairobi Excel exports (same DSpace fields); UoN records were
            imported offline, so pass the folder with --uon-source-dir
  figshare  Figshare article (published_date)
  ojs       OJS submission (datePublished)

Only records with no publication_date are touched, so a manual date is never
overwritten and a rerun carries on where the last one stopped. Records with no
source (created in the DOCiD form, Abukutsa ingest) stay empty.

Dry run by default: nothing is written until --apply is given.

Usage (from backend/):
    python backfill_publication_dates.py                      # dry run, all sources
    python backfill_publication_dates.py --source figshare --limit 20
    python backfill_publication_dates.py --uon-source-dir /path/to/uon-xlsx
    python backfill_publication_dates.py --apply              # write the dates
    python backfill_publication_dates.py --apply --repush-cordra
        # also queue the dated records for the every-minute Cordra cron
        # (push_recent_to_cordra.py, 10 per minute) by clearing cordra_synced
"""

import argparse
import os
import sys
import time
from collections import Counter
from urllib.parse import urlsplit

from sqlalchemy import or_

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import DSpaceMapping, HarvestSource, Publications
from app.utils.publication_dates import (
    format_publication_date,
    parse_source_publication_date,
)

SOURCES = ('dspace', 'uon', 'figshare', 'ojs')
COMMIT_EVERY = 50
RETRY_PAUSE_SECONDS = 3
UON_ITEM_URL_PREFIX = 'https://erepository.uonbi.ac.ke/items/'
LEGACY_ITEM_PREFIX = 'legacy-item-'

# Outcomes counted in the summary.
WOULD_SET = 'would set'
SET = 'set'
NO_DATE_AT_SOURCE = 'source has no usable date'
NOT_FOUND = 'not found at source (removed, restricted or unreachable)'
REPOSITORY_UNREACHABLE = 'repository unreachable (its records were skipped)'
UNKNOWN_REPOSITORY = 'repository not identified'
NEEDS_UON_DIR = 'UoN record, --uon-source-dir not given'
ERROR = 'error'


def _host(url):
    return urlsplit(url or '').netloc.lower()


class RepositoryResolver:
    """Works out which DSpace instance (and API style) a mapping's item lives in."""

    def __init__(self, harvest_sources, env_modern_url=None, env_legacy_url=None):
        self.sources_by_host = {}
        for source in harvest_sources:
            if source.api_type not in ('modern', 'legacy'):
                continue
            for url in (source.base_url, source.ui_base_url):
                if _host(url):
                    self.sources_by_host.setdefault(_host(url), source)
        self.env_modern_url = (env_modern_url or '').rstrip('/')
        self.env_legacy_url = (env_legacy_url or '').rstrip('/')

    def resolve(self, mapping):
        """('modern'|'legacy', api base URL), ('uon', None) or None when unknown."""
        dspace_url = (mapping.dspace_url or '').rstrip('/')
        if dspace_url.startswith(UON_ITEM_URL_PREFIX.rstrip('/')):
            return 'uon', None
        collection = mapping.harvest_source_collection
        if collection is not None and collection.source is not None:
            return collection.source.api_type, collection.source.base_url
        source = self.sources_by_host.get(_host(dspace_url))
        if source is not None:
            return source.api_type, source.base_url
        # Records imported through the /dspace and /dspace-legacy routes store the
        # instance URL from the environment.
        if self.env_modern_url and dspace_url == self.env_modern_url:
            return 'modern', self.env_modern_url
        if self.env_legacy_url and dspace_url == self.env_legacy_url:
            return 'legacy', self.env_legacy_url
        return None


def fetch_with_one_retry(fetch, *args):
    """
    Call a client fetch, and once more after a short pause if it comes back empty.

    The clients return None both for a missing record and for a dropped connection
    (e.g. "Remote end closed connection without response"), so one retry stops a
    momentary server hiccup from being counted as "not found".
    """
    result = fetch(*args)
    if not result:
        time.sleep(RETRY_PAUSE_SECONDS)
        result = fetch(*args)
    return result


class SourceReader:
    """Fetches one record from its source and returns the raw publication date."""

    def __init__(self, uon_source_dir=None, log=print):
        self._dspace_clients = {}
        self._reachable = {}
        self._log = log
        self._uon_items = None
        self._uon_source_dir = uon_source_dir
        self._figshare_client = None
        self._ojs_client = None

    def repository_reachable(self, api_type, base_url):
        """
        Whether a DSpace instance answers at all, checked once per instance.

        When its DNS or server is down, every item request would retry and wait
        in turn, so the whole repository is skipped after one failed check.
        """
        key = (api_type, base_url)
        if key not in self._reachable:
            probe_url = f"{base_url.rstrip('/')}/rest/status" if api_type == 'legacy' else f"{base_url.rstrip('/')}/api"
            try:
                response = self._dspace_client(api_type, base_url).session.get(probe_url, timeout=15)
                reachable = response.status_code < 500
                reason = f"HTTP {response.status_code}"
            except Exception as error:
                reachable, reason = False, f"{type(error).__name__}: {error}"
            self._reachable[key] = reachable
            if not reachable:
                self._log(f"  repository {base_url} is unreachable ({reason[:200]}); skipping its records")
        return self._reachable[key]

    def _dspace_client(self, api_type, base_url):
        key = (api_type, base_url)
        if key not in self._dspace_clients:
            if api_type == 'legacy':
                from app.service_dspace_legacy import DSpaceLegacyClient
                self._dspace_clients[key] = DSpaceLegacyClient(base_url)
            else:
                from app.service_dspace import DSpaceClient
                self._dspace_clients[key] = DSpaceClient(base_url)
        return self._dspace_clients[key]

    def dspace_date(self, api_type, base_url, mapping, user_id):
        """Raw dc.date.issued; raises LookupError when the item can't be fetched."""
        client = self._dspace_client(api_type, base_url)
        if api_type == 'legacy':
            from app.service_dspace_legacy import DSpaceLegacyMetadataMapper
            item_id = mapping.dspace_uuid
            if item_id.startswith(LEGACY_ITEM_PREFIX):
                item_id = item_id[len(LEGACY_ITEM_PREFIX):]
            item = fetch_with_one_retry(client.get_item, item_id)
            if not item:
                raise LookupError(item_id)
            return DSpaceLegacyMetadataMapper.dspace_to_docid(item, user_id)['publication'].get('publication_date')
        from app.service_dspace import DSpaceMetadataMapper
        item = fetch_with_one_retry(client.get_item, mapping.dspace_uuid)
        if not item:
            raise LookupError(mapping.dspace_uuid)
        return DSpaceMetadataMapper.dspace_to_docid(item, user_id)['publication'].get('publication_date')

    def uon_date(self, mapping, user_id):
        """Raw dc.date.issued from the UoN Excel exports; raises LookupError when absent."""
        from app.service_dspace import DSpaceMetadataMapper
        from import_uon_excel import build_dspace_item, read_curated_items
        if self._uon_items is None:
            self._uon_items = read_curated_items(self._uon_source_dir)
        record = self._uon_items.get(mapping.dspace_uuid)
        if record is None:
            raise LookupError(mapping.dspace_uuid)
        item = build_dspace_item(record)
        return DSpaceMetadataMapper.dspace_to_docid(item, user_id)['publication'].get('publication_date')

    def figshare_date(self, publication):
        from app.routes.figshare import get_figshare_client
        from app.service_figshare import FigshareMetadataMapper
        if self._figshare_client is None:
            self._figshare_client = get_figshare_client()
        article = fetch_with_one_retry(self._figshare_client.get_article, int(publication.figshare_article_id))
        if not article:
            raise LookupError(publication.figshare_article_id)
        return FigshareMetadataMapper.figshare_to_docid(article, publication.user_id)['publication'].get('publication_date')

    def ojs_date(self, publication):
        from app.routes.ojs import get_ojs_client
        from app.service_ojs import OJSMetadataMapper
        if self._ojs_client is None:
            self._ojs_client = get_ojs_client()
        submission = fetch_with_one_retry(self._ojs_client.get_submission, int(publication.ojs_submission_id))
        if not submission:
            raise LookupError(publication.ojs_submission_id)
        return OJSMetadataMapper.ojs_to_docid(submission, publication.user_id)['publication'].get('publication_date')


def candidate_query(source, publication_id=None):
    """Live records of one source that have no publication date yet."""
    query = Publications.query.filter(
        Publications.publication_date.is_(None),
        Publications.deleted_at.is_(None),
    )
    if publication_id is not None:
        query = query.filter(Publications.id == publication_id)
    if source in ('dspace', 'uon'):
        is_uon = DSpaceMapping.dspace_url.like(UON_ITEM_URL_PREFIX + '%')
        query = query.join(DSpaceMapping, DSpaceMapping.publication_id == Publications.id)
        # NOT LIKE is unknown for a NULL url, so keep those explicitly (reported as unidentified).
        query = query.filter(is_uon if source == 'uon' else or_(DSpaceMapping.dspace_url.is_(None), ~is_uon))
    elif source == 'figshare':
        query = query.filter(Publications.figshare_article_id.isnot(None))
    elif source == 'ojs':
        query = query.filter(Publications.ojs_submission_id.isnot(None))
    return query.order_by(Publications.id)


def read_raw_date(source, publication, reader, resolver, uon_source_dir):
    """(raw date or None, outcome or None). Outcome is set when no date could be read."""
    if source == 'figshare':
        return reader.figshare_date(publication), None
    if source == 'ojs':
        return reader.ojs_date(publication), None
    mapping = publication.dspace_mapping
    if source == 'uon':
        if not uon_source_dir:
            return None, NEEDS_UON_DIR
        return reader.uon_date(mapping, publication.user_id), None
    resolved = resolver.resolve(mapping)
    if resolved is None:
        return None, UNKNOWN_REPOSITORY
    api_type, base_url = resolved
    if not reader.repository_reachable(api_type, base_url):
        return None, REPOSITORY_UNREACHABLE
    return reader.dspace_date(api_type, base_url, mapping, publication.user_id), None


def backfill(apply=False, sources=SOURCES, limit=None, publication_id=None,
             uon_source_dir=None, repush_cordra=False, delay_seconds=0.0,
             reader=None, resolver=None, log=print):
    """Run the backfill; returns a Counter of outcomes per source, e.g. {('dspace', 'set'): 12}."""
    reader = reader or SourceReader(uon_source_dir, log=log)
    if resolver is None:
        from app.routes.dspace import DSPACE_BASE_URL
        from app.routes.dspace_legacy import DSPACE_LEGACY_URL
        resolver = RepositoryResolver(HarvestSource.query.all(), DSPACE_BASE_URL, DSPACE_LEGACY_URL)

    outcomes = Counter()
    pending_writes = 0
    for source in sources:
        query = candidate_query(source, publication_id)
        if limit:
            query = query.limit(limit)
        publications = query.all()
        log(f"[{source}] {len(publications)} record(s) without a publication date")

        for publication in publications:
            try:
                raw_date, outcome = read_raw_date(source, publication, reader, resolver, uon_source_dir)
            except LookupError:
                raw_date, outcome = None, NOT_FOUND
            except Exception as error:  # one bad record must not stop the run
                raw_date, outcome = None, ERROR
                log(f"  publication {publication.id}: {type(error).__name__}: {error}")
            # Wait only after a real remote request, not after a record that was skipped.
            if delay_seconds and source != 'uon' and outcome not in (
                    REPOSITORY_UNREACHABLE, UNKNOWN_REPOSITORY, NEEDS_UON_DIR):
                time.sleep(delay_seconds)

            if outcome is None:
                value, precision = parse_source_publication_date(raw_date)
                if value is None:
                    outcome = NO_DATE_AT_SOURCE
                else:
                    shown = format_publication_date(value, precision)
                    if apply:
                        publication.publication_date = value
                        publication.publication_date_precision = precision
                        if repush_cordra and publication.cordra_synced:
                            publication.cordra_synced = False
                        pending_writes += 1
                        outcome = SET
                    else:
                        outcome = WOULD_SET
                    log(f"  publication {publication.id}: {shown!r} (source value {raw_date!r})")
            outcomes[(source, outcome)] += 1

            if apply and pending_writes >= COMMIT_EVERY:
                db.session.commit()
                pending_writes = 0

    if apply and pending_writes:
        db.session.commit()
    return outcomes


def print_summary(outcomes, apply, log=print):
    log("")
    log("Summary" + ("" if apply else " (dry run, nothing written; rerun with --apply)"))
    for source in SOURCES:
        rows = [(outcome, count) for (row_source, outcome), count in sorted(outcomes.items()) if row_source == source]
        if rows:
            log(f"  {source}: " + ", ".join(f"{outcome}: {count}" for outcome, count in rows))


def main():
    parser = argparse.ArgumentParser(description='Backfill publication_date from each record\'s source')
    parser.add_argument('--apply', action='store_true', help='Write the dates (default is a dry run)')
    parser.add_argument('--source', choices=SOURCES + ('all',), default='all')
    parser.add_argument('--limit', type=int, help='At most N records per source')
    parser.add_argument('--publication-id', type=int, help='Only this publication')
    parser.add_argument('--uon-source-dir', help='Folder with the UoN *.xlsx exports')
    parser.add_argument('--repush-cordra', action='store_true',
                        help='With --apply: clear cordra_synced on dated records so the Cordra cron re-pushes them')
    parser.add_argument('--delay', type=float, default=0.2,
                        help='Seconds to wait between remote requests (default 0.2)')
    args = parser.parse_args()
    if args.repush_cordra and not args.apply:
        parser.error('--repush-cordra needs --apply')

    sources = SOURCES if args.source == 'all' else (args.source,)
    app = create_app()
    with app.app_context():
        outcomes = backfill(
            apply=args.apply, sources=sources, limit=args.limit,
            publication_id=args.publication_id, uon_source_dir=args.uon_source_dir,
            repush_cordra=args.repush_cordra, delay_seconds=args.delay,
        )
    print_summary(outcomes, args.apply)
    return 1 if any(outcome == ERROR for (_, outcome) in outcomes) else 0


if __name__ == '__main__':
    sys.exit(main())
