#!/usr/bin/env python3
"""Backfill publications.user_id to match the official institutional account
linked to the harvest_source they came from.

Matches publications → harvest_source via publications.owner = harvest_sources.owner_name
(the harvester writes owner_name into publications.owner on every insert).

Defaults to dry-run. Pass --apply to commit changes.

Usage:
    python3 backfill_harvest_user_ids.py                 # dry-run, all sources
    python3 backfill_harvest_user_ids.py --source-id 2   # dry-run, one source
    python3 backfill_harvest_user_ids.py --apply         # commit
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import HarvestSource, Publications


def backfill(source_id=None, apply_changes=False):
    app = create_app()
    with app.app_context():
        sources_query = HarvestSource.query
        if source_id is not None:
            sources_query = sources_query.filter_by(id=source_id)
        sources = sources_query.all()
        if not sources:
            print(f"[ERROR] No harvest_sources found (source_id={source_id})")
            return 1

        grand_total = 0
        for source in sources:
            source.resolve_owner()
            if not source.owner_user_id:
                print(f"[SKIP] source.id={source.id} ({source.name!r}) — owner_user_id unresolved "
                      f"(owner_email={source.owner_email!r})")
                continue

            # Find publications attributed to this source but on the wrong user_id.
            mismatched = Publications.query.filter(
                Publications.owner == source.owner_name,
                Publications.user_id != source.owner_user_id,
            )
            count_by_user = {}
            for pub in mismatched.with_entities(Publications.user_id).all():
                count_by_user[pub.user_id] = count_by_user.get(pub.user_id, 0) + 1
            total = sum(count_by_user.values())
            grand_total += total

            print(f"\n[SOURCE] id={source.id} name={source.name!r} owner_user_id={source.owner_user_id}")
            if not total:
                print("  ✓ already correct, nothing to do")
                continue
            print(f"  → {total} publications need reattribution to user_id={source.owner_user_id}")
            for current_user_id, count in sorted(count_by_user.items(), key=lambda kv: -kv[1]):
                print(f"      from user_id={current_user_id}: {count}")

            if apply_changes:
                updated = mismatched.update(
                    {Publications.user_id: source.owner_user_id},
                    synchronize_session=False,
                )
                db.session.commit()
                print(f"  ✓ APPLIED — {updated} rows updated")
            else:
                print("  (dry-run — no changes committed; pass --apply to commit)")

        print(f"\n[GRAND TOTAL] {grand_total} publications {'updated' if apply_changes else 'would be updated'}")
        return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backfill publications.user_id from harvest_sources.owner_user_id')
    parser.add_argument('--source-id', type=int, default=None, help='Restrict to one harvest_sources.id')
    parser.add_argument('--apply', action='store_true', help='Commit changes (default: dry-run)')
    args = parser.parse_args()
    sys.exit(backfill(source_id=args.source_id, apply_changes=args.apply))
