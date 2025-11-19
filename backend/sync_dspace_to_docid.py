#!/usr/bin/env python3
"""
Script to sync DSpace items to DOCiD publications database
Uses the /api/v1/dspace/sync/item/<uuid> endpoint
"""

import requests
import json
import time
from getpass import getpass

# Configuration
DOCID_API_URL = "http://localhost:5001"
DSPACE_BASE_URL = "https://demo.dspace.org/server"

# DSpace demo credentials (for fetching items)
DSPACE_USERNAME = "dspacedemo+admin@gmail.com"
DSPACE_PASSWORD = "dspace"


def authenticate_docid(email, password):
    """Authenticate with DOCiD API and get JWT token"""
    print("\n🔐 Authenticating with DOCiD API...")

    url = f"{DOCID_API_URL}/api/v1/auth/login"
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


def get_dspace_items(page=0, size=10):
    """Fetch items from DSpace (using local DSpace client)"""
    from app.service_dspace import DSpaceClient

    print(f"\n📥 Fetching {size} items from DSpace...")
    client = DSpaceClient(DSPACE_BASE_URL, DSPACE_USERNAME, DSPACE_PASSWORD)

    # Authenticate
    auth_success = client.authenticate()
    if not auth_success:
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
        response = requests.post(url, headers=headers)

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
    print("DSPACE TO DOCID SYNC SCRIPT")
    print("="*80)
    print(f"DOCiD API: {DOCID_API_URL}")
    print(f"DSpace URL: {DSPACE_BASE_URL}")
    print("="*80)

    # Get DOCiD credentials
    print("\n📝 DOCiD Login Credentials:")
    docid_email = input("Email: ").strip()
    docid_password = getpass("Password: ")

    # Authenticate with DOCiD
    jwt_token = authenticate_docid(docid_email, docid_password)

    if not jwt_token:
        print("\n❌ Failed to authenticate with DOCiD. Exiting.")
        return

    # Get number of items to sync
    print("\n📋 How many items do you want to sync?")
    num_items = int(input("Number of items (default 10): ").strip() or "10")

    # Fetch DSpace items
    items = get_dspace_items(page=0, size=num_items)

    if not items:
        print("\n❌ No items to sync. Exiting.")
        return

    # Sync each item
    print(f"\n{'='*80}")
    print(f"SYNCING {len(items)} ITEMS TO DOCID")
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

        print(f"\n[{idx}/{len(items)}] Syncing item...")
        print(f"   UUID: {uuid}")
        print(f"   Handle: {handle}")
        print(f"   Name: {name[:60]}{'...' if len(name) > 60 else ''}")

        # Sync item
        result = sync_item_to_docid(uuid, handle, jwt_token)

        if result['success']:
            data = result.get('data', {})

            if result['status_code'] == 200 and 'already synced' in data.get('message', '').lower():
                print("   ⚠️ Already synced")
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
                print(f"   ✓ Synced successfully")
                print(f"   Publication ID: {data.get('publication_id')}")
                print(f"   DOCiD: {data.get('docid')}")
                results['synced'] += 1
                results['items'].append({
                    'uuid': uuid,
                    'handle': handle,
                    'name': name,
                    'status': 'synced',
                    'publication_id': data.get('publication_id'),
                    'docid': data.get('docid')
                })
        else:
            print(f"   ❌ Failed to sync")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            results['errors'] += 1
            results['items'].append({
                'uuid': uuid,
                'handle': handle,
                'name': name,
                'status': 'error',
                'error': result.get('error')
            })

        # Small delay between requests
        time.sleep(0.5)

    # Summary
    print(f"\n{'='*80}")
    print("SYNC SUMMARY")
    print(f"{'='*80}")
    print(f"Total items: {results['total']}")
    print(f"✓ Synced successfully: {results['synced']}")
    print(f"⚠️ Already existed: {results['already_exists']}")
    print(f"❌ Failed: {results['errors']}")

    # Show synced items
    if results['synced'] > 0:
        print(f"\n📄 NEWLY SYNCED ITEMS:")
        for item in results['items']:
            if item['status'] == 'synced':
                print(f"   • {item['name'][:50]}...")
                print(f"     DOCiD: {item['docid']}")
                print(f"     Publication ID: {item['publication_id']}")

    # Show errors
    if results['errors'] > 0:
        print(f"\n❌ FAILED ITEMS:")
        for item in results['items']:
            if item['status'] == 'error':
                print(f"   • {item['name'][:50]}...")
                print(f"     Error: {item['error']}")

    # Save results
    output_file = "dspace_sync_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Full results saved to: {output_file}")
    print(f"\n{'='*80}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Sync interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
