#!/usr/bin/env python3
"""Repair publication files whose Crossref DOI is stored inconsistently.

A Crossref file should look the way the create flow saves it:
identifier='3' (the CrossRef type id), the DOI in generated_identifier, and
the DOI again in external_identifier with external_identifier_type='DOI'.
The public DOCiD page labels a file from `identifier`, and the edit page
recognises Crossref from `external_identifier`, so a row that has only one
half shows up as "APA Handle iD" somewhere.

Two shapes are repaired:
  * Saved by edit mode before the fix: the DOI is in external_identifier but
    the row says identifier='1' with the handle as generated_identifier.
    -> identifier='3', generated_identifier=<DOI>. The handle stays in
       handle_identifier.
    Only APA Handle rows (identifier='1') are considered. The create flow
    also stores DataCite files (identifier='2') with their DOI in
    external_identifier, and those are already labelled correctly. A row is
    skipped, with a warning, when the handle it shows is not also saved in
    handle_identifier, so the only copy of a handle is never overwritten.
  * Older Crossref rows: identifier='3' with the DOI in generated_identifier
    but no external_identifier.
    -> external_identifier=<DOI>, external_identifier_type='DOI'.

Idempotent and non-destructive: rows already in the right shape, and rows
whose value is not a real 10.xxxx/... DOI, are left alone. Nothing is deleted.

Usage:
    python3 backfill_file_crossref_identifiers.py           # dry run: list what would change
    python3 backfill_file_crossref_identifiers.py --apply   # write the changes
"""
import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import or_

from app import create_app, db
from app.models import PublicationFiles
from app.routes.publications import coerce_real_doi

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('backfill_file_crossref_identifiers')

APA_HANDLE_TYPE_ID = '1'
CROSSREF_TYPE_ID = '3'


def _shown_handle_is_saved(row):
    """True when replacing generated_identifier loses nothing: it is empty or
    holds the same handle that handle_identifier keeps."""
    saved = (row.handle_identifier or '').strip()
    shown = (row.generated_identifier or '').strip()
    return bool(saved) and shown in ('', saved)


def planned_changes():
    """Return [(row, {column: (old, new)})] for every row that needs repair."""
    plans = []

    edit_mode_rows = PublicationFiles.query.filter(
        PublicationFiles.identifier == APA_HANDLE_TYPE_ID,
        PublicationFiles.external_identifier_type == 'DOI',
        PublicationFiles.external_identifier.isnot(None),
    ).order_by(PublicationFiles.id).all()
    for row in edit_mode_rows:
        doi = coerce_real_doi(row.external_identifier)
        if not doi:
            continue
        if not _shown_handle_is_saved(row):
            logger.warning(
                f"file {row.id} (publication {row.publication_id}): generated_identifier "
                f"{row.generated_identifier!r} is not saved in handle_identifier "
                f"{row.handle_identifier!r}; left alone so the handle is not lost"
            )
            continue
        target = {'identifier': CROSSREF_TYPE_ID, 'generated_identifier': doi}
        diff = {k: (getattr(row, k), v) for k, v in target.items() if getattr(row, k) != v}
        if diff:
            plans.append((row, diff))

    older_crossref_rows = PublicationFiles.query.filter(
        PublicationFiles.identifier == CROSSREF_TYPE_ID,
        or_(PublicationFiles.external_identifier.is_(None), PublicationFiles.external_identifier == ''),
    ).order_by(PublicationFiles.id).all()
    for row in older_crossref_rows:
        doi = coerce_real_doi(row.generated_identifier)
        if not doi:
            logger.warning(
                f"file {row.id}: identifier=3 but generated_identifier {row.generated_identifier!r} "
                f"is not a DOI; left alone"
            )
            continue
        target = {
            'external_identifier': doi,
            'external_identifier_type': 'DOI',
            'generated_identifier': doi,
        }
        diff = {k: (getattr(row, k), v) for k, v in target.items() if getattr(row, k) != v}
        if diff:
            plans.append((row, diff))

    return plans


def run(apply=False):
    plans = planned_changes()
    for row, diff in plans:
        summary = ', '.join(f"{k}: {old!r} -> {new!r}" for k, (old, new) in diff.items())
        logger.info(f"file {row.id} (publication {row.publication_id}): {summary}")
        if apply:
            for column, (_, new) in diff.items():
                setattr(row, column, new)
    if apply:
        db.session.commit()
        logger.info(f"Repaired {len(plans)} file row(s).")
    else:
        db.session.rollback()
        logger.info(f"Dry run: {len(plans)} file row(s) would change. Re-run with --apply to write.")
    return len(plans)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--apply', action='store_true', help='write the changes (default is a dry run)')
    args = parser.parse_args()
    app = create_app()
    with app.app_context():
        run(apply=args.apply)


if __name__ == '__main__':
    main()
