#!/usr/bin/env python3
"""
Test to examine the actual structure of ISNI API responses
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_raw_search_response():
    """Test to see the raw structure of ISNI search results"""
    print("\n=== Testing Raw ISNI Search Response Structure ===")

    # Test with one of the organization names
    test_names = [
        "Narmer Language School",
        "Book Hut Limited",
        "Fezzan Library"
    ]

    for org_name in test_names:
        print(f"\n--- Searching for: {org_name} ---")
        url = f"{BASE_URL}/api/v1/isni/search"
        params = {"q": org_name, "limit": 3}

        response = requests.get(url, params=params, timeout=10)

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Full Response:")
            print(json.dumps(data, indent=2))

            # Check what fields are available
            if 'institutions' in data and len(data['institutions']) > 0:
                first_org = data['institutions'][0]
                print(f"\nFirst organization keys: {list(first_org.keys())}")
                print(f"First organization data:")
                print(json.dumps(first_org, indent=2))
        else:
            print(f"Error: {response.json()}")

        print("-" * 80)


def test_direct_api_call():
    """Test calling the ISNI API directly to see raw response"""
    print("\n=== Testing Direct ISNI API Call (bypassing our backend) ===")

    # Call the Ringgold ISNI API directly
    isni_api_url = "https://isni.ringgold.com/api/stable/search"

    test_queries = [
        "Book Hut Limited",
        "Narmer Language School"
    ]

    for query in test_queries:
        print(f"\n--- Direct API call for: {query} ---")
        params = {
            "q": query,
            "limit": 2
        }

        try:
            response = requests.get(isni_api_url, params=params, timeout=10)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("Direct API Response:")
                print(json.dumps(data, indent=2))
            else:
                print(f"Error response: {response.text}")

        except Exception as e:
            print(f"Exception: {e}")

        print("-" * 80)


def test_with_known_isni():
    """Test with a known valid ISNI ID format"""
    print("\n=== Testing with Standard ISNI Format (16 digits) ===")

    # ISNI IDs are typically 16 digits, formatted like: 0000 0001 2345 6789
    # Let's try to pad the provided 6-digit IDs
    test_ids = [
        "0000000000558087",  # Padded to 16 digits
        "0000000000714314",
        "0000000000682335"
    ]

    for isni_id in test_ids:
        print(f"\nTesting ISNI ID: {isni_id}")
        url = f"{BASE_URL}/api/v1/isni/get-isni-by-id/{isni_id}"

        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print(f"✓ SUCCESS!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"✗ Failed: {response.json()}")


if __name__ == "__main__":
    print("=" * 80)
    print("ISNI API Response Structure Investigation")
    print("=" * 80)

    # Test our backend proxy
    test_raw_search_response()

    # Test with padded ISNI format
    test_with_known_isni()

    # Test direct API call
    test_direct_api_call()

    print("\n" + "=" * 80)
    print("Investigation Complete")
    print("=" * 80)
