#!/usr/bin/env python3
"""
Direct batch sync script — bypasses HTTP/gunicorn/nginx entirely.
Run on the production server with Flask app context.

Usage:
  python3 run_batch_sync.py --collection_id <UUID> [--limit 200] [--user_id 1] [--force_remap]
"""
import argparse
import sys
import os

# Ensure app directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Publications, PublicationCreators, DSpaceMapping, ResourceTypes, CreatorsRoles
from app.routes.dspace_legacy import (
    get_dspace_legacy_client, DSpaceLegacyMetadataMapper,
    _extract_legacy_doi, _apply_legacy_data_to_publication, _save_legacy_creators,
    DSPACE_LEGACY_URL
)

def run_batch_sync(collection_id, limit=200, offset=0, user_id=1, update_existing=False, force_remap=False):
    app = create_app()
    with app.app_context():
        if force_remap:
            update_existing = True

        print(f"[INFO] Starting batch sync for collection: {collection_id}")
        print(f"[INFO] limit={limit}, offset={offset}, user_id={user_id}, update_existing={update_existing}, force_remap={force_remap}")

        client = get_dspace_legacy_client()
        client.authenticate()
        print("[INFO] Authenticated with DSpace Legacy")

        if collection_id:
            items = client.get_collection_items(collection_id, limit=limit, offset=offset)
        else:
            items = client.get_items(limit=limit, offset=offset)

        if not items:
            print("[ERROR] Failed to fetch items")
            client.logout()
            return

        print(f"[INFO] Fetched {len(items)} items from DSpace")

        # Prefetch existing mappings
        def _make_legacy_uuid(item):
            item_uuid = item.get('uuid') or item.get('id')
            return str(item_uuid) if item_uuid and '-' in str(item_uuid) else f"legacy-item-{item_uuid}"

        incoming_legacy_uuids = [_make_legacy_uuid(item) for item in items if item.get('uuid') or item.get('id')]
        existing_mappings_map = {}
        if incoming_legacy_uuids:
            existing_mappings = DSpaceMapping.query.filter(
                DSpaceMapping.dspace_uuid.in_(incoming_legacy_uuids)
            ).all()
            existing_mappings_map = {m.dspace_uuid: m for m in existing_mappings}

        resource_type_cache = {rt.resource_type: rt.id for rt in ResourceTypes.query.all()}
        author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
        author_role_id = author_role.role_id if author_role else None

        results = {'total': len(items), 'created': 0, 'updated': 0, 'unchanged': 0, 'skipped': 0, 'errors': 0}

        for idx, item_summary in enumerate(items, 1):
            item_id = item_summary.get('uuid') or item_summary.get('id')
            handle = item_summary.get('handle', f'legacy/{item_id}')
            legacy_uuid = str(item_id) if item_id and '-' in str(item_id) else f"legacy-item-{item_id}"

            try:
                savepoint = db.session.begin_nested()
                existing_mapping = existing_mappings_map.get(legacy_uuid)

                if existing_mapping and not update_existing:
                    savepoint.rollback()
                    results['skipped'] += 1
                    print(f"  [{idx}/{len(items)}] SKIPPED {item_id} (already synced, docid={existing_mapping.publication.document_docid})")
                    continue

                full_item = client.get_item(item_id)
                if not full_item:
                    savepoint.rollback()
                    results['errors'] += 1
                    print(f"  [{idx}/{len(items)}] ERROR {item_id} (failed to fetch)")
                    continue

                metadata_list = full_item.get('metadata', [])
                new_metadata_hash = client.calculate_metadata_hash(metadata_list)
                mapped_data = DSpaceLegacyMetadataMapper.dspace_to_docid(full_item, user_id)
                doi = _extract_legacy_doi(metadata_list)
                resource_type_id = resource_type_cache.get(
                    mapped_data['publication'].get('resource_type', 'Text'), 1
                )

                if existing_mapping and update_existing:
                    if not force_remap and existing_mapping.dspace_metadata_hash == new_metadata_hash:
                        savepoint.rollback()
                        results['unchanged'] += 1
                        print(f"  [{idx}/{len(items)}] UNCHANGED {item_id} (hash match)")
                        continue

                    publication = existing_mapping.publication
                    publication.user_id = user_id
                    _apply_legacy_data_to_publication(publication, mapped_data, resource_type_id, handle, item_id, doi)
                    PublicationCreators.query.filter_by(publication_id=publication.id).delete()
                    _save_legacy_creators(publication.id, mapped_data.get('creators', []), author_role_id)
                    existing_mapping.dspace_metadata_hash = new_metadata_hash
                    existing_mapping.sync_status = 'synced'
                    existing_mapping.error_message = None
                    savepoint.commit()
                    results['updated'] += 1
                    print(f"  [{idx}/{len(items)}] UPDATED {item_id} -> docid={publication.document_docid}")
                else:
                    publication = Publications(user_id=user_id)
                    _apply_legacy_data_to_publication(publication, mapped_data, resource_type_id, handle, item_id, doi)
                    db.session.add(publication)
                    db.session.flush()
                    _save_legacy_creators(publication.id, mapped_data.get('creators', []), author_role_id)
                    mapping = DSpaceMapping(
                        dspace_handle=handle,
                        dspace_uuid=legacy_uuid,
                        dspace_url=DSPACE_LEGACY_URL,
                        publication_id=publication.id,
                        sync_status='synced',
                        dspace_metadata_hash=new_metadata_hash
                    )
                    db.session.add(mapping)
                    savepoint.commit()
                    results['created'] += 1
                    print(f"  [{idx}/{len(items)}] CREATED {item_id} -> docid={publication.document_docid}")

            except Exception as e:
                try:
                    savepoint.rollback()
                except Exception:
                    db.session.rollback()
                results['errors'] += 1
                print(f"  [{idx}/{len(items)}] ERROR {item_id}: {e}")

        db.session.commit()
        client.logout()

        print(f"\n[DONE] {results['created']} created, {results['updated']} updated, "
              f"{results['unchanged']} unchanged, {results['skipped']} skipped, {results['errors']} errors")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Direct DSpace Legacy batch sync')
    parser.add_argument('--collection_id', required=True, help='DSpace collection UUID')
    parser.add_argument('--limit', type=int, default=200, help='Max items to sync')
    parser.add_argument('--offset', type=int, default=0, help='Offset for pagination')
    parser.add_argument('--user_id', type=int, default=1, help='DOCiD user ID for ownership')
    parser.add_argument('--force_remap', action='store_true', help='Force re-sync even if unchanged')
    parser.add_argument('--update_existing', action='store_true', help='Update existing records')
    args = parser.parse_args()

    run_batch_sync(
        collection_id=args.collection_id,
        limit=args.limit,
        offset=args.offset,
        user_id=args.user_id,
        update_existing=args.update_existing,
        force_remap=args.force_remap
    )
