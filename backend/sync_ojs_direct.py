#!/usr/bin/env python3
"""
Direct OJS to DOCiD sync using Flask app context
Bypasses API authentication for direct database access

Usage:
    python sync_ojs_direct.py                           # Sync published submissions
    python sync_ojs_direct.py --status 4                # Sync only published (status 4)
    python sync_ojs_direct.py --ids 123 124 125         # Import specific submission IDs
    python sync_ojs_direct.py --count 50                # Import 50 items
    python sync_ojs_direct.py --search "machine learning"  # Search and import

OJS Submission Status Codes:
    1 = queued (in review)
    3 = scheduled
    4 = published
    5 = declined
"""

import os
import sys
import argparse
from app import create_app, db
from app.models import Publications, ResourceTypes, UserAccount, PublicationCreators, CreatorsRoles
from app.service_ojs import OJSClient, OJSMetadataMapper

# Configuration from environment
OJS_BASE_URL = os.getenv('OJS_BASE_URL', 'https://your-ojs-instance.com/api/v1')
OJS_API_KEY = os.getenv('OJS_API_KEY', '')

# Default settings
DEFAULT_COUNT = 10
DEFAULT_USER_ID = 1
DEFAULT_STATUS = 4  # Published submissions


def save_ojs_creators(publication_id: int, creators_data: list):
    """
    Save creators from OJS submission to publication_creators table

    Args:
        publication_id: Publication ID
        creators_data: List of creator dictionaries from OJSMetadataMapper
    """
    if not creators_data:
        return 0

    created_count = 0
    for creator_data in creators_data:
        # Get role_id for the creator role
        role_name = creator_data.get('creator_role', 'Author')
        role = CreatorsRoles.query.filter_by(role_name=role_name).first()

        if not role:
            role = CreatorsRoles.query.filter_by(role_name='Author').first()

        if not role:
            continue

        # Parse full name into family_name and given_name
        full_name = creator_data.get('creator_name', '')
        name_parts = full_name.split(',', 1) if ',' in full_name else full_name.rsplit(' ', 1)

        if len(name_parts) == 2:
            if ',' in full_name:
                family_name = name_parts[0].strip()
                given_name = name_parts[1].strip()
            else:
                given_name = name_parts[0].strip()
                family_name = name_parts[1].strip()
        else:
            family_name = full_name.strip()
            given_name = ''

        # Handle ORCID identifier
        orcid_id = creator_data.get('orcid_id', '') or ''
        identifier_value = f"https://orcid.org/{orcid_id}" if orcid_id else ''
        identifier_type_value = 'orcid' if orcid_id else ''

        creator = PublicationCreators(
            publication_id=publication_id,
            family_name=family_name,
            given_name=given_name,
            identifier=identifier_value,
            identifier_type=identifier_type_value,
            role_id=role.role_id
        )
        db.session.add(creator)
        created_count += 1

    return created_count


