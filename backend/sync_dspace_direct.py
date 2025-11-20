#!/usr/bin/env python3
"""
Direct DSpace to DOCiD sync using Flask app context
Bypasses API authentication for direct database access
"""

from app import create_app, db
from app.models import Publications, DSpaceMapping, ResourceTypes, UserAccount
from app.service_dspace import DSpaceClient, DSpaceMetadataMapper
import sys

# Configuration
DSPACE_BASE_URL = "https://demo.dspace.org/server"
DSPACE_USERNAME = "dspacedemo+admin@gmail.com"
DSPACE_PASSWORD = "dspace"
NUM_ITEMS = 10  # Fetch 10 items
START_PAGE = 0  # Start from page 0

# User ID to assign publications to
USER_ID = 1  # Default admin user


def sync_dspace_items():
    """Sync DSpace items directly to database"""

    print("="*80)
    print("DSPACE TO DOCID DIRECT SYNC")
    print("="*80)
    print(f"DSpace URL: {DSPACE_BASE_URL}")
    print(f"Items to sync: {NUM_ITEMS}")
    print("="*80)

    # Create Flask app context
    app = create_app()

    with app.app_context():
        # Check user exists
        user = UserAccount.query.filter_by(user_id=USER_ID).first()
        if not user:
            print(f"\n❌ User ID {USER_ID} not found in database")
            print("Please update USER_ID in the script with a valid user_id")
            return

        print(f"\n✓ Using user: {user.email}")

        # Create DSpace client
        print(f"\n🔐 Connecting to DSpace...")
        client = DSpaceClient(DSPACE_BASE_URL, DSPACE_USERNAME, DSPACE_PASSWORD)

        # Authenticate
        auth_success = client.authenticate()
        if auth_success:
            print("✓ DSpace authentication successful")
        else:
            print("⚠️ DSpace authentication failed, proceeding without auth...")

        # Fetch items
        print(f"\n📥 Fetching {NUM_ITEMS} items from DSpace (page {START_PAGE})...")
        items_data = client.get_items(page=START_PAGE, size=NUM_ITEMS)

        if not items_data:
            print("❌ Failed to fetch items from DSpace")
            return

        items = items_data.get('_embedded', {}).get('items', [])

        if not items:
            print("❌ No items found")
            return

        print(f"✓ Fetched {len(items)} items")

        # Sync each item
        print(f"\n{'='*80}")
        print(f"SYNCING {len(items)} ITEMS TO PUBLICATIONS TABLE")
        print(f"{'='*80}")

        results = {
            'total': len(items),
            'synced': 0,
            'already_exists': 0,
            'errors': 0
        }

        for idx, item_summary in enumerate(items, 1):
            uuid = item_summary.get('uuid')
            handle = item_summary.get('handle')
            name = item_summary.get('name') or 'Untitled'

            display_name = name[:60] if len(name) > 60 else name
            print(f"\n[{idx}/{len(items)}] Processing: {display_name}...")
            print(f"   UUID: {uuid}")
            print(f"   Handle: {handle}")

            try:
                # Check if already synced
                existing = DSpaceMapping.query.filter_by(dspace_uuid=uuid).first()
                if existing:
                    print(f"   ⚠️ Already synced (Publication ID: {existing.publication_id})")
                    results['already_exists'] += 1
                    continue

                # Get full item
                full_item = client.get_item(uuid)
                if not full_item:
                    print("   ❌ Failed to fetch full item")
                    results['errors'] += 1
                    continue

                # Transform metadata
                mapped_data = DSpaceMetadataMapper.dspace_to_docid(full_item, USER_ID)

                # Get resource type
                resource_type_name = mapped_data['publication'].get('resource_type', 'Text')
                resource_type = ResourceTypes.query.filter_by(resource_type=resource_type_name).first()
                resource_type_id = resource_type.id if resource_type else 1

                # Generate DOCiD
                document_docid = f"20.500.DSPACE/{uuid}"

                # Create publication
                publication = Publications(
                    user_id=USER_ID,
                    document_title=mapped_data['publication']['document_title'],
                    document_description=mapped_data['publication'].get('document_description', ''),
                    resource_type_id=resource_type_id,
                    doi='',
                    document_docid=document_docid,
                    owner='DSpace Repository',
                )

                db.session.add(publication)
                db.session.flush()  # Get publication ID

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

                print(f"   ✅ Synced successfully!")
                print(f"      Publication ID: {publication.id}")
                print(f"      DOCiD: {document_docid}")

                # Show authors
                creators = mapped_data.get('creators', [])
                if creators:
                    print(f"      Authors: {', '.join([c['creator_name'] for c in creators[:3]])}")
                    if len(creators) > 3:
                        print(f"               ... and {len(creators) - 3} more")

                results['synced'] += 1

            except Exception as e:
                db.session.rollback()
                print(f"   ❌ Error: {str(e)}")
                results['errors'] += 1

        # Summary
        print(f"\n{'='*80}")
        print("SYNC SUMMARY")
        print(f"{'='*80}")
        print(f"📊 Total items: {results['total']}")
        print(f"✅ Synced successfully: {results['synced']}")
        print(f"⚠️ Already existed: {results['already_exists']}")
        print(f"❌ Failed: {results['errors']}")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    try:
        sync_dspace_items()
    except KeyboardInterrupt:
        print("\n\n⚠️ Sync interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
