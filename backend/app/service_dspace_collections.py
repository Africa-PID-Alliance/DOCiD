"""
Watched-collection integration with institutional DSpace repositories.

An institution gives DOCiD one DSpace account that is Administrator of the
collections DOCiD watches (for example Indigenous Knowledge and Cultural
Heritage). Once a day, for each watched collection, DOCiD:

1. Lists the collection as an anonymous visitor. DSpace leaves out restricted,
   private and withdrawn items, so DOCiD never sees what the public cannot.
2. Harvests records it has not seen, typed by the collection, and mints a DOCiD.
3. Checks records it holds that dropped out of the list, and tombstones the
   ones DSpace now restricts, hides or has deleted (no metadata on DOCiD).
4. Logs in and appends the DOCiD URL to each new record's dc.identifier.uri,
   retrying failures on later runs.

Every minute, a lighter check asks each collection only for records changed
since the last pass, so new records get their DOCiD and link within a minute
(check_watched_collections_for_changes). Hiding records that DSpace restricts
stays with the daily pass: they drop out of the public view, so no "what
changed" query can show them.

The design, with the requests verified against DSpace 10.2, is in the
"Life of a DSpace record: DOCiD link-back" document.
"""
import fcntl
import json
import logging
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
from cryptography.fernet import InvalidToken
from flask import current_app

from app import db
from app.models import (
    DSPACE_WITHHELD_STATUSES,
    CreatorsRoles,
    DSpaceMapping,
    PublicationAuditTrail,
    PublicationCreators,
    Publications,
)
from app.service_dspace import DSpaceAuthError, DSpaceClient, DSpaceMetadataMapper, DSpaceWriteError
from app.service_identifiers import IdentifierService
from app.service_thumbnails import generate_thumbnail_from_url, get_uploads_dir
from app.utils_crypto import decrypt_value

logger = logging.getLogger(__name__)

# Shown on the DOCiD tombstone. Also how DOCiD recognises a tombstone it set
# itself (deleted_by is None and the reason is one of these), so it never
# undoes a retirement made by the record's owner.
WITHHELD_REASONS = {
    'restricted': 'The holding institution has restricted this record in its repository.',
    'private': 'The holding institution has hidden this record in its repository.',
    'deleted': 'The holding institution has removed this record from its repository.',
}

# Write-back gives up and waits for an admin after this many failed attempts.
MAX_WRITEBACK_ATTEMPTS = 5

RETRYABLE_WRITEBACK_STATUSES = ('waiting_for_docid', 'pending', 'failed')

# The every-minute check looks back this far past the last pass, so a record
# DSpace indexes a moment late, or a small clock difference between DOCiD and
# DSpace, is not missed. Anything still missed is picked up by the daily pass.
CHANGE_CHECK_OVERLAP = timedelta(minutes=2)

# Marks last_error_message as written by the every-minute check, so it is
# logged once when checks start failing and cleared when they work again.
CHANGE_CHECK_ERROR_PREFIX = 'Change check failed: '

# Where the per-source harvest locks live (see source_lock).
SOURCE_LOCK_DIR = tempfile.gettempdir()


@contextmanager
def source_lock(source_id: int, wait: bool):
    """
    Hold one source's harvest lock for the duration of the block.

    The daily pass and the every-minute check both harvest new records, and
    each runs in its own cron process; holding this lock stops them from
    harvesting, and minting a DOCiD for, the same record twice. Yields True
    once held, or False straight away when wait is False and another process
    holds it. The operating system releases it if the process dies.
    """
    path = os.path.join(SOURCE_LOCK_DIR, f"docid_dspace_source_{source_id}.lock")
    with open(path, 'a') as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX if wait else fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def docid_landing_url(document_docid: str) -> str:
    """Public landing-page URL for a DOCiD, the value written into DSpace."""
    origin = (current_app.config.get('DOCID_SITE_ORIGIN') or 'https://docid.africapidalliance.org').rstrip('/')
    return f"{origin}/docid/{document_docid.strip('/')}"


def repository_ui_base(source) -> str:
    """The institution's public site, for links to the DSpace item."""
    return source.ui_base_url or source.base_url.replace('/server', '').replace('/rest', '')


def make_reader(source) -> DSpaceClient:
    """A client that never logs in. Every harvest read goes through this."""
    return DSpaceClient(source.base_url)


