#!/usr/bin/env python3
"""
Batch import items from DSpace to DOCiD
Usage: python sync_from_dspace.py [--all] [--pages 5] [--size 50]
"""

import argparse
import sys
from app import create_app, db
from app.models import Publications, DSpaceMapping, UserAccount
from app.service_dspace import DSpaceClient, DSpaceMetadataMapper
import os

# Configuration
DSPACE_BASE_URL = os.getenv('DSPACE_BASE_URL', 'https://demo.dspace.org/server')
DSPACE_USERNAME = os.getenv('DSPACE_USERNAME', 'dspacedemo+admin@gmail.com')
DSPACE_PASSWORD = os.getenv('DSPACE_PASSWORD', 'dspace')
DEFAULT_USER_ID = 1  # Admin user


def sync_items(pages=1, size=50, skip_existing=True):
    """
    Sync items from DSpace to DOCiD

    Args:
        pages: Number of pages to fetch
        size: Items per page
        skip_existing: Skip already synced items
    """
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("DSpace to DOCiD Sync Script")
        print("=" * 60)
        print(f"DSpace URL: {DSPACE_BASE_URL}")
        print(f"Pages: {pages}, Size per page: {size}")
        print(f"Skip existing: {skip_existing}")
        print()

        # Initialize client
        print("Authenticating with DSpace...")
        client = DSpaceClient(DSPACE_BASE_URL, DSPACE_USERNAME, DSPACE_PASSWORD)

        if not client.authenticate():
            print("❌ Authentication failed!")
            return

        print("✅ Authenticated successfully\n")

        stats = {
            'total': 0,
            'created': 0,
            'skipped': 0,
            'errors': 0
        }

        # Fetch and process each page
        for page in range(pages):
            print(f"\n--- Processing Page {page + 1}/{pages} ---")

            items_data = client.get_items(page=page, size=size)
            items = items_data.get('_embedded', {}).get('items', [])

            if not items:
                print(f"No items found on page {page}")
                break

            print(f"Found {len(items)} items on page {page}")
            stats['total'] += len(items)

            for i, item in enumerate(items, 1):
                uuid = item.get('uuid')
                handle = item.get('handle')
                name = item.get('name', 'Untitled')

                print(f"  [{i}/{len(items)}] {name[:50]}...")
                print(f"      UUID: {uuid}, Handle: {handle}")

                try:
                    # Check if exists
                    if skip_existing:
                        existing = DSpaceMapping.query.filter_by(dspace_uuid=uuid).first()
                        if existing:
                            print(f"      ⏭  Skipped (already exists)")
                            stats['skipped'] += 1
                            continue

                    # Get full item data
                    full_item = client.get_item(uuid)
                    if not full_item:
                        print(f"      ❌ Failed to fetch full item data")
                        stats['errors'] += 1
                        continue

                    # Map to DOCiD format
                    mapped_data = DSpaceMetadataMapper.dspace_to_docid(full_item, DEFAULT_USER_ID)

                    # Get resource type ID (default to 1 for 'Text' if not found)
                    from app.models import ResourceTypes
                    resource_type_name = mapped_data['publication'].get('resource_type', 'Text')
                    resource_type = ResourceTypes.query.filter_by(resource_type=resource_type_name).first()
                    resource_type_id = resource_type.id if resource_type else 1

                    # Generate Handle-format DocID for DSpace items
                    # Format: 20.500.DSPACE/uuid (follows Handle system pattern)
                    document_docid = f"20.500.DSPACE/{uuid}"

                    # Create publication
                    publication = Publications(
                        user_id=DEFAULT_USER_ID,
                        document_title=mapped_data['publication']['document_title'],
                        document_description=mapped_data['publication'].get('document_description', ''),
                        resource_type_id=resource_type_id,
                        doi='',  # Will be generated later
                        document_docid=document_docid,
                        owner='DSpace Repository',  # Temporary - will be linked to university ID later
                    )

                    db.session.add(publication)
                    db.session.flush()

                    # Create mapping
                    mapping = DSpaceMapping(
                        dspace_handle=handle,
                        dspace_uuid=uuid,
                        dspace_url=DSPACE_BASE_URL,
                        publication_id=publication.id,
                        sync_status='synced',
                        dspace_metadata_hash=client.calculate_metadata_hash(full_item.get('metadata', {}))
                    )

                    db.session.add(mapping)
                    db.session.commit()

                    print(f"      ✅ Created (DOCiD: {publication.document_docid})")
                    stats['created'] += 1

                except Exception as e:
                    db.session.rollback()
                    print(f"      ❌ Error: {str(e)}")
                    stats['errors'] += 1

        # Print summary
        print("\n" + "=" * 60)
        print("SYNC SUMMARY")
        print("=" * 60)
        print(f"Total items processed: {stats['total']}")
        print(f"  ✅ Created: {stats['created']}")
        print(f"  ⏭  Skipped: {stats['skipped']}")
        print(f"  ❌ Errors: {stats['errors']}")
        print("=" * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sync items from DSpace to DOCiD')
    parser.add_argument('--all', action='store_true', help='Sync all items (570 items)')
    parser.add_argument('--pages', type=int, default=1, help='Number of pages to sync')
    parser.add_argument('--size', type=int, default=50, help='Items per page')
    parser.add_argument('--no-skip', action='store_true', help='Do not skip existing items')

    args = parser.parse_args()

    if args.all:
        # 570 items / 50 per page = ~12 pages
        pages = 12
        size = 50
    else:
        pages = args.pages
        size = args.size

    skip_existing = not args.no_skip

    sync_items(pages=pages, size=size, skip_existing=skip_existing)
