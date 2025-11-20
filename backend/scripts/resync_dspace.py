#!/usr/bin/env python3
"""
Script to delete existing DSpace synced records and sync 10 new ones
"""
import sys
import os
import requests

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import (
    DSpaceMapping, Publications, PublicationCreators,
    PublicationViews, FileDownloads, PublicationFiles, PublicationDocuments
)

def resync_dspace_items():
    """Delete existing synced items and sync 10 new ones"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("DSpace Re-sync Script")
        print("=" * 60)

        # Step 1: Delete all existing synced items
        print("\n[1/3] Deleting existing DSpace synced items...")

        mappings = DSpaceMapping.query.all()
        publication_ids = [m.publication_id for m in mappings]

        if publication_ids:
            # Delete all related records first (to avoid foreign key violations)

            # Delete publication views
            views_count = 0
            for pub_id in publication_ids:
                count = PublicationViews.query.filter_by(publication_id=pub_id).delete()
                views_count += count
            if views_count > 0:
                print(f"  - Deleted {views_count} publication views")

            # Delete file downloads (through files and documents)
            downloads_count = 0
            for pub_id in publication_ids:
                # Get file IDs and document IDs for this publication
                file_ids = [f.id for f in PublicationFiles.query.filter_by(publication_id=pub_id).all()]
                doc_ids = [d.id for d in PublicationDocuments.query.filter_by(publication_id=pub_id).all()]

                # Delete downloads for these files
                if file_ids:
                    count = FileDownloads.query.filter(FileDownloads.publication_file_id.in_(file_ids)).delete(synchronize_session=False)
                    downloads_count += count

                # Delete downloads for these documents
                if doc_ids:
                    count = FileDownloads.query.filter(FileDownloads.publication_document_id.in_(doc_ids)).delete(synchronize_session=False)
                    downloads_count += count

            if downloads_count > 0:
                print(f"  - Deleted {downloads_count} file downloads")

            # Delete publication documents
            docs_count = 0
            for pub_id in publication_ids:
                count = PublicationDocuments.query.filter_by(publication_id=pub_id).delete()
                docs_count += count
            if docs_count > 0:
                print(f"  - Deleted {docs_count} publication documents")

            # Delete publication files
            files_count = 0
            for pub_id in publication_ids:
                count = PublicationFiles.query.filter_by(publication_id=pub_id).delete()
                files_count += count
            if files_count > 0:
                print(f"  - Deleted {files_count} publication files")

            # Delete creators
            creators_count = 0
            for pub_id in publication_ids:
                count = PublicationCreators.query.filter_by(publication_id=pub_id).delete()
                creators_count += count
            if creators_count > 0:
                print(f"  - Deleted {creators_count} creators")

            # Delete publications
            Publications.query.filter(Publications.id.in_(publication_ids)).delete(synchronize_session=False)
            print(f"  - Deleted {len(publication_ids)} publications")

            # Delete mappings
            DSpaceMapping.query.delete()
            print(f"  - Deleted {len(mappings)} DSpace mappings")

            db.session.commit()
            print("✓ All existing DSpace records deleted successfully!\n")
        else:
            print("  - No existing DSpace records found\n")

        # Step 2: Get DSpace credentials from environment
        print("[2/3] Checking DSpace configuration...")
        from app.routes.dspace import DSPACE_BASE_URL, DSPACE_USERNAME, DSPACE_PASSWORD
        from app.service_dspace import DSpaceClient

        print(f"  - DSpace URL: {DSPACE_BASE_URL}")
        print(f"  - Username: {DSPACE_USERNAME}")

        # Step 3: Sync 10 new items
        print("\n[3/3] Syncing 10 new items from DSpace...")

        try:
            client = DSpaceClient(DSPACE_BASE_URL, DSPACE_USERNAME, DSPACE_PASSWORD)
            auth_success = client.authenticate()

            if not auth_success:
                print("✗ Failed to authenticate with DSpace")
                return

            print("✓ Authenticated with DSpace")

            # Get first 10 items
            items_data = client.get_items(page=0, size=10)

            if not items_data:
                print("✗ Failed to fetch items from DSpace")
                return

            items = items_data.get('_embedded', {}).get('items', [])
            print(f"✓ Found {len(items)} items to sync\n")

            # Import sync function
            from app.service_dspace import DSpaceMetadataMapper
            from app.routes.dspace import save_publication_creators
            from app.models import ResourceTypes

            # Use a test user (you can change this)
            from app.models import UserAccount
            user = UserAccount.query.first()
            if not user:
                print("✗ No users found in database. Please create a user first.")
                return

            user_id = user.user_id
            print(f"Using user: {user.email} (ID: {user_id})\n")

            synced_count = 0
            error_count = 0
            for idx, item in enumerate(items, 1):
                try:
                    uuid = item.get('uuid')
                    handle = item.get('handle')
                    name = item.get('name', 'Untitled')

                    print(f"[{idx}/10] Syncing: {name[:50]}...")
                    print(f"        UUID: {uuid}")
                    print(f"        Handle: {handle}")

                    # Get full item data
                    full_item = client.get_item(uuid)
                    if not full_item:
                        print(f"        ✗ Failed to fetch item details\n")
                        error_count += 1
                        continue

                    # Transform metadata
                    mapped_data = DSpaceMetadataMapper.dspace_to_docid(full_item, user_id)

                    # Get resource type
                    resource_type_name = mapped_data['publication'].get('resource_type', 'Text')
                    resource_type = ResourceTypes.query.filter_by(resource_type=resource_type_name).first()
                    resource_type_id = resource_type.id if resource_type else 1

                    # Create publication - use DSpace handle as document_docid
                    document_docid = handle if handle else f"20.500.DSPACE/{uuid}"

                    # Construct full resolvable URL for handle_url
                    handle_url = None
                    if handle:
                        base_url = DSPACE_BASE_URL.replace('/server', '')
                        handle_url = f"{base_url}/handle/{handle}"

                    publication = Publications(
                        user_id=user_id,
                        document_title=mapped_data['publication']['document_title'],
                        document_description=mapped_data['publication'].get('document_description', ''),
                        resource_type_id=resource_type_id,
                        doi=handle if handle else '',
                        document_docid=document_docid,  # DSpace handle (not full URL)
                        handle_url=handle_url,  # Full resolvable URL for DSpace item
                        owner='DSpace Repository',
                    )

                    db.session.add(publication)
                    db.session.flush()

                    # Save creators
                    creators = mapped_data.get('creators', [])
                    if creators:
                        save_publication_creators(publication.id, creators)
                        print(f"        ✓ Saved {len(creators)} creators")

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

                    print(f"        ✓ Synced successfully (Publication ID: {publication.id})\n")
                    synced_count += 1

                except Exception as e:
                    db.session.rollback()
                    error_count += 1
                    print(f"        ✗ Error: {str(e)}\n")

            print("=" * 60)
            print(f"✓ Re-sync completed!")
            print(f"  - Successfully synced: {synced_count}/10 items")
            print(f"  - Errors: {error_count}/10 items")
            print("=" * 60)

        except Exception as e:
            print(f"\n✗ Fatal error during sync: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    resync_dspace_items()
