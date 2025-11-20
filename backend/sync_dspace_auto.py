#!/usr/bin/env python3
"""
Automated script to sync DSpace items to DOCiD publications database
Non-interactive version for testing
"""

import requests
import json
import time
from app.service_dspace import DSpaceClient

# Configuration
DOCID_API_URL = "http://localhost:5001"
DSPACE_BASE_URL = "https://demo.dspace.org/server"

# DSpace credentials
DSPACE_USERNAME = "dspacedemo+admin@gmail.com"
DSPACE_PASSWORD = "dspace"

# DOCiD credentials - UPDATE THESE WITH YOUR CREDENTIALS
DOCID_EMAIL = "ekariz@africapid.org"  # UPDATE THIS
DOCID_PASSWORD = "Amina@1991"  # UPDATE THIS

# Number of items to sync
NUM_ITEMS = 5


def authenticate_docid(email, password):
    """Authenticate with DOCiD API and get JWT token"""
    print("\n🔐 Authenticating with DOCiD API...")

    url = f"{DOCID_API_URL}/api/v1/auth/login"

    try:
        response = requests.post(url, json={
            "email": email,
            "password": password
        })

        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            print("✓ Authentication successful")
            return access_token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("\n⚠️ Make sure the Flask server is running on http://localhost:5001")
        return None


def get_dspace_items(page=0, size=10):
    """Fetch items from DSpace"""
    print(f"\n📥 Fetching {size} items from DSpace...")

    client = DSpaceClient(DSPACE_BASE_URL, DSPACE_USERNAME, DSPACE_PASSWORD)

    # Authenticate
    auth_success = client.authenticate()
    if auth_success:
        print("✓ DSpace authentication successful")
    else:
        print("⚠️ DSpace authentication failed, proceeding without auth...")

    # Get items
    items_data = client.get_items(page=page, size=size)

    if not items_data:
        print("❌ Failed to fetch items from DSpace")
        return []

    items = items_data.get('_embedded', {}).get('items', [])
    print(f"✓ Fetched {len(items)} items from DSpace")

    return items


def sync_item_to_docid(uuid, handle, jwt_token):
    """Sync a single DSpace item to DOCiD publications table"""
    url = f"{DOCID_API_URL}/api/v1/dspace/sync/item/{uuid}"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, timeout=30)

        if response.status_code in [200, 201]:
            data = response.json()
            return {
                'success': True,
                'status_code': response.status_code,
                'data': data
            }
        else:
            return {
                'success': False,
                'status_code': response.status_code,
                'error': response.text
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def main():
    print("="*80)
    print("DSPACE TO DOCID AUTOMATED SYNC")
    print("="*80)
    print(f"DOCiD API: {DOCID_API_URL}")
    print(f"DSpace URL: {DSPACE_BASE_URL}")
    print(f"Items to sync: {NUM_ITEMS}")
    print("="*80)

    # Check credentials
    if DOCID_EMAIL == "your-email@example.com":
        print("\n⚠️ WARNING: Please update DOCID_EMAIL and DOCID_PASSWORD in the script")
        print("   Edit sync_dspace_auto.py and set your credentials")
        print("\n   Alternatively, use the interactive version:")
        print("   python sync_dspace_to_docid.py")
        return

    # Authenticate with DOCiD
    jwt_token = authenticate_docid(DOCID_EMAIL, DOCID_PASSWORD)

    if not jwt_token:
        print("\n❌ Failed to authenticate with DOCiD. Exiting.")
        return

    # Fetch DSpace items
    items = get_dspace_items(page=0, size=NUM_ITEMS)

    if not items:
        print("\n❌ No items to sync. Exiting.")
        return

    # Sync each item
    print(f"\n{'='*80}")
    print(f"SYNCING {len(items)} ITEMS TO DOCID PUBLICATIONS TABLE")
    print(f"{'='*80}")

    results = {
        'total': len(items),
        'synced': 0,
        'already_exists': 0,
        'errors': 0,
        'items': []
    }

    for idx, item in enumerate(items, 1):
        uuid = item.get('uuid')
        handle = item.get('handle')
        name = item.get('name', 'Untitled')

        print(f"\n[{idx}/{len(items)}] Processing item...")
        print(f"   UUID: {uuid}")
        print(f"   Handle: {handle}")
        print(f"   Title: {name[:60]}{'...' if len(name) > 60 else ''}")

        # Sync item
        result = sync_item_to_docid(uuid, handle, jwt_token)

        if result['success']:
            data = result.get('data', {})

            if result['status_code'] == 200 and 'already synced' in data.get('message', '').lower():
                print("   ⚠️ Already synced to database")
                results['already_exists'] += 1
                results['items'].append({
                    'uuid': uuid,
                    'handle': handle,
                    'name': name,
                    'status': 'already_exists',
                    'publication_id': data.get('publication_id'),
                    'docid': data.get('docid')
                })
            else:
                print(f"   ✅ Successfully synced to publications table!")
                print(f"      Publication ID: {data.get('publication_id')}")
                print(f"      DOCiD: {data.get('docid')}")
                results['synced'] += 1
                results['items'].append({
                    'uuid': uuid,
                    'handle': handle,
                    'name': name,
                    'status': 'synced',
                    'publication_id': data.get('publication_id'),
                    'docid': data.get('docid'),
                    'dspace_handle': data.get('dspace_handle')
                })
        else:
            print(f"   ❌ Failed to sync")
            error_msg = result.get('error', 'Unknown error')
            print(f"      Error: {error_msg[:100]}")
            results['errors'] += 1
            results['items'].append({
                'uuid': uuid,
                'handle': handle,
                'name': name,
                'status': 'error',
                'error': error_msg
            })

        # Small delay between requests
        time.sleep(0.5)

    # Summary
    print(f"\n{'='*80}")
    print("SYNC SUMMARY")
    print(f"{'='*80}")
    print(f"📊 Total items: {results['total']}")
    print(f"✅ Synced successfully: {results['synced']}")
    print(f"⚠️ Already existed: {results['already_exists']}")
    print(f"❌ Failed: {results['errors']}")

    # Show synced items
    if results['synced'] > 0:
        print(f"\n📄 NEWLY SYNCED TO PUBLICATIONS TABLE:")
        for item in results['items']:
            if item['status'] == 'synced':
                print(f"\n   • {item['name'][:70]}")
                print(f"     DOCiD: {item['docid']}")
                print(f"     Publication ID: {item['publication_id']}")
                print(f"     DSpace Handle: {item['dspace_handle']}")

    # Show already existing
    if results['already_exists'] > 0:
        print(f"\n⚠️ ALREADY IN DATABASE:")
        for item in results['items']:
            if item['status'] == 'already_exists':
                print(f"   • {item['name'][:70]}")
                print(f"     DOCiD: {item['docid']}")

    # Show errors
    if results['errors'] > 0:
        print(f"\n❌ FAILED ITEMS:")
        for item in results['items']:
            if item['status'] == 'error':
                print(f"   • {item['name'][:70]}")
                print(f"     Error: {item['error'][:100]}")

    # Save results
    output_file = "dspace_sync_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Full results saved to: {output_file}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Sync interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
