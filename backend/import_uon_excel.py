#!/usr/bin/env python3
"""
Import University of Nairobi (UoN) curated DSpace metadata from Excel exports.

UoN filtered their DSpace 7 repository into themed spreadsheets and sent us the
resulting `search-results.xlsx` files. This importer works purely offline from
those files -- it never calls the UoN API -- so a run is fully reproducible from
the zip the client supplied.

Two things about the DSpace Excel export shape drive most of the code here:

1. Columns are splintered by language qualifier. A single logical field arrives
   as `dc.title`, `dc.title[en]`, `dc.title[en_US]` and `dc.title[]`, with any
   given row populating only one of them. `_coalesce_row_metadata` folds the
   variants back into the canonical field name so the existing
   DSpaceMetadataMapper (which expects live-API shaped metadata) can be reused
   verbatim rather than reimplemented.

2. Repeated values are `||`-joined, and authority-controlled fields carry
   `Name::authority-uuid::confidence`. Both are normalised away before mapping.

Theme membership is the curation the client actually paid attention to, so it is
preserved: an item appearing in both the Traditional Knowledge and Indigenous
Knowledge sheets is imported once with both themes recorded in collection_name.

Usage:
    python scripts/import_uon_excel.py --source-dir /path/to/unzipped --dry-run
    python scripts/import_uon_excel.py --source-dir /path/to/unzipped
    python scripts/import_uon_excel.py --source-dir /path/to/unzipped --mint
"""

import argparse
import glob
import logging
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openpyxl

from app import create_app, db
from app.models import (
    CreatorsRoles,
    DSpaceMapping,
    Publications,
    PublicationCreators,
    PublicationOrganization,
    ResourceTypes,
    UserAccount,
)
from app.service_dspace import DSpaceMetadataMapper
from app.service_identifiers import IdentifierService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('import_uon')

OWNER_EMAIL = 'journals@uonbi.ac.ke'
OWNER_NAME = 'University of Nairobi'

# UoN's live DSpace 7 UI resolves an item by UUID. The dc.identifier.uri values
# in these spreadsheets are stale legacy XMLUI URLs (:8080/xmlui/handle/123456789/...)
# that now 404, so the UUID -- present on every row -- is the reliable link.
UON_ITEM_URL_TEMPLATE = 'https://erepository.uonbi.ac.ke/items/{uuid}'

# Every item in these exports is a University of Nairobi repository output, so UoN
# is recorded as the affiliated organization on each one. Values are taken from
# UoN's ROR record (https://api.ror.org/v2/organizations/02y9nww90) rather than
# typed by hand, so the identifier, type and ISNI are authoritative.
UON_ORGANIZATION = dict(
    name='University of Nairobi',
    type='education',
    other_name='UON',
    country='Kenya',
    identifier='https://ror.org/02y9nww90',
    identifier_type='ror',
    isni='0000 0001 2019 0495',
)

# Handle prefixes that belong to UoN. Legacy exports carry the DSpace default
# `123456789`; the live repository has since been assigned `11295`. Any other
# prefix (1887, 10568 CGSpace, 10986 World Bank, ...) is an EXTERNAL publisher
# URI that happens to sit in dc.identifier.uri and must not be treated as a
# UoN handle.
UON_HANDLE_PREFIX = '11295'
UON_LEGACY_HANDLE_PREFIXES = {'123456789', '11295'}

VALUE_SEPARATOR = '||'

# "Traditional Knowledge (Articles) search-results (5).xlsx" -> theme, genre
FILENAME_PATTERN = re.compile(r'^(?P<theme>.+?)\s*\((?P<genre>[^)]+)\)\s*search-results')