def make_writer(source, secret_key: str) -> Optional[DSpaceClient]:
    """A client with the institution's DOCiD account, used only to write back. None without usable credentials."""
    if not (source.encrypted_username and source.encrypted_password):
        return None
    try:
        username = decrypt_value(source.encrypted_username, secret_key)
        password = decrypt_value(source.encrypted_password, secret_key)
    except (InvalidToken, ValueError) as decrypt_error:
        logger.error(f"[{source.name}] Cannot decrypt DSpace credentials (SECRET_KEY changed?): {decrypt_error}")
        return None
    if not username or not password:
        return None
    return DSpaceClient(source.base_url, username=username, password=password)


def generate_dspace_thumbnail(client, item_uuid):
    """Best-effort: download the item's ORIGINAL bitstream and produce a JPEG thumbnail.

    Returns the relative /uploads/<file>.jpg path on success, or None on any failure.
    Tries the DSpace `/thumbnail` endpoint first (cheap if DSpace already made one),
    then falls back to the ORIGINAL bundle's first bitstream.
    """
    try:
        base = client.base_url.rstrip('/') if hasattr(client, 'base_url') else None
        if not base:
            return None
        uploads_dir = get_uploads_dir()

        # 1. Try DSpace's own thumbnail endpoint
        try:
            response = client.session.get(f"{base}/api/core/items/{item_uuid}/thumbnail", timeout=10)
            if response.status_code == 200 and response.content:
                # DSpace's thumbnail is already a JPEG — reuse as-is
                return generate_thumbnail_from_url(
                    f"{base}/api/core/items/{item_uuid}/thumbnail",
                    "thumbnail.jpg",
                    uploads_dir,
                )
        except Exception:
            pass

        # 2. Fall back to ORIGINAL bundle's first bitstream
        bundles_response = client.session.get(f"{base}/api/core/items/{item_uuid}/bundles", timeout=15)
        if bundles_response.status_code != 200:
            return None
        bundles = bundles_response.json().get('_embedded', {}).get('bundles', [])
        original = next((bundle for bundle in bundles if bundle.get('name') == 'ORIGINAL'), None)
        if not original:
            return None
        bitstreams_response = client.session.get(
            f"{base}/api/core/bundles/{original.get('uuid')}/bitstreams", timeout=15
        )
        if bitstreams_response.status_code != 200:
            return None
        bitstreams = bitstreams_response.json().get('_embedded', {}).get('bitstreams', [])
        if not bitstreams:
            return None
        bitstream = bitstreams[0]
        bitstream_uuid = bitstream.get('uuid')
        bitstream_name = bitstream.get('name') or 'bitstream'
        content_url = f"{base}/api/core/bitstreams/{bitstream_uuid}/content"
        return generate_thumbnail_from_url(content_url, bitstream_name, uploads_dir)
    except Exception as exc:
        logger.warning(f"thumbnail: failed for item {item_uuid}: {exc}")
        return None


def create_publication_from_item(client, source, full_item: Dict, owner_user_id: int,
                                 resource_type_id: int, collection_name: Optional[str],
                                 author_role_id) -> tuple:
    """
    Build a Publications row (plus creators and thumbnail) from a DSpace item
    and try to mint its DOCiD. Flushes but does not commit.

    Returns (publication, handle_url, minted). When minting fails the
    publication keeps the DSpace handle as document_docid, as before.
    """
    mapped_data = DSpaceMetadataMapper.dspace_to_docid(
        full_item, user_id=owner_user_id, collection_name=collection_name
    )
    publication_data = mapped_data.get('publication', {})

    item_uuid = full_item.get('uuid')
    item_handle = full_item.get('handle')
    handle_url = f"{repository_ui_base(source)}/handle/{item_handle}" if item_handle else None

    publication = Publications(
        user_id=owner_user_id,
        document_title=(publication_data.get('document_title') or 'Untitled')[:255],
        document_description=publication_data.get('document_description', ''),
        document_docid=item_handle,
        doi=publication_data.get('doi'),
        handle_url=handle_url,
        collection_name=collection_name,
        owner=source.owner_name,
        resource_type_id=resource_type_id,
    )
    db.session.add(publication)
    db.session.flush()

    minted_docid = IdentifierService.generate_handle()
    if minted_docid:
        publication.document_docid = minted_docid
        logger.info(f"[{source.name}] Minted DOCiD {minted_docid} for item {item_uuid}")
    else:
        logger.warning(f"[{source.name}] Cordra mint failed for item {item_uuid}, keeping DSpace handle: {item_handle}")

    for creator_data in mapped_data.get('creators', []):
        family_name = (creator_data.get('family_name') or '')[:255]
        given_name = (creator_data.get('given_name') or '')[:255]
        if family_name or given_name:
            db.session.add(PublicationCreators(
                publication_id=publication.id,
                family_name=family_name or 'Unknown',
                given_name=given_name,
                role_id=author_role_id or 'Author',
            ))

    # Best-effort: any failure leaves the poster empty.
    thumbnail_path = generate_dspace_thumbnail(client, item_uuid)
    if thumbnail_path:
        publication.publication_poster_url = thumbnail_path

    return publication, handle_url, bool(minted_docid)


