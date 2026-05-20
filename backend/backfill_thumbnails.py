#!/usr/bin/env python3
"""Generate thumbnails for publications that have no publication_poster_url.

Walks every publication with a dspace_mapping but no poster, fetches the
ORIGINAL bitstream from the source DSpace instance, generates a JPEG
thumbnail via app.service_thumbnails, and stores the relative /uploads
path on the publication.

Usage:
    python3 backfill_thumbnails.py                    # dry-run, all sources
    python3 backfill_thumbnails.py --apply            # write changes
    python3 backfill_thumbnails.py --apply --limit 50 # process at most 50
    python3 backfill_thumbnails.py --source-id 2 --apply

Safe to re-run: skips publications that already have publication_poster_url.
Thumbnail filenames are deterministic (sha1 of bitstream bytes) so duplicate
extractions reuse the same file.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests

from app import create_app, db
from app.models import Publications, DSpaceMapping, HarvestSource
from app.service_thumbnails import generate_thumbnail_from_url, get_uploads_dir


def _dspace_base_url(source):
    """Return the DSpace REST API root for a HarvestSource."""
    return (source.base_url or '').rstrip('/')


def _find_bitstream(session, base_url, dspace_uuid):
    """Return (content_url, filename) for the item's ORIGINAL first bitstream, or None."""
    try:
        bundles = session.get(
            f"{base_url}/api/core/items/{dspace_uuid}/bundles", timeout=15
        ).json().get('_embedded', {}).get('bundles', [])
    except Exception:
        return None
    original = next((bundle for bundle in bundles if bundle.get('name') == 'ORIGINAL'), None)
    if not original:
        return None
    try:
        bitstreams = session.get(
            f"{base_url}/api/core/bundles/{original.get('uuid')}/bitstreams", timeout=15
        ).json().get('_embedded', {}).get('bitstreams', [])
    except Exception:
        return None
    if not bitstreams:
        return None
    bitstream = bitstreams[0]
    return (
        f"{base_url}/api/core/bitstreams/{bitstream.get('uuid')}/content",
        bitstream.get('name') or 'bitstream',
    )


def backfill(source_id=None, limit=None, apply_changes=False):
    app = create_app()
    with app.app_context():
        sources = HarvestSource.query.all()
        if source_id is not None:
            sources = [source for source in sources if source.id == source_id]
        if not sources:
            print(f"[ERROR] no harvest_sources found (source_id={source_id})")
            return 1

        uploads_dir = get_uploads_dir()
        print(f"[INFO] uploads_dir={uploads_dir}")
        print(f"[INFO] apply={apply_changes} limit={limit}")

        session = requests.Session()
        total_examined = 0
        total_generated = 0
        total_skipped = 0
        total_errors = 0

        for source in sources:
            base_url = _dspace_base_url(source)
            print(f"\n[SOURCE] id={source.id} name={source.name!r} base_url={base_url}")

            query = (
                db.session.query(Publications, DSpaceMapping)
                .join(DSpaceMapping, DSpaceMapping.publication_id == Publications.id)
                .filter(Publications.owner == source.owner_name)
                .filter(
                    (Publications.publication_poster_url.is_(None))
                    | (Publications.publication_poster_url == '')
                )
            )
            if limit:
                query = query.limit(limit)

            for publication, mapping in query.all():
                total_examined += 1
                bitstream = _find_bitstream(session, base_url, mapping.dspace_uuid)
                if not bitstream:
                    total_skipped += 1
                    if total_examined % 20 == 0:
                        print(f"  ... examined={total_examined} generated={total_generated} skipped={total_skipped} errors={total_errors}")
                    continue
                content_url, filename = bitstream
                if not apply_changes:
                    print(f"  [DRY] pub_id={publication.id} would fetch {content_url}")
                    total_generated += 1
                    continue
                relative_path = generate_thumbnail_from_url(content_url, filename, uploads_dir)
                if relative_path:
                    publication.publication_poster_url = relative_path
                    db.session.commit()
                    total_generated += 1
                    print(f"  ✓ pub_id={publication.id} → {relative_path} ({filename})")
                else:
                    total_errors += 1
                time.sleep(0.2)  # polite to DSpace

        print(
            f"\n[GRAND TOTAL] examined={total_examined} generated={total_generated} "
            f"skipped={total_skipped} errors={total_errors} "
            f"({'APPLIED' if apply_changes else 'DRY-RUN'})"
        )
        return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backfill publication poster thumbnails from DSpace bitstreams')
    parser.add_argument('--source-id', type=int, default=None, help='Restrict to one harvest_sources.id')
    parser.add_argument('--limit', type=int, default=None, help='Process at most N publications per source')
    parser.add_argument('--apply', action='store_true', help='Commit changes (default: dry-run)')
    args = parser.parse_args()
    sys.exit(backfill(source_id=args.source_id, limit=args.limit, apply_changes=args.apply))