def clean_text(raw_value):
    """Normalise a single cell value: strip Excel's escaped CR and collapse space."""
    if raw_value is None:
        return ''
    text = str(raw_value)
    # openpyxl surfaces carriage returns from the DSpace export as a literal
    # `_x000D_` escape rather than an actual control character.
    text = text.replace('_x000D_', '\n').replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def strip_authority(value):
    """Drop DSpace authority control suffixes: `Name::uuid::confidence` -> `Name`."""
    return value.split('::', 1)[0].strip()


def split_values(raw_value):
    """Split a `||`-joined DSpace export cell into clean, deduplicated values."""
    text = clean_text(raw_value)
    if not text:
        return []
    seen_values = []
    for part in text.split(VALUE_SEPARATOR):
        cleaned = strip_authority(clean_text(part)).rstrip(',').strip()
        if cleaned and cleaned not in seen_values:
            seen_values.append(cleaned)
    return seen_values


def canonical_field_name(column_header):
    """`dc.title[en_US]` -> `dc.title`; `dc.rights[*]` -> `dc.rights`."""
    return re.sub(r'\[[^\]]*\]$', '', str(column_header)).strip()


def parse_theme_and_genre(file_path):
    """Derive the curated theme and content genre from the export filename."""
    basename = os.path.basename(file_path)
    match = FILENAME_PATTERN.match(basename)
    if not match:
        return None, None
    return match.group('theme').strip(), match.group('genre').strip()


def _coalesce_row_metadata(row_values, column_headers):
    """
    Fold language-splintered export columns into live-API shaped DSpace metadata.

    Returns `{canonical_field: [{'value': v}, ...]}`, which is exactly what
    DSpaceMetadataMapper._get_metadata_value(s) reads.
    """
    coalesced_values = {}
    for column_header, cell_value in zip(column_headers, row_values):
        if column_header in (None, 'id', 'collection'):
            continue
        field_name = canonical_field_name(column_header)
        if not field_name:
            continue
        bucket = coalesced_values.setdefault(field_name, [])
        for value in split_values(cell_value):
            if value not in bucket:
                bucket.append(value)
    return {
        field_name: [{'value': value} for value in values]
        for field_name, values in coalesced_values.items()
        if values
    }


def derive_uon_handle(metadata, item_uuid):
    """
    Work out the item's UoN handle from dc.identifier.uri, remapping the legacy
    `123456789` prefix onto the live `11295` one.

    Falls back to a UUID-scoped value because dspace_mappings.dspace_handle is
    NOT NULL + UNIQUE and roughly a third of these rows carry no URI at all.
    """
    for uri_entry in metadata.get('dc.identifier.uri', []):
        match = re.search(r'handle/([^/\s]+)/(\d+)', uri_entry.get('value', ''))
        if match and match.group(1) in UON_LEGACY_HANDLE_PREFIXES:
            return f'{UON_HANDLE_PREFIX}/{match.group(2)}'
    return f'{UON_HANDLE_PREFIX}/uuid-{item_uuid}'


def read_curated_items(source_dir):
    """
    Read every export in `source_dir` and return uuid -> record, deduplicated.

    The same item legitimately appears in more than one themed sheet; each
    occurrence contributes its theme and genre to the single merged record.
    """
    curated_items = {}
    export_paths = sorted(glob.glob(os.path.join(source_dir, '*.xlsx')))
    if not export_paths:
        raise SystemExit(f'No .xlsx exports found in {source_dir}')

    for export_path in export_paths:
        theme, genre = parse_theme_and_genre(export_path)
        if not theme:
            logger.warning(f'Skipping unrecognised filename: {os.path.basename(export_path)}')
            continue

        workbook = openpyxl.load_workbook(export_path, read_only=True, data_only=True)
        worksheet = workbook.active
        row_iterator = worksheet.iter_rows(values_only=True)
        column_headers = list(next(row_iterator))
        row_count = 0

        for row_values in row_iterator:
            row_map = dict(zip(column_headers, row_values))
            item_uuid = clean_text(row_map.get('id'))
            if not item_uuid:
                continue
            row_count += 1

            existing_record = curated_items.get(item_uuid)
            if existing_record:
                existing_record['themes'].add(theme)
                existing_record['genres'].add(genre)
                continue

            metadata = _coalesce_row_metadata(row_values, column_headers)
            title = clean_text(row_map.get('dc.title[en]') or row_map.get('dc.title') or '')
            if not title:
                title_entries = metadata.get('dc.title', [])
                title = title_entries[0]['value'] if title_entries else 'Untitled'

            curated_items[item_uuid] = {
                'uuid': item_uuid,
                'metadata': metadata,
                'title': title,
                'collection_handle': clean_text(row_map.get('collection')),
                'themes': {theme},
                'genres': {genre},
            }

        workbook.close()
        logger.info(f'{os.path.basename(export_path)}: {row_count} rows [{theme} / {genre}]')

    return curated_items


