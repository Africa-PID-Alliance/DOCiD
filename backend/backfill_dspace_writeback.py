#!/usr/bin/env python3
"""
Adopt records DOCiD already harvested from a collection it now watches.

When a DSpace collection becomes a watched collection (harvest_source_collections),
records DOCiD harvested from it earlier through the whole-repository crawl are
already in dspace_mappings, so the daily harvest skips them as known. This
script links them to the watched collection and marks them for write-back,
so the next harvest run writes their DOCiD URLs into DSpace.

Only records the public can currently see in the collection are adopted, so a
restricted record is never touched.

Usage:
    python3 backfill_dspace_writeback.py --collection-id 3 --dry-run
    python3 backfill_dspace_writeback.py --collection-id 3
    python3 backfill_dspace_writeback.py --collection-id 3 --retype   # also set the collection's resource type
"""
import argparse
import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import DSpaceMapping, HarvestSourceCollection
from app.service_dspace_collections import make_reader

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def adopt_collection_records(collection_id, retype=False, dry_run=False):
    collection = db.session.get(HarvestSourceCollection, collection_id)
    if collection is None:
        logger.error(f"No watched collection with id={collection_id}")
        return 1

    reader = make_reader(collection.source)
    listed_uuids = [item['uuid'] for item in reader.list_public_collection_items(collection.dspace_collection_uuid)]
    logger.info(f"{collection.collection_name!r}: {len(listed_uuids)} public record(s) in DSpace")

    adopted = already_watched = other_collection = 0
    for chunk_start in range(0, len(listed_uuids), 500):
        chunk = listed_uuids[chunk_start:chunk_start + 500]
        for mapping in DSpaceMapping.query.filter(DSpaceMapping.dspace_uuid.in_(chunk)).all():
            if mapping.harvest_source_collection_id == collection.id:
                already_watched += 1
                continue
            if mapping.harvest_source_collection_id is not None:
                other_collection += 1
                continue

            publication = mapping.publication
            # A failed mint left the DSpace handle in document_docid.
            has_docid = publication.document_docid and publication.document_docid != mapping.dspace_handle
            if not has_docid:
                new_writeback_status = 'waiting_for_docid'
            else:
                new_writeback_status = 'pending' if collection.write_back_enabled else 'disabled'

            change = f"publication {publication.id} ({publication.document_docid}): writeback -> {new_writeback_status}"
            if retype and publication.resource_type_id != collection.resource_type_id:
                change += f", resource_type_id {publication.resource_type_id} -> {collection.resource_type_id}"
            logger.info(("[DRY RUN] " if dry_run else "") + change)

            if not dry_run:
                mapping.harvest_source_collection_id = collection.id
                mapping.dspace_status = 'public'
                mapping.dspace_status_changed_at = datetime.utcnow()
                mapping.writeback_status = new_writeback_status
                mapping.writeback_attempts = 0
                mapping.writeback_error = None
                if retype:
                    publication.resource_type_id = collection.resource_type_id
            adopted += 1

    if not dry_run:
        db.session.commit()
    logger.info(
        f"{'[DRY RUN] ' if dry_run else ''}Adopted {adopted}; already watched {already_watched}; "
        f"belong to another watched collection {other_collection}; "
        f"not yet in DOCiD {len(listed_uuids) - adopted - already_watched - other_collection} "
        "(the next harvest creates those)."
    )
    return 0


def main():
    parser = argparse.ArgumentParser(description="Adopt already-harvested records into a watched collection")
    parser.add_argument("--collection-id", type=int, required=True, help="harvest_source_collections.id")
    parser.add_argument("--retype", action="store_true", help="Also set each record's resource type to the collection's")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        return adopt_collection_records(args.collection_id, retype=args.retype, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
