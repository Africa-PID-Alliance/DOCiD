#!/usr/bin/env python3
"""Backfill affiliation='Stellenbosch University' for Stellenbosch creators.

Usage:
    PYTHONPATH=. python backfill_stellenbosch_affiliation.py --dry-run
    PYTHONPATH=. python backfill_stellenbosch_affiliation.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Publications, PublicationCreators


def backfill(dry_run=False):
    app = create_app()
    with app.app_context():
        # Get Stellenbosch publication IDs first (avoids bulk-update-with-join limitation)
        stellenbosch_pub_ids = [
            row[0] for row in db.session.query(Publications.id)
            .filter(Publications.owner == 'Stellenbosch University')
            .all()
        ]
        print(f"Found {len(stellenbosch_pub_ids)} Stellenbosch publications")

        if not stellenbosch_pub_ids:
            return

        creators_to_update = (
            db.session.query(PublicationCreators)
            .filter(PublicationCreators.publication_id.in_(stellenbosch_pub_ids))
            .filter(
                (PublicationCreators.affiliation.is_(None))
                | (PublicationCreators.affiliation == '')
            )
        )

        count = creators_to_update.count()
        print(f"Found {count} Stellenbosch creators without affiliation")

        if count == 0:
            return

        if dry_run:
            print("DRY RUN — no changes made")
            sample = creators_to_update.limit(5).all()
            for creator in sample:
                print(f"  would update creator id={creator.id} "
                      f"({creator.given_name} {creator.family_name}) "
                      f"publication_id={creator.publication_id}")
            return

        updated = creators_to_update.update(
            {PublicationCreators.affiliation: 'Stellenbosch University'},
            synchronize_session=False
        )
        db.session.commit()
        print(f"Updated {updated} rows")


if __name__ == '__main__':
    dry = '--dry-run' in sys.argv
    backfill(dry_run=dry)