def _tombstone_set_by_status_check(publication) -> bool:
    return (
        publication.deleted_at is not None
        and publication.deleted_by is None
        and publication.deletion_reason in WITHHELD_REASONS.values()
    )


def _audit(publication, action: str, details: Dict):
    try:
        PublicationAuditTrail.log_change(
            publication_id=publication.id,
            user_id=publication.user_id,
            action=action,
            field_name='deleted_at',
            new_value=json.dumps({**details, 'source': 'dspace_status_check'}),
            user_agent='DOCiD-Harvester',
        )
    except Exception as audit_error:
        logger.warning(f"Audit entry for publication {publication.id} failed: {audit_error}")


def apply_dspace_status(mapping: DSpaceMapping, new_status: str, now: Optional[datetime] = None) -> bool:
    """
    Record a record's new DSpace status and update its DOCiD page to match.

    Restricted, private and deleted records are tombstoned, so no metadata is
    shown. When the record is public (or withdrawn) again, only a tombstone set
    by this check is lifted; an owner's own retirement is left alone.
    Returns True when the status changed. Does not commit.
    """
    if mapping.dspace_status == new_status:
        return False
    now = now or datetime.utcnow()
    previous_status = mapping.dspace_status
    publication = mapping.publication
    mapping.dspace_status = new_status
    mapping.dspace_status_changed_at = now

    if publication is None:
        return True

    if new_status in DSPACE_WITHHELD_STATUSES:
        if publication.deleted_at is None or _tombstone_set_by_status_check(publication):
            publication.deleted_at = now
            publication.deleted_by = None
            publication.deletion_reason = WITHHELD_REASONS[new_status]
            _audit(publication, 'SOFT_DELETE', {
                'deleted_at': now.isoformat() + 'Z', 'dspace_status': new_status,
            })
    elif _tombstone_set_by_status_check(publication):
        publication.deleted_at = None
        publication.deleted_by = None
        publication.deletion_reason = None
        _audit(publication, 'RESTORE', {
            'restored_at': now.isoformat() + 'Z', 'dspace_status': new_status,
            'previous_dspace_status': previous_status,
        })

    logger.info(
        f"DSpace status of item {mapping.dspace_uuid} (publication {mapping.publication_id}): "
        f"{previous_status} -> {new_status}"
    )
    return True


def _harvest_new_item(reader, source, collection, item_uuid: str, owner_user_id: int, author_role_id) -> bool:
    savepoint = db.session.begin_nested()
    try:
        full_item = reader.get_item(item_uuid)
        if not full_item:
            raise RuntimeError(f"item {item_uuid} could not be read anonymously")
        publication, handle_url, minted = create_publication_from_item(
            reader, source, full_item, owner_user_id,
            collection.resource_type_id, collection.collection_name, author_role_id,
        )
        if not minted:
            writeback_status = 'waiting_for_docid'
        else:
            writeback_status = 'pending' if collection.write_back_enabled else 'disabled'
        db.session.add(DSpaceMapping(
            dspace_uuid=item_uuid,
            dspace_handle=full_item.get('handle') or item_uuid,
            dspace_url=handle_url,
            publication_id=publication.id,
            sync_status='synced',
            harvest_source_collection_id=collection.id,
            dspace_status='public',
            dspace_status_changed_at=datetime.utcnow(),
            writeback_status=writeback_status,
        ))
        savepoint.commit()
        # Commit per record: the DOCiD must be durable before it is written into DSpace.
        db.session.commit()
        return True
    except Exception as item_error:
        try:
            savepoint.rollback()
        except Exception:
            db.session.rollback()
        logger.error(f"[{source.name}] Error harvesting item {item_uuid}: {item_error}")
        return False


