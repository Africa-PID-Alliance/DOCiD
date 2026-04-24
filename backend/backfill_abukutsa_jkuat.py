#!/usr/bin/env python3
"""Backfill JKUAT organization on every Prof. Abukutsa publication.

Idempotent: if a publication already has an organization with the JKUAT ROR,
skip it. Otherwise insert a new PublicationOrganization row.

Usage:
    PYTHONPATH=. python3 backfill_abukutsa_jkuat.py --dry-run
    PYTHONPATH=. python3 backfill_abukutsa_jkuat.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Publications, PublicationOrganization

ABUKUTSA_USER_ID = 147
JKUAT_ROR = 'https://ror.org/05x2td459'
JKUAT_NAME = 'Jomo Kenyatta University of Agriculture and Technology'


def backfill(dry_run=False):
    app = create_app()
    with app.app_context():
        pubs = (
            Publications.query
            .filter_by(user_id=ABUKUTSA_USER_ID)
            .order_by(Publications.id)
            .all()
        )
        print(f"Found {len(pubs)} publications for user_id={ABUKUTSA_USER_ID}")

        created = 0
        skipped = 0
        for pub in pubs:
            existing = PublicationOrganization.query.filter_by(
                publication_id=pub.id,
                identifier=JKUAT_ROR,
            ).first()
            if existing:
                skipped += 1
                print(f"  [{pub.id}] skipped — JKUAT already attached (org_id={existing.id})")
                continue

            if dry_run:
                created += 1
                print(f"  [{pub.id}] DRY RUN — would add JKUAT org to {pub.document_docid}")
                continue

            org = PublicationOrganization(
                publication_id=pub.id,
                name=JKUAT_NAME[:255],
                type='Education',
                other_name='JKUAT',
                country='Kenya',
                identifier_type='ror',
                identifier=JKUAT_ROR,
                rrid=None,
            )
            db.session.add(org)
            created += 1
            print(f"  [{pub.id}] added JKUAT org to {pub.document_docid}")

        if not dry_run:
            db.session.commit()
        print(f"\nDone: {created} created, {skipped} skipped")


if __name__ == '__main__':
    backfill(dry_run='--dry-run' in sys.argv)