def build_dspace_item(record):
    """Shape a curated record as the DSpace item dict the shared mapper expects."""
    return {
        'uuid': record['uuid'],
        'handle': derive_uon_handle(record['metadata'], record['uuid']),
        'name': record['title'],
        'metadata': record['metadata'],
    }


def ensure_uon_organization(publication_ids):
    """
    Attach the UoN organization to every given publication that lacks it.

    Split out from the create path so it also repairs publications imported by an
    earlier run, and so it stays idempotent: publications that already carry the
    ROR row are left untouched.
    """
    if not publication_ids:
        return 0

    already_linked = {
        organization.publication_id
        for organization in PublicationOrganization.query.filter(
            PublicationOrganization.publication_id.in_(publication_ids),
            PublicationOrganization.identifier == UON_ORGANIZATION['identifier'],
        ).all()
    }

    added_count = 0
    for publication_id in publication_ids:
        if publication_id in already_linked:
            continue
        db.session.add(PublicationOrganization(publication_id=publication_id, **UON_ORGANIZATION))
        added_count += 1

    if added_count:
        db.session.commit()
    return added_count


def import_items(source_dir, dry_run=False, limit=None, mint=False):
    curated_items = read_curated_items(source_dir)
    logger.info(f'{len(curated_items)} unique items after dedup across themed sheets')

    owner = UserAccount.query.filter(
        db.func.lower(UserAccount.email) == OWNER_EMAIL.lower()
    ).first()
    if not owner:
        raise SystemExit(
            f'Owner account {OWNER_EMAIL} not found. Refusing to import -- publications '
            'would otherwise be silently attributed to the wrong user.'
        )
    logger.info(f'Importing as user_id={owner.user_id} ({owner.email})')

    resource_type_ids = {rt.resource_type: rt.id for rt in ResourceTypes.query.all()}
    default_resource_type_id = resource_type_ids.get('Text', 1)
    author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
    author_role_id = author_role.role_id if author_role else None

    records = list(curated_items.values())
    if limit:
        records = records[:limit]

    results = {'total': len(records), 'created': 0, 'skipped': 0, 'errors': 0, 'organizations_added': 0}

    existing_uuids = {
        mapping.dspace_uuid
        for mapping in DSpaceMapping.query.filter(
            DSpaceMapping.dspace_uuid.in_([r['uuid'] for r in records])
        ).all()
    } if records else set()

    for index, record in enumerate(records, 1):
        item_uuid = record['uuid']
        if item_uuid in existing_uuids:
            results['skipped'] += 1
            continue

        dspace_item = build_dspace_item(record)
        collection_name = '; '.join(sorted(record['themes']))

        if dry_run:
            mapped = DSpaceMetadataMapper.dspace_to_docid(
                dspace_item, user_id=owner.user_id, collection_name=collection_name
            )
            logger.info(
                f"[{index}/{len(records)}] DRY RUN {dspace_item['handle']} :: "
                f"{mapped['publication']['document_title'][:70]} :: "
                f"{len(mapped['creators'])} creators :: {collection_name}"
            )
            results['created'] += 1
            continue

        savepoint = db.session.begin_nested()
        try:
            mapped = DSpaceMetadataMapper.dspace_to_docid(
                dspace_item, user_id=owner.user_id, collection_name=collection_name
            )
            publication_data = mapped['publication']
            resource_type_id = resource_type_ids.get(
                publication_data.get('resource_type', 'Text'), default_resource_type_id
            )

            publication = Publications(
                user_id=owner.user_id,
                document_title=(publication_data.get('document_title') or 'Untitled')[:255],
                document_description=publication_data.get('document_description', ''),
                document_docid=f'uon/{item_uuid}',
                doi=publication_data.get('doi'),
                handle_url=UON_ITEM_URL_TEMPLATE.format(uuid=item_uuid),
                collection_name=collection_name[:500],
                owner=OWNER_NAME,
                resource_type_id=resource_type_id,
            )
            db.session.add(publication)
            db.session.flush()

            # Minting is opt-in: it calls out to Cordra and burns a real handle,
            # which must not happen during a local test run.
            if mint:
                minted_docid = IdentifierService.generate_handle()
                if minted_docid:
                    publication.document_docid = minted_docid
                else:
                    logger.warning(f'Cordra mint failed for {item_uuid}; keeping placeholder docid')

            for creator_data in mapped.get('creators', []):
                family_name = (creator_data.get('family_name') or '')[:255]
                given_name = (creator_data.get('given_name') or '')[:255]
                if family_name or given_name:
                    db.session.add(PublicationCreators(
                        publication_id=publication.id,
                        family_name=family_name or 'Unknown',
                        given_name=given_name,
                        role_id=author_role_id or 'Author',
                    ))

            db.session.add(DSpaceMapping(
                dspace_uuid=item_uuid,
                dspace_handle=dspace_item['handle'],
                dspace_url=UON_ITEM_URL_TEMPLATE.format(uuid=item_uuid),
                publication_id=publication.id,
                sync_status='synced',
            ))

            savepoint.commit()
            results['created'] += 1
            if results['created'] % 100 == 0:
                db.session.commit()
                logger.info(f"Committed {results['created']} publications so far")

        except Exception as item_error:
            try:
                savepoint.rollback()
            except Exception:
                db.session.rollback()
            results['errors'] += 1
            logger.error(f'Error importing {item_uuid}: {item_error}')

    if not dry_run:
        db.session.commit()

        # Backfill across every UoN publication, not just the ones created in this
        # run, so rows imported before organizations were recorded get repaired.
        uon_publication_ids = [
            publication.id
            for publication in Publications.query.filter_by(user_id=owner.user_id).all()
        ]
        results['organizations_added'] = ensure_uon_organization(uon_publication_ids)
        logger.info(f"Organization rows added: {results['organizations_added']}")

    return results


def main():
    parser = argparse.ArgumentParser(description='Import UoN curated DSpace Excel exports into DOCiD')
    parser.add_argument('--source-dir', required=True, help='Directory holding the unzipped *.xlsx exports')
    parser.add_argument('--dry-run', action='store_true', help='Parse and report without writing to the database')
    parser.add_argument('--limit', type=int, help='Import at most N items (for testing)')
    parser.add_argument('--mint', action='store_true', help='Mint real DOCiD handles via Cordra (off by default)')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        results = import_items(
            source_dir=args.source_dir,
            dry_run=args.dry_run,
            limit=args.limit,
            mint=args.mint,
        )

    logger.info('=' * 60)
    logger.info(f"Total considered : {results['total']}")
    logger.info(f"Created          : {results['created']}")
    logger.info(f"Skipped (exists) : {results['skipped']}")
    logger.info(f"Errors           : {results['errors']}")
    logger.info(f"Orgs attached    : {results['organizations_added']}")
    logger.info('=' * 60)
    return 1 if results['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
