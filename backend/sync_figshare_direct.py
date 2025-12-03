#!/usr/bin/env python3
"""
Direct Figshare to DOCiD sync using Flask app context
Bypasses API authentication for direct database access

Usage:
    python sync_figshare_direct.py                    # Search with default query
    python sync_figshare_direct.py "climate data"    # Search with custom query
    python sync_figshare_direct.py --ids 12345 12346 # Import specific article IDs
    python sync_figshare_direct.py --count 50        # Import 50 items
"""

import os
import sys
import argparse
from app import create_app, db
from app.models import Publications, ResourceTypes, UserAccount, PublicationCreators, CreatorsRoles
from app.service_figshare import FigshareClient, FigshareMetadataMapper

# Configuration from environment
FIGSHARE_BASE_URL = os.getenv('FIGSHARE_BASE_URL', 'https://api.figshare.com/v2')
FIGSHARE_API_TOKEN = os.getenv('FIGSHARE_API_TOKEN', '')

# Default settings
DEFAULT_QUERY = "research data"
DEFAULT_COUNT = 10
DEFAULT_USER_ID = 1


def save_figshare_creators(publication_id: int, creators_data: list):
    """
    Save creators from Figshare article to publication_creators table

    Args:
        publication_id: Publication ID
        creators_data: List of creator dictionaries from FigshareMetadataMapper
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


def sync_figshare_items(query: str = None, article_ids: list = None,
                        count: int = DEFAULT_COUNT, user_id: int = DEFAULT_USER_ID,
                        item_type: int = None, skip_existing: bool = True):
    """
    Sync Figshare articles directly to database

    Args:
        query: Search query string
        article_ids: List of specific article IDs to import
        count: Number of items to sync
        user_id: User ID to assign publications to
        item_type: Figshare item type filter (3=dataset, 9=software, etc.)
        skip_existing: Skip articles that already exist in database
    """

    print("=" * 80)
    print("FIGSHARE TO DOCID DIRECT SYNC")
    print("=" * 80)
    print(f"Figshare URL: {FIGSHARE_BASE_URL}")
    print(f"API Token: {'Configured' if FIGSHARE_API_TOKEN else 'Not configured (using public API)'}")

    if article_ids:
        print(f"Import mode: Specific IDs ({len(article_ids)} articles)")
    else:
        print(f"Search query: {query or DEFAULT_QUERY}")
        print(f"Items to sync: {count}")
        if item_type:
            print(f"Item type filter: {item_type}")

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

        # Create Figshare client
        print(f"\n[INFO] Connecting to Figshare...")
        token = FIGSHARE_API_TOKEN if FIGSHARE_API_TOKEN else None
        client = FigshareClient(FIGSHARE_BASE_URL, token)

        # Test connection
        connection_status = client.test_connection()
        if connection_status.get('status') == 'connected':
            print("[OK] Figshare connection successful")
        else:
            print(f"[WARNING] Figshare connection issue: {connection_status.get('error', 'Unknown')}")
            print("Proceeding anyway...")

        # Get articles
        articles_to_import = []

        if article_ids:
            print(f"\n[INFO] Fetching {len(article_ids)} specific articles...")
            for article_id in article_ids:
                article = client.get_article(article_id)
                if article:
                    articles_to_import.append(article)
                    print(f"   [OK] Article {article_id}: {article.get('title', 'Unknown')[:50]}")
                else:
                    print(f"   [ERROR] Article {article_id} not found")
        else:
            search_query = query or DEFAULT_QUERY
            print(f"\n[INFO] Searching Figshare for '{search_query}'...")
            search_results = client.search_articles(
                query=search_query,
                page=1,
                page_size=count,
                item_type=item_type
            )
            articles_to_import = search_results.get('articles', [])

        if not articles_to_import:
            print("[ERROR] No articles found to import")
            return

        print(f"[OK] Found {len(articles_to_import)} articles to process")

        # Sync each article
        print(f"\n{'=' * 80}")
        print(f"SYNCING {len(articles_to_import)} ARTICLES TO PUBLICATIONS TABLE")
        print(f"{'=' * 80}")

        results = {
            'total': len(articles_to_import),
            'synced': 0,
            'already_exists': 0,
            'errors': 0,
            'creators_added': 0
        }

        for idx, article_summary in enumerate(articles_to_import, 1):
            article_id = article_summary.get('id')
            title = article_summary.get('title', 'Untitled')

            display_title = title[:60] if len(title) > 60 else title
            print(f"\n[{idx}/{len(articles_to_import)}] Processing: {display_title}...")
            print(f"   Figshare ID: {article_id}")

            try:
                # Check if already synced
                if skip_existing:
                    existing = Publications.query.filter_by(figshare_article_id=str(article_id)).first()
                    if existing:
                        print(f"   [SKIP] Already synced (Publication ID: {existing.id})")
                        results['already_exists'] += 1
                        continue

                # Get full article details if we only have summary
                if 'description' not in article_summary:
                    article = client.get_article(article_id)
                    if not article:
                        print("   [ERROR] Failed to fetch full article details")
                        results['errors'] += 1
                        continue
                else:
                    article = article_summary

                # Transform metadata
                mapped_data = FigshareMetadataMapper.figshare_to_docid(article, user_id)
                pub_data = mapped_data['publication']

                # Get resource type
                resource_type_name = pub_data.get('resource_type', 'Dataset')
                resource_type = ResourceTypes.query.filter_by(resource_type=resource_type_name).first()
                resource_type_id = resource_type.id if resource_type else 1

                # Generate DOCiD using Figshare DOI or create one
                figshare_doi = pub_data.get('doi', '')
                document_docid = figshare_doi if figshare_doi else f"figshare:{article_id}"

                # Create publication
                publication = Publications(
                    user_id=user_id,
                    document_title=pub_data['document_title'],
                    document_description=pub_data.get('document_description', ''),
                    resource_type_id=resource_type_id,
                    doi=figshare_doi,
                    document_docid=document_docid,
                    figshare_article_id=str(article_id),
                    figshare_url=pub_data.get('figshare_url', ''),
                    owner='Figshare Repository',
                )

                db.session.add(publication)
                db.session.flush()  # Get publication ID

                # Save creators
                creators_count = save_figshare_creators(publication.id, mapped_data.get('creators', []))
                results['creators_added'] += creators_count

                db.session.commit()

                print(f"   [OK] Synced successfully!")
                print(f"      Publication ID: {publication.id}")
                print(f"      DOCiD: {document_docid}")
                print(f"      Type: {resource_type_name}")

                # Show authors
                creators = mapped_data.get('creators', [])
                if creators:
                    author_names = [c['creator_name'] for c in creators[:3]]
                    print(f"      Authors: {', '.join(author_names)}")
                    if len(creators) > 3:
                        print(f"               ... and {len(creators) - 3} more")

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
        description='Sync Figshare articles to DOCiD publications database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python sync_figshare_direct.py                       # Default search
    python sync_figshare_direct.py "machine learning"   # Custom search query
    python sync_figshare_direct.py --ids 12345 12346    # Import specific articles
    python sync_figshare_direct.py --count 50           # Import 50 items
    python sync_figshare_direct.py --type 3             # Import only datasets
    python sync_figshare_direct.py --user-id 2          # Assign to specific user

Item types:
    1=figure, 2=media, 3=dataset, 4=fileset, 5=poster,
    6=journal contribution, 7=presentation, 8=thesis,
    9=software, 11=online resource, 12=preprint, 13=book,
    14=conference contribution, 15=chapter, 16=peer review,
    17=educational resource
        """
    )

    parser.add_argument('query', nargs='?', default=DEFAULT_QUERY,
                        help=f'Search query (default: "{DEFAULT_QUERY}")')
    parser.add_argument('--ids', nargs='+', type=int,
                        help='Specific article IDs to import')
    parser.add_argument('--count', type=int, default=DEFAULT_COUNT,
                        help=f'Number of items to sync (default: {DEFAULT_COUNT})')
    parser.add_argument('--user-id', type=int, default=DEFAULT_USER_ID,
                        help=f'User ID to assign publications to (default: {DEFAULT_USER_ID})')
    parser.add_argument('--type', type=int, dest='item_type',
                        help='Filter by Figshare item type')
    parser.add_argument('--no-skip', action='store_true',
                        help='Re-import articles that already exist (will create duplicates)')

    args = parser.parse_args()

    try:
        sync_figshare_items(
            query=args.query,
            article_ids=args.ids,
            count=args.count,
            user_id=args.user_id,
            item_type=args.item_type,
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
