#!/usr/bin/env python3
"""
Backfill creators for Stellenbosch University DSpace publications.

Directly fetches metadata for each publication using the DSpace UUID
stored in dspace_mappings, then saves creators.

Usage:
  python3 backfill_creators.py [--dry_run] [--batch_size 50]
"""
import argparse
import sys
import os
import time
import re
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Publications, PublicationCreators, DSpaceMapping, CreatorsRoles
from app.routes.dspace_legacy import get_dspace_legacy_client, DSPACE_LEGACY_URL


def strip_date_from_name(name):
    """Remove date ranges like ', 1894-1979', ', 1909-', '1870-1950.' from names."""
    cleaned = re.sub(r',?\s*\d{4}-?\d{0,4}\.?\s*$', '', name).strip()
    return cleaned if cleaned else name


def extract_authors_from_metadata(metadata_list):
    """Extract author names from DSpace 6.x metadata list."""
    authors = []
    if not metadata_list:
        return authors
    for entry in metadata_list:
        key = entry.get('key', '')
        if key == 'dc.contributor.author':
            value = entry.get('value', '').strip()
            if value:
                authors.append(value)
    return authors


def backfill_creators(dry_run=False, batch_size=50):
    app = create_app()
    with app.app_context():
        # Get Author role
        author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
        if not author_role:
            print("[ERROR] 'Author' role not found in creators_roles table!")
            return
        author_role_id = author_role.role_id
        print(f"[INFO] Author role_id = {author_role_id}")

        # Get Stellenbosch publications missing creators, with their DSpace UUIDs
        results = db.session.query(
            Publications.id, DSpaceMapping.dspace_uuid
        ).join(
            DSpaceMapping, DSpaceMapping.publication_id == Publications.id
        ).filter(
            Publications.owner == 'Stellenbosch University',
            ~Publications.id.in_(
                db.session.query(PublicationCreators.publication_id).distinct()
            )
        ).all()

        print(f"[INFO] Found {len(results)} publications without creators")
        if not results:
            print("[INFO] Nothing to do!")
            return

        # Authenticate with DSpace
        client = get_dspace_legacy_client()
        if not client.authenticate():
            print("[ERROR] Failed to authenticate with DSpace")
            return
        print("[INFO] Authenticated with DSpace Legacy")

        total_created = 0
        total_skipped = 0
        total_errors = 0

        for idx, (publication_id, dspace_uuid) in enumerate(results, 1):
            # Extract the actual UUID (strip 'legacy-item-' prefix if present)
            item_id = dspace_uuid
            if dspace_uuid.startswith('legacy-item-'):
                item_id = dspace_uuid[len('legacy-item-'):]

            try:
                # Fetch item metadata from DSpace
                resp = client.session.get(
                    f"{DSPACE_LEGACY_URL}/rest/items/{item_id}",
                    params={'expand': 'metadata'},
                    timeout=15
                )
                if resp.status_code != 200:
                    print(f"  [{idx}/{len(results)}] SKIP pub_id={publication_id} uuid={item_id} (HTTP {resp.status_code})")
                    total_skipped += 1
                    continue

                item_data = resp.json()
                metadata_list = item_data.get('metadata', [])
                authors = extract_authors_from_metadata(metadata_list)

                if not authors:
                    total_skipped += 1
                    if idx % 50 == 0:
                        print(f"  [{idx}/{len(results)}] Progress: {total_created} created, {total_skipped} skipped, {total_errors} errors")
                    continue

                if dry_run:
                    print(f"  [{idx}/{len(results)}] DRY RUN pub_id={publication_id}: {len(authors)} authors")
                    total_created += len(authors)
                    continue

                # Save creators
                for author_name in authors:
                    author_name = strip_date_from_name(author_name)
                    name_parts = author_name.split(',', 1) if ',' in author_name else author_name.rsplit(' ', 1)
                    if len(name_parts) == 2:
                        family_name = strip_date_from_name(name_parts[0].strip())
                        given_name = strip_date_from_name(name_parts[1].strip())
                    else:
                        family_name = strip_date_from_name(author_name.strip())
                        given_name = ''

                    db.session.add(PublicationCreators(
                        publication_id=publication_id,
                        family_name=family_name,
                        given_name=given_name,
                        identifier='',
                        identifier_type='',
                        role_id=author_role_id
                    ))

                total_created += len(authors)

                if idx % batch_size == 0:
                    db.session.commit()
                    print(f"  [{idx}/{len(results)}] Committed batch. Total creators: {total_created}")

                # Small delay
                time.sleep(0.3)

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                print(f"  [{idx}/{len(results)}] CONN ERROR pub_id={publication_id}: {type(e).__name__}")
                total_errors += 1
                time.sleep(3)
                # Re-authenticate in case session dropped
                try:
                    client.authenticate()
                except Exception:
                    pass
            except Exception as e:
                db.session.rollback()
                total_errors += 1
                print(f"  [{idx}/{len(results)}] ERROR pub_id={publication_id}: {e}")

        # Final commit
        if not dry_run:
            db.session.commit()

        client.logout()

        print(f"\n{'='*60}")
        print(f"DONE: {total_created} creator records added, {total_skipped} skipped, {total_errors} errors")
        print(f"{'='*60}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backfill creators for Stellenbosch publications')
    parser.add_argument('--dry_run', action='store_true', help='Preview without saving')
    parser.add_argument('--batch_size', type=int, default=50, help='Commit every N items')
    args = parser.parse_args()
    backfill_creators(dry_run=args.dry_run, batch_size=args.batch_size)
