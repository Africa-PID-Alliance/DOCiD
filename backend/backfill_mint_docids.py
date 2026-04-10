#!/usr/bin/env python3
"""
Backfill: Mint DOCiD identifiers for publications that still have raw DSpace handles.

Targets publications whose document_docid looks like a DSpace handle (e.g. 123456789/7027)
rather than a minted Cordra handle (e.g. 20.500.14351/abc123).

Usage:
    PYTHONPATH=. python backfill_mint_docids.py --owner "University of Lagos" --dry-run
    PYTHONPATH=. python backfill_mint_docids.py --owner "University of Lagos"
"""
import argparse
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Publications
from app.service_identifiers import IdentifierService


def backfill_mint(owner_filter, dry_run=False):
    app = create_app()
    with app.app_context():
        # Find publications with DSpace-style handles (not already minted)
        pubs = Publications.query.filter(
            Publications.owner == owner_filter,
            ~Publications.document_docid.like('20.500.%')
        ).order_by(Publications.id).all()

        print(f"Found {len(pubs)} publications needing minted DOCiDs (owner={owner_filter})")

        if not pubs:
            print("Nothing to do.")
            return

        minted_count = 0
        failed_count = 0

        for idx, pub in enumerate(pubs, 1):
            old_docid = pub.document_docid

            if dry_run:
                print(f"  [{idx}/{len(pubs)}] DRY RUN: pub {pub.id} ({old_docid}) would be minted")
                minted_count += 1
                continue

            new_docid = IdentifierService.generate_handle()
            if new_docid:
                pub.document_docid = new_docid
                db.session.commit()
                minted_count += 1
                print(f"  [{idx}/{len(pubs)}] MINTED: pub {pub.id}: {old_docid} -> {new_docid}")
            else:
                failed_count += 1
                print(f"  [{idx}/{len(pubs)}] FAILED: pub {pub.id} ({old_docid}) — Cordra mint returned None")

            time.sleep(0.1)  # Be polite to Cordra

        print(f"\nDone: {minted_count} minted, {failed_count} failed, {len(pubs)} total")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backfill DOCiD identifiers for publications with raw DSpace handles')
    parser.add_argument('--owner', required=True, help='Owner name filter (e.g. "University of Lagos")')
    parser.add_argument('--dry-run', action='store_true', help='Preview without minting')
    args = parser.parse_args()

    backfill_mint(owner_filter=args.owner, dry_run=args.dry_run)