def process_writebacks(writer: Optional[DSpaceClient], collection, results: Dict,
                       only_uuids: Optional[List[str]] = None):
    """
    Mint DOCiDs that failed earlier, then write each pending DOCiD URL back to
    DSpace. Covers records harvested this run and retries from earlier runs.

    only_uuids limits the pass to those records. The every-minute check uses
    it to write back only what it just harvested: retries count against
    MAX_WRITEBACK_ATTEMPTS, which assumes one attempt a day.
    """
    if only_uuids is not None and not only_uuids:
        return
    query = (
        DSpaceMapping.query
        .filter(DSpaceMapping.harvest_source_collection_id == collection.id)
        .filter(DSpaceMapping.writeback_status.in_(RETRYABLE_WRITEBACK_STATUSES))
        .filter(DSpaceMapping.writeback_attempts < MAX_WRITEBACK_ATTEMPTS)
    )
    if only_uuids is not None:
        query = query.filter(DSpaceMapping.dspace_uuid.in_(only_uuids))
    rows = query.order_by(DSpaceMapping.id).all()
    # Set when writing is impossible for the whole collection (no credentials,
    # login refused). Failed mints are still retried; only the writes stop.
    writes_blocked_reason = None if writer is not None else \
        'No usable DSpace credentials on this source; write-back skipped.'

    for mapping in rows:
        publication = mapping.publication
        if publication is None or mapping.is_withheld:
            continue

        if mapping.writeback_status == 'waiting_for_docid':
            minted_docid = IdentifierService.generate_handle()
            if not minted_docid:
                continue
            publication.document_docid = minted_docid
            mapping.writeback_status = 'pending' if collection.write_back_enabled else 'disabled'
            db.session.commit()

        if not collection.write_back_enabled:
            mapping.writeback_status = 'disabled'
            db.session.commit()
            continue
        if writes_blocked_reason:
            continue

        try:
            writer.add_identifier_uri(mapping.dspace_uuid, docid_landing_url(publication.document_docid))
            mapping.writeback_status = 'done'
            mapping.writeback_error = None
            mapping.written_back_at = datetime.utcnow()
            results['written_back'] += 1
        except DSpaceAuthError as auth_error:
            # Every write would fail the same way; leave rows pending and tell the admin.
            writes_blocked_reason = str(auth_error)
            logger.error(f"[collection {collection.id}] {auth_error}")
            continue
        except DSpaceWriteError as write_error:
            mapping.writeback_status = 'failed'
            mapping.writeback_attempts = (mapping.writeback_attempts or 0) + 1
            mapping.writeback_error = str(write_error)[:2000]
            if write_error.status_code == 403:
                collection.write_back_ok = False
            results['writeback_failed'] += 1
            logger.warning(f"Write-back failed for item {mapping.dspace_uuid}: {write_error}")
        db.session.commit()

    if writes_blocked_reason:
        collection.last_error_message = writes_blocked_reason
        results['writes_blocked'] = True
        db.session.commit()


