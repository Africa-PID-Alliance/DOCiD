#!/usr/bin/env python3
"""Ingest Prof. Mary Abukutsa-Onyango's collections from a CSV manifest.

Reads a CSV with rows describing each PDF file, then for each row:
- Creates a Publications record (user_id=147, owner='PROF MARY ABUKUTSA-ONYANGO')
- Mints a DOCiD handle via Cordra (IdentifierService.generate_handle)
- Creates a PublicationFiles record pointing to the PDF on the server
- Creates a PublicationCreators record with affiliation='JKUAT'

Assumes PDFs are already uploaded to the server at --files-base-url
(e.g. https://your-domain.example/uploads/abukutsa/).

Usage:
    PYTHONPATH=. python3 ingest_abukutsa_collections.py --manifest manifest.csv --files-base-url https://your-domain.example/uploads/abukutsa/ --dry-run
    PYTHONPATH=. python3 ingest_abukutsa_collections.py --manifest manifest.csv --files-base-url https://your-domain.example/uploads/abukutsa/
"""
import argparse
import csv
import os
import sys
import time
from urllib.parse import quote

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import (
    Publications, PublicationFiles, PublicationCreators,
    CreatorsRoles, UserAccount,
)
from app.service_identifiers import IdentifierService

ABUKUTSA_USER_ID = 147
ABUKUTSA_OWNER = 'PROF MARY ABUKUTSA-ONYANGO'
DEFAULT_PUBLICATION_TYPE_ID = 1  # "Article" — best available match


def sanitize_url_segment(filename):
    """URL-encode filename for use in file_url."""
    return quote(filename)


def find_author_role_id():
    author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
    return author_role.role_id if author_role else None


def ingest_row(row, files_base_url, author_role_id, dry_run=False):
    """Ingest a single manifest row. Returns (status, pub_id_or_reason)."""
    title = row['title'].strip()
    filename = row['filename'].strip()
    description = row['description'].strip()
    resource_type_id = int(row['resource_type_id'])

    # Idempotency — skip if a publication with the same title already exists for this user
    existing = Publications.query.filter_by(
        user_id=ABUKUTSA_USER_ID,
        document_title=title[:255]
    ).first()
    if existing:
        return ('skipped', f'already exists (pub_id={existing.id}, docid={existing.document_docid})')

    if dry_run:
        return ('dry-run', f'would create "{title[:60]}..." from {filename}')

    # 1. Create Publications
    publication = Publications(
        user_id=ABUKUTSA_USER_ID,
        document_title=title[:255],
        document_description=description,
        owner=ABUKUTSA_OWNER,
        resource_type_id=resource_type_id,
        document_docid='pending',  # temporary, overwritten below
    )
    db.session.add(publication)
    db.session.flush()  # get publication.id

    # 2. Mint DOCiD via Cordra
    minted_docid = IdentifierService.generate_handle()
    if not minted_docid:
        db.session.rollback()
        return ('error', f'Cordra mint failed for "{title[:60]}"')
    publication.document_docid = minted_docid

    # 3. Create PublicationFiles
    file_url = f"{files_base_url.rstrip('/')}/{sanitize_url_segment(filename)}"
    pub_file = PublicationFiles(
        publication_id=publication.id,
        title=title[:255],
        description=description,
        publication_type_id=DEFAULT_PUBLICATION_TYPE_ID,
        file_name=filename[:255],
        file_type='application/pdf',
        file_url=file_url[:255],
        identifier=minted_docid[:100],
        generated_identifier=minted_docid[:100],
    )
    db.session.add(pub_file)

    # 4. Create PublicationCreators
    family_name = (row.get('family_name') or '').strip()
    given_name = (row.get('given_name') or '').strip()
    orcid = (row.get('orcid') or '').strip()
    affiliation = (row.get('affiliation') or '').strip() or None

    identifier_url = f'https://orcid.org/{orcid}' if orcid else ''
    identifier_type = 'orcid' if orcid else ''

    creator = PublicationCreators(
        publication_id=publication.id,
        family_name=family_name[:255] or 'Unknown',
        given_name=given_name[:255],
        identifier=identifier_url[:500],
        identifier_type=identifier_type[:50],
        role_id=author_role_id,
        affiliation=affiliation,
    )
    db.session.add(creator)

    db.session.commit()
    return ('created', f'pub_id={publication.id}, docid={minted_docid}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True, help='Path to manifest CSV')
    parser.add_argument('--files-base-url', required=True,
                        help='Base URL where PDFs are hosted (e.g. https://your-domain.example/uploads/abukutsa/)')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        # Sanity check
        user = UserAccount.query.get(ABUKUTSA_USER_ID)
        if not user:
            print(f"ERROR: user_id={ABUKUTSA_USER_ID} does not exist")
            sys.exit(1)
        print(f"Ingesting as: {user.full_name} <{user.email}> (user_id={user.user_id})")

        author_role_id = find_author_role_id()
        if not author_role_id:
            print("ERROR: 'Author' role not found in creators_roles")
            sys.exit(1)

        with open(args.manifest, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"Manifest has {len(rows)} items")
        print(f"Files base URL: {args.files_base_url}")
        if args.dry_run:
            print("DRY RUN — no changes will be made")
        print()

        for idx, row in enumerate(rows, 1):
            status, detail = ingest_row(row, args.files_base_url, author_role_id, dry_run=args.dry_run)
            print(f"  [{idx:>2}/{len(rows)}] {status:>7}: {row['filename'][:40]:<40} -> {detail}")
            if status == 'created':
                time.sleep(0.5)  # be polite to Cordra

        print()
        print("Done.")


if __name__ == '__main__':
    main()
