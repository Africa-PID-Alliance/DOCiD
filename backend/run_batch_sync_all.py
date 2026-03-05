#!/usr/bin/env python3
"""
Batch sync ALL collections from Stellenbosch DSpace Legacy.
Loops through all communities/collections and syncs items that have not been synced yet.

Usage:
  python3 run_batch_sync_all.py [--limit_per_collection 200] [--user_id 1] [--force_remap]
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Publications, PublicationCreators, DSpaceMapping, ResourceTypes, CreatorsRoles
from app.routes.dspace_legacy import (
    get_dspace_legacy_client, DSpaceLegacyMetadataMapper,
    _extract_legacy_doi, _apply_legacy_data_to_publication, _save_legacy_creators,
    DSPACE_LEGACY_URL
)


def run_sync_all_collections(limit_per_collection=200, user_id=1, update_existing=False, force_remap=False, target_collections=None):
    app = create_app()
    with app.app_context():
        if force_remap:
            update_existing = True

        client = get_dspace_legacy_client()
        client.authenticate()
        print("[INFO] Authenticated with DSpace Legacy")

        # Get all communities
        communities = client.session.get(f"{DSPACE_LEGACY_URL}/rest/communities?limit=50").json()
        print(f"[INFO] Found {len(communities)} communities")

        # Collect all collections with items
        collections_to_sync = []
        for community in communities:
            community_name = community.get('name', 'Unknown')
            community_uuid = community.get('uuid')
            resp = client.session.get(f"{DSPACE_LEGACY_URL}/rest/communities/{community_uuid}/collections?limit=200")
            if resp.status_code == 200:
                for col in resp.json():
                    num_items = col.get('numberItems', 0)
                    if num_items > 0:
                        collection_info = {
                            'uuid': col.get('uuid'),
                            'name': col.get('name'),
                            'num_items': num_items,
                            'community': community_name
                        }
                        if target_collections is None or col.get('uuid') in target_collections:
                            collections_to_sync.append(collection_info)

        print(f"[INFO] Found {len(collections_to_sync)} collections with items to sync")
        total_items_expected = sum(c['num_items'] for c in collections_to_sync)
        print(f"[INFO] Total items expected: {total_items_expected}")

        # Prefetch caches
        resource_type_cache = {rt.resource_type: rt.id for rt in ResourceTypes.query.all()}
        author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
        author_role_id = author_role.role_id if author_role else None

        grand_totals = {'created': 0, 'updated': 0, 'unchanged': 0, 'skipped': 0, 'errors': 0}

        for col_idx, col_info in enumerate(collections_to_sync, 1):
            collection_id = col_info['uuid']
            collection_name = col_info['name']
            num_items = col_info['num_items']
            community_name = col_info['community']

            print(f"\n{'='*60}")
            print(f"[{col_idx}/{len(collections_to_sync)}] Collection: {collection_name}")
            print(f"    Community: {community_name} | Items: {num_items}")
            print(f"{'='*60}")

            try:
                items = client.get_collection_items(collection_id, limit=limit_per_collection, offset=0)
            except Exception as e:
                print(f"  ERROR fetching collection items: {e}")
                grand_totals['errors'] += num_items
                continue

            if not items:
                print(f"  No items returned for collection {collection_name}")
                continue

            print(f"  Fetched {len(items)} items")

            # Prefetch existing mappings for this batch
            def make_legacy_uuid(item):
                item_uuid = item.get('uuid') or item.get('id')
                return str(item_uuid) if item_uuid and '-' in str(item_uuid) else f"legacy-item-{item_uuid}"

            incoming_uuids = [make_legacy_uuid(item) for item in items if item.get('uuid') or item.get('id')]
            existing_mappings_map = {}
            if incoming_uuids:
                existing_mappings = DSpaceMapping.query.filter(
                    DSpaceMapping.dspace_uuid.in_(incoming_uuids)
                ).all()
                existing_mappings_map = {m.dspace_uuid: m for m in existing_mappings}

            results = {'created': 0, 'updated': 0, 'unchanged': 0, 'skipped': 0, 'errors': 0}

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
                        continue

                    full_item = client.get_item(item_id)
                    if not full_item:
                        savepoint.rollback()
                        results['errors'] += 1
                        print(f"    [{idx}/{len(items)}] ERROR {item_id} (failed to fetch)")
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
                        print(f"    [{idx}/{len(items)}] UPDATED {item_id}")
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
                        print(f"    [{idx}/{len(items)}] CREATED {item_id} -> docid={publication.document_docid}")

                except Exception as e:
                    try:
                        savepoint.rollback()
                    except Exception:
                        db.session.rollback()
                    results['errors'] += 1
                    print(f"    [{idx}/{len(items)}] ERROR {item_id}: {e}")

            db.session.commit()

            print(f"  Summary: {results['created']} created, {results['updated']} updated, "
                  f"{results['unchanged']} unchanged, {results['skipped']} skipped, {results['errors']} errors")

            for key in grand_totals:
                grand_totals[key] += results[key]

        client.logout()

        print(f"\n{'='*60}")
        print(f"GRAND TOTAL: {grand_totals['created']} created, {grand_totals['updated']} updated, "
              f"{grand_totals['unchanged']} unchanged, {grand_totals['skipped']} skipped, {grand_totals['errors']} errors")
        print(f"{'='*60}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sync ALL DSpace Legacy collections')
    parser.add_argument('--limit_per_collection', type=int, default=200, help='Max items per collection')
    parser.add_argument('--user_id', type=int, default=1, help='DOCiD user ID for ownership')
    parser.add_argument('--force_remap', action='store_true', help='Force re-sync even if unchanged')
    parser.add_argument('--update_existing', action='store_true', help='Update existing records')
    args = parser.parse_args()

    run_sync_all_collections(
        limit_per_collection=args.limit_per_collection,
        user_id=args.user_id,
        update_existing=args.update_existing,
        force_remap=args.force_remap
    )
