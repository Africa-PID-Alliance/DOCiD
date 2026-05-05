#!/usr/bin/env python3
"""Check what metadata fields DSpace items have for publications missing creators."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Publications, PublicationCreators, DSpaceMapping
from app.routes.dspace_legacy import get_dspace_legacy_client, DSPACE_LEGACY_URL

app = create_app()
with app.app_context():
    results = db.session.query(Publications.id, Publications.document_title, DSpaceMapping.dspace_uuid).join(
        DSpaceMapping, DSpaceMapping.publication_id == Publications.id
    ).filter(
        Publications.owner == 'Stellenbosch University',
        ~Publications.id.in_(db.session.query(PublicationCreators.publication_id).distinct())
    ).limit(5).all()

    client = get_dspace_legacy_client()
    client.authenticate()

    for pub_id, title, uuid in results:
        item_id = uuid.replace('legacy-item-', '') if uuid.startswith('legacy-item-') else uuid
        resp = client.session.get(
            f'{DSPACE_LEGACY_URL}/rest/items/{item_id}',
            params={'expand': 'metadata'},
            timeout=15
        )
        if resp.status_code != 200:
            print(f"pub_id={pub_id}: HTTP {resp.status_code}")
            continue

        item = resp.json()
        meta = item.get('metadata', [])
        print(f"\n=== pub_id={pub_id} title='{title}' ===")
        contributor_keys = [e for e in meta if 'contributor' in e.get('key', '') or 'creator' in e.get('key', '')]
        if contributor_keys:
            for e in contributor_keys:
                print(f"  {e.get('key')}: {e.get('value')}")
        else:
            print("  NO contributor/creator fields found")
            all_keys = sorted(set(e.get('key') for e in meta))
            print(f"  All keys: {all_keys}")

    client.logout()