def sync_ojs_submissions(submission_ids: list = None, search: str = None,
                         status: int = DEFAULT_STATUS, count: int = DEFAULT_COUNT,
                         user_id: int = DEFAULT_USER_ID, skip_existing: bool = True):
    """
    Sync OJS submissions directly to database

    Args:
        submission_ids: List of specific submission IDs to import
        search: Search phrase to filter submissions
        status: Submission status filter (4=published by default)
        count: Number of items to sync
        user_id: User ID to assign publications to
        skip_existing: Skip submissions that already exist in database
    """

    print("=" * 80)
    print("OJS TO DOCID DIRECT SYNC")
    print("=" * 80)
    print(f"OJS URL: {OJS_BASE_URL}")
    print(f"API Key: {'Configured' if OJS_API_KEY else 'Not configured'}")

    if not OJS_API_KEY:
        print("\n[ERROR] OJS API key is required for accessing submissions")
        print("Please set OJS_API_KEY in your environment or .env file")
        return

    if submission_ids:
        print(f"Import mode: Specific IDs ({len(submission_ids)} submissions)")
    else:
        print(f"Status filter: {status} (1=queued, 3=scheduled, 4=published, 5=declined)")
        if search:
            print(f"Search phrase: {search}")
        print(f"Items to sync: {count}")

    print("=" * 80)

    # Create Flask app context
    app = create_app()

    with app.app_context():
        # Check user exists
        user = UserAccount.query.filter_by(user_id=user_id).first()
        if not user:
            print(f"\n[ERROR] User ID {user_id} not found in database")
            print("Please update user_id with a valid user_id")
            return

        print(f"\n[OK] Using user: {user.email}")

        # Create OJS client
        print(f"\n[INFO] Connecting to OJS...")
        client = OJSClient(OJS_BASE_URL, OJS_API_KEY)

        # Test connection
        connection_status = client.test_connection()
        if connection_status.get('status') == 'connected':
            print("[OK] OJS connection successful")
        elif connection_status.get('status') == 'not_configured':
            print(f"[ERROR] OJS not configured: {connection_status.get('message', 'Unknown error')}")
            return
        else:
            print(f"[WARNING] OJS connection issue: {connection_status.get('error', 'Unknown')}")
            print("Proceeding anyway...")

        # Get submissions
        submissions_to_import = []

        if submission_ids:
            print(f"\n[INFO] Fetching {len(submission_ids)} specific submissions...")
            for submission_id in submission_ids:
                submission = client.get_submission(submission_id)
                if submission:
                    submissions_to_import.append(submission)
                    # Extract title from multilingual field
                    title_data = submission.get('title', {})
                    title = OJSMetadataMapper._get_localized_value(title_data) or 'Untitled'
                    print(f"   [OK] Submission {submission_id}: {title[:50]}")
                else:
                    print(f"   [ERROR] Submission {submission_id} not found")
        else:
            print(f"\n[INFO] Fetching submissions from OJS...")
            results = client.get_submissions(
                status=status,
                page=1,
                per_page=count,
                search_phrase=search if search else None
            )

            if 'error' in results:
                print(f"[ERROR] Failed to fetch submissions: {results.get('error')}")
                return

            submissions_to_import = results.get('items', [])

        if not submissions_to_import:
            print("[ERROR] No submissions found to import")
            return

        print(f"[OK] Found {len(submissions_to_import)} submissions to process")

        # Sync each submission
        print(f"\n{'=' * 80}")
        print(f"SYNCING {len(submissions_to_import)} SUBMISSIONS TO PUBLICATIONS TABLE")
        print(f"{'=' * 80}")

        results = {
            'total': len(submissions_to_import),
            'synced': 0,
            'already_exists': 0,
            'errors': 0,
            'creators_added': 0
        }

        for idx, submission in enumerate(submissions_to_import, 1):
            submission_id = submission.get('id')

            # Extract title from multilingual field
            title_data = submission.get('title', {})
            if not title_data:
                publications = submission.get('publications', [])
                if publications:
                    title_data = publications[0].get('title', {})

            title = OJSMetadataMapper._get_localized_value(title_data) or 'Untitled'

            display_title = title[:60] if len(title) > 60 else title
            print(f"\n[{idx}/{len(submissions_to_import)}] Processing: {display_title}...")
            print(f"   OJS ID: {submission_id}")
            print(f"   Status: {submission.get('status', 'Unknown')}")

            try:
                # Check if already synced
                if skip_existing:
                    existing = Publications.query.filter_by(ojs_submission_id=str(submission_id)).first()
                    if existing:
                        print(f"   [SKIP] Already synced (Publication ID: {existing.id})")
                        results['already_exists'] += 1
                        continue

                # Get full submission details if needed
                if 'publications' not in submission or not submission.get('publications'):
                    full_submission = client.get_submission(submission_id)
                    if not full_submission:
                        print("   [ERROR] Failed to fetch full submission details")
                        results['errors'] += 1
                        continue
                    submission = full_submission

                # Transform metadata
                mapped_data = OJSMetadataMapper.ojs_to_docid(submission, user_id)
                pub_data = mapped_data['publication']

                # Get resource type (OJS is primarily Text/Articles)
                resource_type = ResourceTypes.query.filter_by(resource_type='Text').first()
                resource_type_id = resource_type.id if resource_type else 1

                # Generate DOCiD using OJS DOI or create one
                ojs_doi = pub_data.get('doi', '')
                document_docid = ojs_doi if ojs_doi else f"ojs:{submission_id}"

                # Create publication
                publication = Publications(
                    user_id=user_id,
                    document_title=pub_data['document_title'],
                    document_description=pub_data.get('document_description', ''),
                    resource_type_id=resource_type_id,
                    doi=ojs_doi,
                    document_docid=document_docid,
                    ojs_submission_id=str(submission_id),
                    ojs_url=pub_data.get('ojs_url', ''),
                    owner='OJS Repository',
                )

                db.session.add(publication)
                db.session.flush()  # Get publication ID

                # Save creators
                creators_count = save_ojs_creators(publication.id, mapped_data.get('creators', []))
                results['creators_added'] += creators_count

                db.session.commit()

                print(f"   [OK] Synced successfully!")
                print(f"      Publication ID: {publication.id}")
                print(f"      DOCiD: {document_docid}")

                # Show authors
                creators = mapped_data.get('creators', [])
                if creators:
                    author_names = [c['creator_name'] for c in creators[:3]]
                    print(f"      Authors: {', '.join(author_names)}")
                    if len(creators) > 3:
                        print(f"               ... and {len(creators) - 3} more")

                # Show extended metadata
                extended = mapped_data.get('extended_metadata', {})
                if extended.get('date_published'):
                    print(f"      Published: {extended['date_published']}")
                if extended.get('pages'):
                    print(f"      Pages: {extended['pages']}")

                results['synced'] += 1

            except Exception as e:
                db.session.rollback()
                print(f"   [ERROR] {str(e)}")
                results['errors'] += 1

        # Summary
        print(f"\n{'=' * 80}")
        print("SYNC SUMMARY")
        print(f"{'=' * 80}")
        print(f"Total items: {results['total']}")
        print(f"Synced successfully: {results['synced']}")
        print(f"Creators added: {results['creators_added']}")
        print(f"Already existed: {results['already_exists']}")
        print(f"Failed: {results['errors']}")
        print(f"{'=' * 80}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Sync OJS submissions to DOCiD publications database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python sync_ojs_direct.py                           # Sync published submissions
    python sync_ojs_direct.py --status 4                # Published only (status 4)
    python sync_ojs_direct.py --status 1                # Queued submissions
    python sync_ojs_direct.py --ids 123 124 125         # Import specific submissions
    python sync_ojs_direct.py --count 50                # Import 50 items
    python sync_ojs_direct.py --search "climate"        # Search and import
    python sync_ojs_direct.py --user-id 2               # Assign to specific user

OJS Submission Status Codes:
    1 = queued (in review)
    3 = scheduled for publication
    4 = published
    5 = declined

Required Environment Variables:
    OJS_BASE_URL - OJS API base URL (e.g., https://journal.org/api/v1)
    OJS_API_KEY  - OJS API key for authentication
        """
    )

    parser.add_argument('--ids', nargs='+', type=int,
                        help='Specific submission IDs to import')
    parser.add_argument('--search', type=str,
                        help='Search phrase to filter submissions')
    parser.add_argument('--status', type=int, default=DEFAULT_STATUS,
                        help=f'Submission status filter (default: {DEFAULT_STATUS}=published)')
    parser.add_argument('--count', type=int, default=DEFAULT_COUNT,
                        help=f'Number of items to sync (default: {DEFAULT_COUNT})')
    parser.add_argument('--user-id', type=int, default=DEFAULT_USER_ID,
                        help=f'User ID to assign publications to (default: {DEFAULT_USER_ID})')
    parser.add_argument('--no-skip', action='store_true',
                        help='Re-import submissions that already exist (will create duplicates)')

    args = parser.parse_args()

    try:
        sync_ojs_submissions(
            submission_ids=args.ids,
            search=args.search,
            status=args.status,
            count=args.count,
            user_id=args.user_id,
            skip_existing=not args.no_skip
        )
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Sync interrupted by user")
    except Exception as e:
        print(f"\n\n[FATAL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
