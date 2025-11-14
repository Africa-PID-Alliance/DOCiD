#!/usr/bin/env python3
"""
Test with valid ISNI IDs discovered from direct API calls
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_search():
    """Test search endpoint"""
    print("\n=== Testing ISNI Search (after fix) ===")
    url = f"{BASE_URL}/api/v1/isni/search"

    test_queries = [
        "Book Hut Limited",
        "Narmer Language School",
        "Harvard University",
        "University of Oxford"
    ]

    for query in test_queries:
        print(f"\n--- Searching for: {query} ---")
        params = {"q": query, "limit": 3}

        response = requests.get(url, params=params, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            institutions = data.get('institutions', [])

            print(f"Total results: {total}")
            print(f"Returned: {len(institutions)} institutions")

            if institutions:
                print("\nFirst result:")
                first = institutions[0]
                print(f"  ISNI: {first.get('isni', 'N/A')}")
                print(f"  Name: {first.get('name', 'N/A')}")
                print(f"  Location: {first.get('locality', 'N/A')}, {first.get('country_code', 'N/A')}")
        else:
            print(f"Error: {response.json()}")


def test_get_by_id():
    """Test get by ID with valid ISNI numbers"""
    print("\n=== Testing Get by ISNI ID ===")

    valid_isnis = [
        {"isni": "0000000523894585", "name": "Book Hut Limited"},
        {"isni": "0000000480216003", "name": "Narmer Language School"},
    ]

    for item in valid_isnis:
        isni_id = item['isni']
        expected_name = item['name']

        print(f"\n--- Testing ISNI: {isni_id} ({expected_name}) ---")
        url = f"{BASE_URL}/api/v1/isni/get-isni-by-id/{isni_id}"

        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ SUCCESS")
            print(f"  Name: {data.get('name', 'N/A')}")
            print(f"  ISNI: {data.get('isni', 'N/A')}")
            print(f"  Location: {data.get('locality', 'N/A')}, {data.get('country_code', 'N/A')}")
        elif response.status_code == 404:
            print(f"✗ NOT FOUND: {response.json().get('error')}")
        else:
            print(f"✗ ERROR: {response.json()}")


def test_search_organization():
    """Test single organization search"""
    print("\n=== Testing Search Organization (single result) ===")

    test_queries = [
        {"name": "Book Hut Limited"},
        {"name": "Harvard University"},
    ]

    for query in test_queries:
        print(f"\n--- Searching for: {query['name']} ---")
        url = f"{BASE_URL}/api/v1/isni/search-organization"

        response = requests.get(url, params=query, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ FOUND")
            print(f"  ISNI: {data.get('isni', 'N/A')}")
            print(f"  Name: {data.get('name', 'N/A')}")
            print(f"  Location: {data.get('locality', 'N/A')}, {data.get('country_code', 'N/A')}")
        else:
            print(f"Error: {response.json()}")


if __name__ == "__main__":
    print("=" * 80)
    print("Testing ISNI API with Valid IDs")
    print("=" * 80)

    try:
        test_search()
        test_get_by_id()
        test_search_organization()

        print("\n" + "=" * 80)
        print("✅ Testing Complete")
        print("=" * 80)

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to Flask server.")
        print("Make sure the Flask server is running on http://localhost:5001")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