def harvest_collection(reader: DSpaceClient, writer: Optional[DSpaceClient], source, collection,
                       owner_user_id: int, author_role_id, dry_run: bool = False,
                       changed_since: Optional[datetime] = None) -> Dict:
    """
    One pass over one watched collection. Raises if the listing fails.

    The daily pass (changed_since None) lists every public record, so it also
    notices watched records that dropped out (restricted, hidden, deleted) and
    retries earlier write-back failures. The every-minute pass lists only the
    records changed since changed_since: it harvests the new ones, brings back
    records that are public again, writes back only what it just harvested,
    and leaves everything else to the daily pass.
    """
    results = {'listed': 0, 'created': 0, 'status_changed': 0, 'written_back': 0,
               'writeback_failed': 0, 'errors': 0}

    public_items = reader.list_public_collection_items(
        collection.dspace_collection_uuid, changed_since=changed_since,
    )
    results['listed'] = len(public_items)
    listed_uuids = [item['uuid'] for item in public_items]

    known_mappings = {}
    for chunk_start in range(0, len(listed_uuids), 500):
        chunk = listed_uuids[chunk_start:chunk_start + 500]
        for mapping in DSpaceMapping.query.filter(DSpaceMapping.dspace_uuid.in_(chunk)).all():
            known_mappings[mapping.dspace_uuid] = mapping

    # New public records, and watched records that are public again.
    harvested_uuids = []
    for item_uuid in listed_uuids:
        mapping = known_mappings.get(item_uuid)
        if mapping is None:
            if dry_run:
                results['created'] += 1
            elif _harvest_new_item(reader, source, collection, item_uuid, owner_user_id, author_role_id):
                results['created'] += 1
                harvested_uuids.append(item_uuid)
            else:
                results['errors'] += 1
        elif mapping.harvest_source_collection_id == collection.id and mapping.dspace_status != 'public':
            if not dry_run and apply_dspace_status(mapping, 'public'):
                results['status_changed'] += 1
                db.session.commit()

    if changed_since is None:
        # Watched records that dropped out of the public list. Only a full
        # listing can show that a record is missing.
        listed_set = set(listed_uuids)
        missing = [
            mapping for mapping in DSpaceMapping.query
            .filter(DSpaceMapping.harvest_source_collection_id == collection.id).all()
            if mapping.dspace_uuid not in listed_set
        ]
        for mapping in missing:
            try:
                state, _item = reader.get_public_item_state(mapping.dspace_uuid)
            except requests.RequestException as status_error:
                results['errors'] += 1
                logger.warning(f"Status check failed for item {mapping.dspace_uuid}: {status_error}")
                continue
            # 'public' here means visible by link but not listed in this collection
            # (moved, or search index lag): nothing to hide.
            if not dry_run and apply_dspace_status(mapping, state):
                results['status_changed'] += 1
                db.session.commit()

    if not dry_run:
        process_writebacks(writer, collection, results,
                           only_uuids=None if changed_since is None else harvested_uuids)
    return results


def _advance_last_checked(collection, pass_started_at: datetime):
    if collection.last_checked_at is None or collection.last_checked_at < pass_started_at:
        collection.last_checked_at = pass_started_at


def harvest_watched_collections(source, secret_key: str, dry_run: bool = False) -> Dict:
    """
    The daily pass over every active watched collection of one source.
    Returns totals shaped like the other harvesters'.
    """
    totals = {'total': 0, 'created': 0, 'skipped': 0, 'errors': 0,
              'status_changed': 0, 'written_back': 0, 'writeback_failed': 0}

    source.resolve_owner()
    owner_user_id = source.owner_user_id
    if not owner_user_id:
        logger.error(
            f"[{source.name}] owner_user_id is NULL (owner_email={source.owner_email!r}). "
            "Skipping harvest — link an institutional user_account before retrying."
        )
        return totals

    author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
    author_role_id = author_role.role_id if author_role else None
    reader = make_reader(source)
    writer = make_writer(source, secret_key)

    # Waits for an every-minute check of this source to finish (seconds).
    with source_lock(source.id, wait=True):
        for collection in source.collections:
            if not collection.is_active:
                continue
            pass_started_at = datetime.utcnow()
            try:
                results = harvest_collection(reader, writer, source, collection, owner_user_id,
                                             author_role_id, dry_run=dry_run)
            except Exception as collection_error:
                db.session.rollback()
                collection.last_error_message = f"Harvest failed: {collection_error}"[:2000]
                db.session.commit()
                totals['errors'] += 1
                logger.error(f"[{source.name}] Collection {collection.collection_name!r} failed: {collection_error}")
                continue

            logger.info(f"[{source.name}] Collection {collection.collection_name!r}: {results}")
            if not dry_run:
                collection.last_harvested_at = datetime.utcnow()
                # The full listing saw every change up to its start.
                _advance_last_checked(collection, pass_started_at)
                if not results.get('writes_blocked') and results['writeback_failed'] == 0 and results['errors'] == 0:
                    collection.last_error_message = None
                db.session.commit()
            totals['total'] += results['listed']
            totals['created'] += results['created']
            totals['skipped'] += results['listed'] - results['created']
            totals['errors'] += results['errors']
            for key in ('status_changed', 'written_back', 'writeback_failed'):
                totals[key] += results[key]
    return totals


