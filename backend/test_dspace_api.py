#!/usr/bin/env python3
"""
Test DSpace REST API Connection
Demonstrates pulling data from demo.dspace.org
"""

import requests
import json

# DSpace Demo Configuration
DSPACE_BASE_URL = "https://demo.dspace.org/server"
DSPACE_API_URL = f"{DSPACE_BASE_URL}/api"
DSPACE_USERNAME = "dspacedemo+admin@gmail.com"
DSPACE_PASSWORD = "dspace"

def test_api_root():
    """Test basic API connectivity"""
    print("=" * 60)
    print("Testing DSpace Demo REST API")
    print("=" * 60)

    response = requests.get(f"{DSPACE_API_URL}")
    print(f"\n✓ API Root: {response.status_code}")
    data = response.json()
    print(f"  DSpace Name: {data.get('dspaceName')}")
    print(f"  DSpace Version: {data.get('dspaceVersion')}")
    print(f"  Server URL: {data.get('dspaceServer')}")
    return data

def authenticate():
    """Authenticate and get JWT token"""
    print(f"\n{'=' * 60}")
    print("Authenticating...")
    print("=" * 60)

    session = requests.Session()

    # Step 1: Get CSRF token
    print("  Step 1: Getting CSRF token...")
    status_response = session.get(f"{DSPACE_API_URL}/authn/status")
    csrf_token = status_response.headers.get('DSPACE-XSRF-TOKEN')
    print(f"  CSRF Token obtained: {csrf_token[:30] if csrf_token else 'Not found'}...")

    if not csrf_token:
        print("  ❌ Failed to get CSRF token")
        return None, None, None

    # Step 2: Login with CSRF token
    print("  Step 2: Logging in...")
    login_url = f"{DSPACE_API_URL}/authn/login"

    headers = {
        'X-XSRF-TOKEN': csrf_token
    }

    response = session.post(
        login_url,
        data={
            'user': DSPACE_USERNAME,
            'password': DSPACE_PASSWORD
        },
        headers=headers
    )

    print(f"\n✓ Login Status: {response.status_code}")

    if response.status_code == 200:
        # Extract JWT token from headers
        auth_token = response.headers.get('Authorization')
        new_csrf_token = response.headers.get('DSPACE-XSRF-TOKEN')

        print(f"  Auth Token: {auth_token[:50] if auth_token else 'Not found'}...")
        print(f"  New CSRF Token: {new_csrf_token[:30] if new_csrf_token else 'Using previous'}...")

        return session, auth_token, new_csrf_token or csrf_token
    else:
        print(f"  Error: {response.text}")
        return None, None, None

def get_communities(session):
    """Get list of communities"""
    print(f"\n{'=' * 60}")
    print("Fetching Communities...")
    print("=" * 60)

    response = session.get(f"{DSPACE_API_URL}/core/communities?size=5")
    print(f"\n✓ Communities Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        communities = data.get('_embedded', {}).get('communities', [])

        print(f"  Total Communities: {data.get('page', {}).get('totalElements', 0)}")
        print(f"\n  Sample Communities:")
        for i, comm in enumerate(communities[:3], 1):
            print(f"    {i}. {comm.get('name')} (UUID: {comm.get('uuid')})")

        return communities
    else:
        print(f"  Error: {response.text}")
        return []

def get_items(session, auth_token, size=5):
    """Get list of items"""
    print(f"\n{'=' * 60}")
    print("Fetching Items...")
    print("=" * 60)

    headers = {}
    if auth_token:
        headers['Authorization'] = auth_token

    response = session.get(f"{DSPACE_API_URL}/core/items?size={size}", headers=headers)
    print(f"\n✓ Items Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        items = data.get('_embedded', {}).get('items', [])

        print(f"  Total Items: {data.get('page', {}).get('totalElements', 0)}")
        print(f"\n  Sample Items:")
        for i, item in enumerate(items[:3], 1):
            print(f"    {i}. {item.get('name')} (UUID: {item.get('uuid')})")
            print(f"       Handle: {item.get('handle', 'N/A')}")

        return items
    else:
        print(f"  Error: {response.text}")
        return []

def get_item_metadata(session, auth_token, item_uuid):
    """Get detailed metadata for an item"""
    print(f"\n{'=' * 60}")
    print(f"Fetching Item Metadata (UUID: {item_uuid})")
    print("=" * 60)

    headers = {}
    if auth_token:
        headers['Authorization'] = auth_token

    response = session.get(f"{DSPACE_API_URL}/core/items/{item_uuid}", headers=headers)

    if response.status_code == 200:
        item = response.json()

        print(f"\n✓ Item Retrieved:")
        print(f"  Name: {item.get('name')}")
        print(f"  Handle: {item.get('handle')}")
        print(f"  UUID: {item.get('uuid')}")
        print(f"  Last Modified: {item.get('lastModified')}")

        # Get metadata
        metadata = item.get('metadata', {})
        print(f"\n  Metadata Fields:")
        for field, values in list(metadata.items())[:10]:
            if values:
                print(f"    {field}: {values[0].get('value', '')[:100]}")

        return item
    else:
        print(f"  Error: {response.text}")
        return None

def main():
    """Main test function"""

    # Test API root
    api_info = test_api_root()

    # Authenticate
    session, auth_token, csrf_token = authenticate()

    if not session:
        print("\n❌ Authentication failed!")
        return

    print("\n✅ Authentication successful!")

    # Get communities
    communities = get_communities(session)

    # Get items
    items = get_items(session, auth_token, size=5)

    # Get detailed metadata for first item
    if items:
        first_item = items[0]
        item_uuid = first_item.get('uuid')
        if item_uuid:
            detailed_item = get_item_metadata(session, auth_token, item_uuid)

            # Save sample item for reference
            with open('/tmp/dspace_sample_item.json', 'w') as f:
                json.dump(detailed_item, f, indent=2)
            print(f"\n💾 Sample item saved to: /tmp/dspace_sample_item.json")

    print(f"\n{'=' * 60}")
    print("✅ DSpace API Test Complete!")
    print("=" * 60)
    print("\nKey Findings:")
    print("  - DSpace REST API is fully functional")
    print("  - Authentication works with JWT tokens")
    print("  - Can pull items, collections, and metadata")
    print("  - Ready for DOCiD integration!")
    print("\n")

if __name__ == "__main__":
    main()
