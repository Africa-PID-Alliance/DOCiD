#!/usr/bin/env python3
"""Backfill SHA-256 checksums for existing PublicationFiles / PublicationDocuments.

For every file/document row whose checksum has not yet been computed, resolve the
stored bytes and record a SHA-256 fingerprint + size. External URLs (video links,
DataCite/DSpace/Figshare targets) are marked ``external_not_supported`` rather than
downloaded — DOCiD only hashes bytes it hosts locally under /uploads.

Idempotent and safe to re-run:
  * Rows already ``verified`` are skipped unless --recheck is passed.
  * On --recheck, an existing hash is NEVER silently overwritten; a mismatch is
    logged as a potential integrity event and left for a human to inspect.
  * No rows are deleted; nothing destructive.

Usage:
    python3 backfill_checksums.py                 # dry-run, report what would change
    python3 backfill_checksums.py --apply         # write checksums
    python3 backfill_checksums.py --apply --limit 100
    python3 backfill_checksums.py --apply --recheck   # re-verify already-hashed rows
"""
import argparse
import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import PublicationFiles, PublicationDocuments
from app.utils_checksum import (
    checksum_for_stored_file,
    STATUS_VERIFIED,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('backfill_checksums')

MODELS = (
    ('publications_files', PublicationFiles),
    ('publication_documents', PublicationDocuments),
)


def _needs_backfill(row, recheck):
    if recheck:
        return True
    # Not yet computed: no status, or status pending, or verified-but-missing-hash.
    if row.checksum_status is None:
        return True
    if row.checksum_status != STATUS_VERIFIED:
        # Re-attempt transient failures / missing bytes on each run; leave
        # external_not_supported alone (bytes will never be local).
        return row.checksum_status != 'external_not_supported'
    return False


def _apply_result(row, result, recheck):
    """Populate checksum columns from a computed result. Returns an event label
    for logging. Never overwrites an existing verified hash silently on recheck.
    """
    now = datetime.utcnow()
    row.checksum_last_checked_at = now

    new_hash = result['checksum']

    if recheck and row.checksum and new_hash and row.checksum != new_hash:
        # Integrity event — do NOT overwrite. Flag it for a human.
        logger.warning(
            'INTEGRITY MISMATCH id=%s url=%s stored=%s recomputed=%s — NOT overwriting',
            row.id, row.file_url, row.checksum, new_hash,
        )
        row.checksum_status = 'failed'
        row.checksum_error = f'recheck mismatch: stored={row.checksum} recomputed={new_hash}'
        return 'MISMATCH'

    row.checksum_algorithm = result['checksum_algorithm']
    row.checksum_status = result['checksum_status']
    row.checksum_error = result['checksum_error']
    if new_hash:
        row.checksum = new_hash
        row.file_size = result['file_size']
        row.checksum_generated_at = now
    return result['checksum_status']


def backfill(apply_changes, limit, recheck):
    counts = {}
    processed = 0

    for table_name, model in MODELS:
        query = model.query.order_by(model.id)
        for row in query.yield_per(200):
            if limit is not None and processed >= limit:
                break
            if not _needs_backfill(row, recheck):
                continue

            result = checksum_for_stored_file(row.file_url)
            label = f'{table_name}:{result["checksum_status"]}'

            if apply_changes:
                outcome = _apply_result(row, result, recheck)
                label = f'{table_name}:{outcome}'

            counts[label] = counts.get(label, 0) + 1
            processed += 1
            logger.info(
                '%s id=%s status=%s size=%s url=%s',
                table_name, row.id, result['checksum_status'],
                result['file_size'], (row.file_url or '')[:80],
            )

        if limit is not None and processed >= limit:
            break

    if apply_changes:
        db.session.commit()
        logger.info('Committed checksum updates.')
    else:
        db.session.rollback()
        logger.info('DRY-RUN — no changes written. Re-run with --apply.')

    logger.info('Processed %s rows. Breakdown: %s', processed, counts)


def main():
    parser = argparse.ArgumentParser(description='Backfill SHA-256 checksums for stored files.')
    parser.add_argument('--apply', action='store_true', help='Write changes (default: dry-run).')
    parser.add_argument('--limit', type=int, default=None, help='Process at most N rows total.')
    parser.add_argument('--recheck', action='store_true',
                        help='Re-verify already-hashed rows; logs mismatches without overwriting.')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        backfill(apply_changes=args.apply, limit=args.limit, recheck=args.recheck)


if __name__ == '__main__':
    main()