def check_watched_collections_for_changes(source, secret_key: str, dry_run: bool = False) -> Optional[Dict]:
    """
    The every-minute check of one source: ask each watched collection for the
    records changed since the last pass, and harvest the new ones straight away.

    When nothing changed this is one anonymous search per collection, and it
    logs nothing. Collections that have never had a daily pass are skipped:
    their first, possibly long, harvest belongs to the daily pass, which is due
    at once for them.

    Returns None, doing nothing, while a daily pass of this source holds the
    source lock. 'check_failures' counts collections whose check failed; their
    last_checked_at stays put, so the next check covers the gap.
    """
    totals = {'total': 0, 'created': 0, 'errors': 0, 'status_changed': 0,
              'written_back': 0, 'writeback_failed': 0, 'check_failures': 0}
    collections = [collection for collection in source.collections
                   if collection.is_active and collection.last_harvested_at is not None]
    if not collections:
        return totals

    with source_lock(source.id, wait=False) as locked:
        if not locked:
            return None

        source.resolve_owner()
        owner_user_id = source.owner_user_id
        if not owner_user_id:
            # The daily pass reports this; repeating it every minute adds nothing.
            return totals
        author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
        author_role_id = author_role.role_id if author_role else None
        reader = make_reader(source)
        writer = make_writer(source, secret_key)

        for collection in collections:
            since = (collection.last_checked_at or collection.last_harvested_at) - CHANGE_CHECK_OVERLAP
            check_started_at = datetime.utcnow()
            try:
                results = harvest_collection(reader, writer, source, collection, owner_user_id,
                                             author_role_id, dry_run=dry_run, changed_since=since)
            except Exception as check_error:
                db.session.rollback()
                totals['check_failures'] += 1
                if dry_run:
                    logger.error(f"[{source.name}] Collection {collection.collection_name!r}: {check_error}")
                    continue
                already_failing = (collection.last_error_message or '').startswith(CHANGE_CHECK_ERROR_PREFIX)
                collection.last_error_message = f"{CHANGE_CHECK_ERROR_PREFIX}{check_error}"[:2000]
                db.session.commit()
                if not already_failing:
                    # Once per outage, not once a minute while it lasts.
                    logger.error(f"[{source.name}] Collection {collection.collection_name!r}: "
                                 f"{collection.last_error_message}")
                continue

            if not dry_run:
                if (collection.last_error_message or '').startswith(CHANGE_CHECK_ERROR_PREFIX):
                    logger.info(f"[{source.name}] Collection {collection.collection_name!r}: "
                                "change checks are working again")
                    collection.last_error_message = None
                _advance_last_checked(collection, check_started_at)
                db.session.commit()
            totals['total'] += results['listed']
            for key in ('created', 'errors', 'status_changed', 'written_back', 'writeback_failed'):
                totals[key] += results[key]
    return totals


def check_collection_connection(source, collection, secret_key: str) -> Dict:
    """
    The admin connection test: can DOCiD list the collection anonymously, log
    in, and edit metadata there? Stores the answer in collection.write_back_ok.
    """
    report = {'listed_public_items': None, 'login_ok': False, 'can_edit_metadata': False, 'error': None}
    try:
        report['listed_public_items'] = len(
            make_reader(source).list_public_collection_items(collection.dspace_collection_uuid)
        )
    except Exception as listing_error:
        report['error'] = f"Listing the collection failed: {listing_error}"
        return report

    writer = make_writer(source, secret_key)
    if writer is None:
        report['error'] = 'No usable DSpace credentials on this source.'
        return report
    try:
        report['can_edit_metadata'] = writer.can_edit_metadata(collection.dspace_collection_uuid)
        report['login_ok'] = True
    except DSpaceAuthError as auth_error:
        report['error'] = str(auth_error)
        return report
    except requests.RequestException as check_error:
        # Inconclusive (network or server error): leave write_back_ok as it was.
        report['login_ok'] = writer.auth_token is not None
        report['error'] = f"Permission check failed: {check_error}"
        return report

    collection.write_back_ok = report['can_edit_metadata']
    if not report['can_edit_metadata']:
        report['error'] = ('The account is not Administrator of this collection; '
                           'records will be harvested but not linked back.')
    db.session.commit()
    return report
