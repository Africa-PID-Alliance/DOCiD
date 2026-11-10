#!/usr/bin/env python3
"""
Multi-Source Repository Harvest Orchestrator for DOCiD.

Iterates all active harvest_sources, checks harvest frequency,
and syncs new records from each repository using the appropriate
DSpace client (legacy or modern).

Usage:
    python3 harvest_repositories.py                    # Harvest all due sources
    python3 harvest_repositories.py --source-id 2      # Harvest specific source by ID
    python3 harvest_repositories.py --force             # Ignore frequency, harvest now
    python3 harvest_repositories.py --dry-run           # Preview without committing
    python3 harvest_repositories.py --batch-size 100    # Items per page (default: 50)
    python3 harvest_repositories.py --changes-only      # Every-minute check of watched collections
"""

import os
import sys
import logging
import argparse
import time
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# The every-minute check runs 1,440 times a day and must stay silent when
# nothing changed. The app logs INFO lines while it loads and starts, which
# would fill its log and rotate logs/app.log (10 KB files) out from under the
# web app. main() lifts this once the app is up; warnings and errors still pass.
if '--changes-only' in sys.argv:
    logging.disable(logging.INFO)

from app import create_app, db
from app.models import (
    HarvestSource, HarvestSourceFieldMapping, EnrichmentRun,
    Publications, DSpaceMapping, ResourceTypes, CreatorsRoles, PublicationCreators
)
from app.utils_crypto import decrypt_value
from app.service_dspace_collections import (
    check_watched_collections_for_changes,
    create_publication_from_item,
    harvest_watched_collections,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

FREQUENCY_DAYS = {'daily': 1, 'weekly': 7, 'biweekly': 14, 'monthly': 30}


def is_due_for_harvest(source, now=None):
    """
    Whether a source's full harvest is due under its frequency setting.

    Counted in calendar days (UTC): a daily source harvested at 02:05 yesterday
    is due at 02:00 today. Counting whole 24-hour periods made it wait another
    day, so a daily cron harvested daily sources only every other day.
    A watched collection that has never been harvested makes the source due at
    once: the every-minute check leaves a collection's first harvest to this run.
    """
    if source.last_harvested_at is None:
        return True
    if any(collection.is_active and collection.last_harvested_at is None
           for collection in source.collections):
        return True
    now = now or datetime.utcnow()
    elapsed_days = (now.date() - source.last_harvested_at.date()).days
    required_days = FREQUENCY_DAYS.get(source.harvest_frequency, 7)
    return elapsed_days >= required_days


def get_client_for_source(source, secret_key):
    """
    Create the appropriate DSpace client for a harvest source.
    Handles auth, wrong credentials, and unreachable APIs gracefully.

    Returns:
        (client, error_message) tuple. client is None if connection failed.
    """
    if source.api_type == 'legacy':
        try:
            from app.service_dspace_legacy import DSpaceLegacyClient
        except ImportError:
            return None, "DSpaceLegacyClient not available"

        client = DSpaceLegacyClient(source.base_url)

        if source.auth_required:
            username = decrypt_value(source.encrypted_username, secret_key)
            password = decrypt_value(source.encrypted_password, secret_key)

            if not username or not password:
                return None, "Credentials decryption failed (SECRET_KEY may have changed)"

            try:
                client.authenticate(username, password)
            except Exception as auth_error:
                return None, f"Authentication failed: {auth_error}"

        # Verify connection
        try:
            status_response = client.session.get(f"{source.base_url}/rest/status", timeout=10)
            if status_response.status_code != 200:
                return None, f"API unreachable: HTTP {status_response.status_code}"
        except Exception as connection_error:
            return None, f"API unreachable: {connection_error}"

        return client, None

    elif source.api_type == 'modern':
        try:
            from app.service_dspace import DSpaceClient
        except ImportError:
            return None, "DSpaceClient not available"

        client = DSpaceClient(source.base_url)

        # Verify connection
        try:
            test_response = client.session.get(f"{source.base_url}/api", timeout=10)
            if test_response.status_code != 200:
                return None, f"API unreachable: HTTP {test_response.status_code}"
        except Exception as connection_error:
            return None, f"API unreachable: {connection_error}"

        return client, None

    else:
        return None, f"Unsupported api_type: {source.api_type}"


def harvest_modern_source(client, source, batch_size=50, max_pages=10, dry_run=False):
    """
    Harvest items from a modern DSpace 7+/9 source using discover/search.
    Falls back from /api/core/items to /api/discover/search if needed.
    """
    from app.service_dspace import DSpaceMetadataMapper

    results = {'total': 0, 'created': 0, 'skipped': 0, 'errors': 0}

    # Resolve owner from harvest_sources.owner_email → user_accounts.user_id.
    # Refuse to harvest when no official institutional account is linked, to
    # prevent silently attributing records to user 1 (legacy default).
    source.resolve_owner()
    owner_user_id = source.owner_user_id
    if not owner_user_id:
        logger.error(
            f"[{source.name}] owner_user_id is NULL (owner_email={source.owner_email!r}). "
            "Skipping harvest — link an institutional user_account before retrying."
        )
        return results
    logger.info(f"[{source.name}] Harvesting as user_id={owner_user_id} (owner_email={source.owner_email})")

    # Prefetch lookup data
    resource_type_cache = {resource_type.resource_type: resource_type.id for resource_type in ResourceTypes.query.all()}
    default_resource_type_id = resource_type_cache.get('Text', 1)
    author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
    author_role_id = author_role.role_id if author_role else None

    for page_number in range(max_pages):
        # Try /api/core/items first, fallback to discover/search
        items_data = client.get_items(page=page_number, size=batch_size)
        items = items_data.get('_embedded', {}).get('items', [])

        if not items:
            items_data = client.search_items(page=page_number, size=batch_size)
            items = items_data.get('_embedded', {}).get('items', [])

        if not items:
            logger.info(f"[{source.name}] No more items at page {page_number}")
            break

        logger.info(f"[{source.name}] Page {page_number}: {len(items)} items")

        # Prefetch existing mappings for dedup
        incoming_uuids = [item.get('uuid') for item in items if item.get('uuid')]
        existing_mappings = {}
        if incoming_uuids:
            existing_records = DSpaceMapping.query.filter(
                DSpaceMapping.dspace_uuid.in_(incoming_uuids)
            ).all()
            existing_mappings = {mapping.dspace_uuid: mapping for mapping in existing_records}

        for item in items:
            item_uuid = item.get('uuid')
            if not item_uuid:
                results['errors'] += 1
                continue

            results['total'] += 1

            # Skip if already synced
            if item_uuid in existing_mappings:
                results['skipped'] += 1
                continue

            if dry_run:
                results['created'] += 1
                continue

            savepoint = db.session.begin_nested()
            try:
                # Fetch full metadata
                full_item = client.get_item(item_uuid)
                if not full_item:
                    results['errors'] += 1
                    savepoint.rollback()
                    continue

                # Get collection name
                collection_name = None
                try:
                    collection_data = client.get_item_owning_collection(item_uuid)
                    if collection_data:
                        collection_name = collection_data.get('name')
                except Exception:
                    pass

                # Determine resource type from dc.type
                mapped_type = DSpaceMetadataMapper.dspace_to_docid(full_item, user_id=owner_user_id)
                resource_type_name = mapped_type.get('publication', {}).get('resource_type', 'Text')
                resource_type_id = resource_type_cache.get(resource_type_name, default_resource_type_id)

                # Publication, creators, thumbnail and DOCiD mint (shared with watched collections)
                publication, handle_url, _minted = create_publication_from_item(
                    client, source, full_item, owner_user_id,
                    resource_type_id, collection_name, author_role_id,
                )

                # Create DSpace mapping for dedup
                dspace_mapping = DSpaceMapping(
                    dspace_uuid=item_uuid,
                    dspace_handle=full_item.get('handle'),
                    dspace_url=handle_url,
                    publication_id=publication.id,
                    sync_status='synced',
                )
                db.session.add(dspace_mapping)
                savepoint.commit()
                results['created'] += 1

            except Exception as item_error:
                try:
                    savepoint.rollback()
                except Exception:
                    db.session.rollback()
                results['errors'] += 1
                logger.error(f"[{source.name}] Error syncing item {item_uuid}: {item_error}")

            time.sleep(0.1)  # Be polite to the API

        # Commit after each page
        if not dry_run:
            db.session.commit()

    return results


def harvest_legacy_source(client, source, batch_size=50, dry_run=False):
    """
    Harvest items from a legacy DSpace 6.x source.
    Discovers communities → collections → items.
    """
    dspace_legacy_url = source.base_url
    results = {'total': 0, 'created': 0, 'skipped': 0, 'errors': 0}

    source.resolve_owner()
    if not source.owner_user_id:
        logger.error(
            f"[{source.name}] owner_user_id is NULL (owner_email={source.owner_email!r}). "
            "Skipping harvest — link an institutional user_account before retrying."
        )
        return results
    logger.info(f"[{source.name}] Harvesting as user_id={source.owner_user_id} (owner_email={source.owner_email})")

    # Discover communities
    try:
        communities_response = client.session.get(
            f"{dspace_legacy_url}/rest/communities?limit=50", timeout=15
        )
        if communities_response.status_code != 200:
            logger.error(f"[{source.name}] Failed to list communities: HTTP {communities_response.status_code}")
            return results
        communities = communities_response.json()
    except Exception as discovery_error:
        logger.error(f"[{source.name}] Failed to discover communities: {discovery_error}")
        return results

    for community in communities:
        community_name = community.get('name', 'Unknown')
        community_id = community.get('uuid', community.get('id'))

        try:
            collections_response = client.session.get(
                f"{dspace_legacy_url}/rest/communities/{community_id}/collections", timeout=15
            )
            if collections_response.status_code != 200:
                continue
            collections = collections_response.json()
        except Exception:
            continue

        for collection in collections:
            collection_name = collection.get('name', 'Unknown')
            collection_id = collection.get('uuid', collection.get('id'))
            item_count = collection.get('numberItems', 0)

            if item_count == 0:
                continue

            logger.info(f"[{source.name}] Collection: {collection_name} ({item_count} items)")

            if dry_run:
                results['total'] += item_count
                results['created'] += item_count
                continue

            # Sync collection items
            try:
                from run_batch_sync import sync_collection
                sync_results = sync_collection(client, str(collection_id), limit=batch_size)
                results['created'] += sync_results.get('created', 0)
                results['skipped'] += sync_results.get('unchanged', 0) + sync_results.get('skipped', 0)
                results['errors'] += sync_results.get('errors', 0)
                results['total'] += sync_results.get('total', 0)
            except ImportError:
                logger.warning(f"[{source.name}] run_batch_sync not available")
                results['skipped'] += item_count
            except Exception as sync_error:
                logger.error(f"[{source.name}] Error syncing collection {collection_name}: {sync_error}")
                results['errors'] += 1

    # Logout
    try:
        client.session.post(f"{dspace_legacy_url}/rest/logout", timeout=10)
    except Exception:
        pass

    return results


def harvest_all_sources(force=False, source_id=None, batch_size=50, dry_run=False):
    """Main harvest loop: iterate all active sources."""
    from flask import current_app
    secret_key = current_app.config.get('SECRET_KEY', '')

    if source_id:
        sources = HarvestSource.query.filter_by(id=source_id, is_active=True).all()
    else:
        sources = HarvestSource.query.filter_by(is_active=True).all()

    if not sources:
        logger.info("No active harvest sources found")
        return

    logger.info(f"Found {len(sources)} active source(s)")

    for source in sources:
        # Check frequency
        if not force and not is_due_for_harvest(source):
            logger.info(
                f"[{source.name}] Skipping — last harvested {source.last_harvested_at}, "
                f"frequency={source.harvest_frequency}"
            )
            continue

        logger.info(f"\n{'='*60}")
        logger.info(f"Harvesting: {source.name} (DSpace {source.dspace_version}, {source.api_type})")
        logger.info(f"{'='*60}")

        # Create run record
        harvest_run = EnrichmentRun(
            run_type='harvest',
            source_name=source.name,
            status='running',
            started_at=datetime.utcnow()
        )
        if not dry_run:
            db.session.add(harvest_run)
            db.session.flush()

        # Get client
        client, connection_error = get_client_for_source(source, secret_key)
        if not client:
            logger.error(f"[{source.name}] Connection failed: {connection_error}")
            if not dry_run:
                harvest_run.status = 'failed'
                harvest_run.error_summary = connection_error
                harvest_run.completed_at = datetime.utcnow()
                db.session.commit()
            continue

        # Harvest based on api_type. A modern source with watched collections
        # harvests only those collections (anonymously, with write-back);
        # one without keeps the whole-repository crawl.
        if source.api_type == 'modern' and any(collection.is_active for collection in source.collections):
            results = harvest_watched_collections(source, secret_key, dry_run=dry_run)
        elif source.api_type == 'modern':
            results = harvest_modern_source(client, source, batch_size=batch_size, dry_run=dry_run)
        elif source.api_type == 'legacy':
            results = harvest_legacy_source(client, source, batch_size=batch_size, dry_run=dry_run)
        else:
            logger.warning(f"[{source.name}] Unsupported api_type: {source.api_type}")
            results = {'total': 0, 'created': 0, 'skipped': 0, 'errors': 0}

        # Update source and run records
        if not dry_run:
            source.last_harvested_at = datetime.utcnow()
            source.total_items_synced = (source.total_items_synced or 0) + results.get('created', 0)
            harvest_run.status = 'completed'
            harvest_run.completed_at = datetime.utcnow()
            harvest_run.publications_processed = results.get('total', 0)
            harvest_run.publications_enriched = results.get('created', 0)
            harvest_run.publications_skipped = results.get('skipped', 0)
            harvest_run.publications_failed = results.get('errors', 0)
            db.session.commit()

        prefix = "[DRY RUN] " if dry_run else ""
        logger.info(f"\n{prefix}{source.name} Results:")
        logger.info(f"  Total: {results.get('total', 0)}")
        logger.info(f"  Created: {results.get('created', 0)}")
        logger.info(f"  Skipped: {results.get('skipped', 0)}")
        logger.info(f"  Errors: {results.get('errors', 0)}")


def check_all_sources_for_changes(source_id=None, dry_run=False):
    """
    The every-minute pass (--changes-only): for each source with watched
    collections, harvest the records changed since the last check.

    Quiet when nothing changed: no run record and no log lines. It never
    touches the source's last_harvested_at, so the daily full pass keeps its
    own schedule.
    """
    from flask import current_app
    secret_key = current_app.config.get('SECRET_KEY', '')

    query = HarvestSource.query.filter_by(is_active=True, api_type='modern')
    if source_id:
        query = query.filter_by(id=source_id)

    for source in query.all():
        if not any(collection.is_active for collection in source.collections):
            continue
        started_at = datetime.utcnow()
        totals = check_watched_collections_for_changes(source, secret_key, dry_run=dry_run)
        if totals is None:
            continue  # its daily pass is running and will see the same records
        failed = totals['errors'] + totals['writeback_failed']
        if not (totals['created'] or totals['status_changed'] or totals['written_back'] or failed):
            continue

        prefix = "[DRY RUN] " if dry_run else ""
        logger.info(
            f"{prefix}[{source.name}] Change check: {totals['created']} new, "
            f"{totals['status_changed']} public again, {totals['written_back']} linked back, {failed} failed"
        )
        if dry_run:
            continue
        db.session.add(EnrichmentRun(
            run_type='harvest_changes',
            source_name=source.name,
            status='completed',
            started_at=started_at,
            completed_at=datetime.utcnow(),
            publications_processed=totals['total'],
            publications_enriched=totals['created'],
            publications_skipped=totals['total'] - totals['created'],
            publications_failed=failed,
        ))
        source.total_items_synced = (source.total_items_synced or 0) + totals['created']
        db.session.commit()


def main():
    parser = argparse.ArgumentParser(
        description="Harvest new records from all active repository sources"
    )
    parser.add_argument("--source-id", type=int, default=None, help="Harvest a specific source by ID")
    parser.add_argument("--force", action="store_true", help="Ignore frequency schedule, harvest now")
    parser.add_argument("--batch-size", type=int, default=50, help="Items per page (default: 50)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without committing")
    parser.add_argument(
        "--changes-only", action="store_true",
        help="Every-minute check: in watched collections, harvest only records changed since the last check",
    )
    args = parser.parse_args()

    app = create_app()
    # Start-up is over: let this run's own lines through (see the top of the file).
    logging.disable(logging.NOTSET)
    with app.app_context():
        if args.changes_only:
            check_all_sources_for_changes(source_id=args.source_id, dry_run=args.dry_run)
            return
        harvest_all_sources(
            force=args.force,
            source_id=args.source_id,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
