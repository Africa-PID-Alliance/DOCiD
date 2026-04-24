#!/usr/bin/env python3
"""Ingest the 10 items from UNILAG's Special Collections into DOCiD.

Collection: https://ir.unilag.edu.ng/collections/d22b183d-10bd-4081-903b-d09c311f737c
Delivered by Prof. Okiki on 2026-04-22 as the pilot set for the new UNILAG integration.

Each item:
  - Creates a Publications row (user_id=146, owner='University of Lagos', resource_type=Cultural Heritage)
  - Mints a DOCiD via Cordra (IdentifierService.generate_handle)
  - Creates PublicationCreators rows with affiliation='University of Lagos'
  - Creates a DSpaceMapping row for dedup on re-runs

Idempotent by DSpaceMapping.dspace_uuid — safe to re-run.

Usage:
    PYTHONPATH=. python3 ingest_unilag_special_collections.py --dry-run
    PYTHONPATH=. python3 ingest_unilag_special_collections.py
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import (
    Publications, PublicationCreators, DSpaceMapping,
    ResourceTypes, CreatorsRoles, UserAccount,
)
from app.service_dspace import DSpaceClient, DSpaceMetadataMapper
from app.service_identifiers import IdentifierService

COLLECTION_UUID = 'd22b183d-10bd-4081-903b-d09c311f737c'
UNILAG_USER_ID = 146
UNILAG_OWNER = 'University of Lagos'
DSPACE_API_BASE = 'https://api-ir.unilag.edu.ng/server'
DSPACE_UI_BASE = 'https://ir.unilag.edu.ng'
CULTURAL_HERITAGE_RESOURCE_TYPE_ID = 3


def fetch_collection_items(client: DSpaceClient, collection_uuid: str):
    """Return list of item stubs in the given collection via discover/search."""
    all_items = []
    page = 0
    while True:
        path = f"/discover/search/objects?scope={collection_uuid}&dsoType=item&size=20&page={page}"
        response = client.session.get(f"{client.api_url}{path}", timeout=30)
        response.raise_for_status()
        data = response.json()
        objects = (
            data.get('_embedded', {})
            .get('searchResult', {})
            .get('_embedded', {})
            .get('objects', [])
        )
        if not objects:
            break
        for obj in objects:
            indexable = obj.get('_embedded', {}).get('indexableObject', {})
            if indexable.get('type') == 'item':
                all_items.append(indexable)
        page_info = data.get('_embedded', {}).get('searchResult', {}).get('page', {})
        if page + 1 >= page_info.get('totalPages', 0):
            break
        page += 1
    return all_items


def ingest_item(client, item_stub, author_role_id, dry_run=False):
    """Ingest a single DSpace item. Returns (status, detail)."""
    item_uuid = item_stub.get('uuid')
    handle = item_stub.get('handle')

    existing = DSpaceMapping.query.filter_by(dspace_uuid=item_uuid).first()
    if existing:
        return ('skipped', f'already synced (pub_id={existing.publication_id})')

    if dry_run:
        return ('dry-run', f'would ingest "{(item_stub.get("name") or "")[:60]}" uuid={item_uuid}')

    full_item = client.get_item(item_uuid)
    if not full_item:
        return ('error', f'could not fetch full metadata for {item_uuid}')

    collection_name = None
    try:
        owning = client.get_item_owning_collection(item_uuid)
        if owning:
            collection_name = owning.get('name')
    except Exception:
        collection_name = 'Special Collections'

    mapped = DSpaceMetadataMapper.dspace_to_docid(
        full_item, user_id=UNILAG_USER_ID, collection_name=collection_name
    )
    pub_data = mapped.get('publication', {})

    handle_url = f"{DSPACE_UI_BASE}/handle/{handle}" if handle else None

    savepoint = db.session.begin_nested()
    try:
        publication = Publications(
            user_id=UNILAG_USER_ID,
            document_title=(pub_data.get('document_title') or 'Untitled')[:255],
            document_description=pub_data.get('document_description', ''),
            document_docid=handle,  # temporary — overwritten below
            doi=pub_data.get('doi'),
            handle_url=handle_url,
            collection_name=collection_name or 'Special Collections',
            owner=UNILAG_OWNER,
            resource_type_id=CULTURAL_HERITAGE_RESOURCE_TYPE_ID,
            avatar=(pub_data.get('avatar_url') or '')[:255] or None,
        )
        db.session.add(publication)
        db.session.flush()

        minted = IdentifierService.generate_handle()
        if minted:
            publication.document_docid = minted
        else:
            publication.document_docid = handle  # fallback to DSpace handle

        for creator_data in mapped.get('creators', []):
            family_name = (creator_data.get('family_name') or '')[:255]
            given_name = (creator_data.get('given_name') or '')[:255]
            if family_name or given_name:
                creator = PublicationCreators(
                    publication_id=publication.id,
                    family_name=family_name or 'Unknown',
                    given_name=given_name,
                    role_id=author_role_id,
                    affiliation=UNILAG_OWNER,
                )
                db.session.add(creator)

        dspace_mapping = DSpaceMapping(
            dspace_uuid=item_uuid,
            dspace_handle=handle,
            dspace_url=handle_url,
            publication_id=publication.id,
            sync_status='synced',
        )
        db.session.add(dspace_mapping)

        savepoint.commit()
        db.session.commit()
        return ('created', f'pub_id={publication.id}, docid={publication.document_docid}')
    except Exception as error:
        try:
            savepoint.rollback()
        except Exception:
            db.session.rollback()
        return ('error', f'{error}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        user = UserAccount.query.get(UNILAG_USER_ID)
        if not user:
            print(f'ERROR: user_id={UNILAG_USER_ID} does not exist')
            sys.exit(1)
        print(f'Ingesting as: {user.full_name} <{user.email}> (user_id={user.user_id})')

        author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
        if not author_role:
            print('ERROR: Author role not found')
            sys.exit(1)
        author_role_id = author_role.role_id

        client = DSpaceClient(DSPACE_API_BASE)
        items = fetch_collection_items(client, COLLECTION_UUID)
        print(f'Fetched {len(items)} items from Special Collections ({COLLECTION_UUID})')
        if args.dry_run:
            print('DRY RUN — no changes will be made')
        print()

        for idx, item in enumerate(items, 1):
            status, detail = ingest_item(client, item, author_role_id, dry_run=args.dry_run)
            title_snippet = (item.get('name') or '')[:50]
            print(f'  [{idx:>2}/{len(items)}] {status:>7}: {title_snippet:<50} -> {detail}')
            if status == 'created':
                time.sleep(0.3)  # be polite to Cordra + DSpace

        print()
        print('Done.')


if __name__ == '__main__':
    main()
