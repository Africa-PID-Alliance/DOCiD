#!/usr/bin/env python3
"""
Direct DSpace Legacy (6.x) to DOCiD sync using Flask app context

Bypasses API authentication for direct database access.
Use this for bulk syncing from DSpace 6.x repositories.
"""

from app import create_app, db
from app.models import Publications, DSpaceMapping, ResourceTypes, UserAccount
from app.service_dspace_legacy import DSpaceLegacyClient, DSpaceLegacyMetadataMapper
import sys

# Configuration - UPDATE THESE FOR YOUR DSPACE LEGACY INSTANCE
DSPACE_LEGACY_URL = "http://localhost:8080"  # Your DSpace 6.x URL
DSPACE_EMAIL = ""  # Email for authentication (optional)
DSPACE_PASSWORD = ""  # Password for authentication (optional)
NUM_ITEMS = 10  # Number of items to fetch
OFFSET = 0  # Starting offset

# User ID to assign publications to
USER_ID = 1  # Default admin user


def sync_dspace_legacy_items():
    """Sync DSpace Legacy items directly to database"""

    print("="*80)
    print("DSPACE LEGACY (6.x) TO DOCID DIRECT SYNC")
    print("="*80)
    print(f"DSpace URL: {DSPACE_LEGACY_URL}")
    print(f"Items to sync: {NUM_ITEMS}")
    print(f"Starting offset: {OFFSET}")
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

        # Create DSpace Legacy client
        print(f"\n🔐 Connecting to DSpace Legacy...")
        client = DSpaceLegacyClient(
            base_url=DSPACE_LEGACY_URL,
            email=DSPACE_EMAIL,
            password=DSPACE_PASSWORD
        )

        # Test connection
        if not client.test_connection():
            print("❌ Failed to connect to DSpace Legacy")
            print("Please check:")
            print("  - DSPACE_LEGACY_URL is correct")
            print("  - DSpace server is running")
            print("  - REST API is enabled")
            return

        print("✓ Connection successful")

        # Authenticate (if credentials provided)
        if DSPACE_EMAIL and DSPACE_PASSWORD:
            print(f"🔐 Authenticating...")
            auth_success = client.authenticate()
            if auth_success:
                print("✓ DSpace authentication successful")
            else:
                print("⚠️ DSpace authentication failed, proceeding without auth...")
        else:
            print("ℹ️  No credentials provided, proceeding without authentication")

        # Fetch items
        print(f"\n📥 Fetching {NUM_ITEMS} items from DSpace Legacy (offset {OFFSET})...")
        items = client.get_items(limit=NUM_ITEMS, offset=OFFSET)

        if not items:
            print("❌ Failed to fetch items from DSpace Legacy")
            if client.token:
                client.logout()
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
            item_id = item_summary.get('id')
            handle = item_summary.get('handle', f'legacy/{item_id}')
            name = item_summary.get('name') or 'Untitled'

            display_name = name[:60] if len(name) > 60 else name
            print(f"\n[{idx}/{len(items)}] Processing: {display_name}...")
            print(f"   Item ID: {item_id}")
            print(f"   Handle: {handle}")

            try:
                # Check if already synced
                existing = DSpaceMapping.query.filter_by(dspace_handle=handle).first()
                if existing:
                    print(f"   ⚠️ Already synced (Publication ID: {existing.publication_id})")
                    results['already_exists'] += 1
                    continue

                # Get full item
                full_item = client.get_item(item_id)
                if not full_item:
                    print("   ❌ Failed to fetch full item")
                    results['errors'] += 1
                    continue

                # Transform metadata
                mapped_data = DSpaceLegacyMetadataMapper.dspace_to_docid(full_item, USER_ID)

                # Get resource type
                resource_type_name = mapped_data['publication'].get('resource_type', 'Text')
                resource_type = ResourceTypes.query.filter_by(resource_type=resource_type_name).first()
                resource_type_id = resource_type.id if resource_type else 1

                # Generate DOCiD
                document_docid = f"20.500.DSPACE-LEGACY/{item_id}"

                # Create publication
                publication = Publications(
                    user_id=USER_ID,
                    document_title=mapped_data['publication']['document_title'],
                    document_description=mapped_data['publication'].get('document_description', ''),
                    resource_type_id=resource_type_id,
                    doi='',
                    document_docid=document_docid,
                    owner='DSpace Legacy Repository',
                )

                db.session.add(publication)
                db.session.flush()  # Get publication ID

                # Create mapping
                metadata_hash = client.calculate_metadata_hash(full_item.get('metadata', []))
                mapping = DSpaceMapping(
                    dspace_handle=handle,
                    dspace_uuid=f"legacy-item-{item_id}",
                    dspace_url=DSPACE_LEGACY_URL,
                    publication_id=publication.id,
                    sync_status='synced',
                    dspace_metadata_hash=metadata_hash
                )

                db.session.add(mapping)
                db.session.commit()

                print(f"   ✅ Synced successfully!")
                print(f"      Publication ID: {publication.id}")
                print(f"      DOCiD: {document_docid}")

                # Show authors
                creators = mapped_data.get('creators', [])
                if creators:
                    print(f"      Authors: {', '.join([c['creator_name'] for c in creators[:3]])}...")
                    if len(creators) > 3:
                        print(f"               ... and {len(creators) - 3} more")

                results['synced'] += 1

            except Exception as e:
                db.session.rollback()
                print(f"   ❌ Error: {str(e)}")
                results['errors'] += 1

        # Cleanup
        if client.token:
            client.logout()

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
        sync_dspace_legacy_items()
    except KeyboardInterrupt:
        print("\n\n⚠️ Sync interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
