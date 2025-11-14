#!/usr/bin/env python3
"""
Test script for specific ISNI IDs provided by user
"""

import requests
import json

BASE_URL = "http://localhost:5001"

# List of ISNI IDs to test (from user)
test_organizations = [
    {"id": "558087", "name": "Narmer Language School"},
    {"id": "682335", "name": "Tetuan Eye Centre"},
    {"id": "705882", "name": "Global Business Development Solutions (Pty) Ltd"},
    {"id": "706638", "name": "Leratong Hospital"},
    {"id": "518584", "name": "Fezzan Library"},
    {"id": "714314", "name": "Book Hut Limited"},
    {"id": "573957", "name": "The Egyptian Society for the Development of Fisheries and Human Health"},
    {"id": "717611", "name": "Allweiler-Farid Pumps Co SAE"},
    {"id": "719816", "name": "Abaphathibemali Trading Pty Ltd"},
    {"id": "579209", "name": "National Medicine and Food Administration"},
    {"id": "581601", "name": "Saint Dominique"}
]


def test_isni_by_id(isni_id, expected_name):
    """Test fetching organization by ISNI ID"""
    url = f"{BASE_URL}/api/v1/isni/get-isni-by-id/{isni_id}"

    try:
        response = requests.get(url, timeout=10)

        print(f"\nTesting ISNI ID: {isni_id} - {expected_name}")
        print(f"URL: {url}")
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ SUCCESS")
            print(f"  Response: {json.dumps(data, indent=2)}")
            return True
        elif response.status_code == 404:
            print(f"✗ NOT FOUND - {response.json().get('error', 'Unknown error')}")
            return False
        else:
            print(f"✗ ERROR - Status {response.status_code}: {response.json()}")
            return False

    except requests.exceptions.Timeout:
        print(f"✗ TIMEOUT - Request took too long")
        return False
    except requests.exceptions.ConnectionError:
        print(f"✗ CONNECTION ERROR - Cannot connect to server")
        return False
    except Exception as e:
        print(f"✗ EXCEPTION - {str(e)}")
        return False


def test_search_by_name(organization_name):
    """Test searching for organization by name"""
    url = f"{BASE_URL}/api/v1/isni/search-organization"
    params = {"name": organization_name}

    try:
        response = requests.get(url, params=params, timeout=10)

        print(f"\nSearching for: {organization_name}")
        print(f"URL: {url}")
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ FOUND")
            print(f"  ISNI: {data.get('ISNI', 'N/A')}")
            print(f"  Name: {data.get('name', 'N/A')}")
            print(f"  Location: {data.get('locality', 'N/A')}, {data.get('country_code', 'N/A')}")
            return data.get('ISNI')
        elif response.status_code == 404:
            print(f"✗ NOT FOUND - {response.json().get('error', 'Unknown error')}")
            return None
        else:
            print(f"✗ ERROR - Status {response.status_code}")
            return None

    except Exception as e:
        print(f"✗ EXCEPTION - {str(e)}")
        return None


if __name__ == "__main__":
    print("=" * 80)
    print("Testing Specific ISNI IDs")
    print("=" * 80)

    print("\n" + "=" * 80)
    print("PART 1: Testing by Direct ISNI ID Lookup")
    print("=" * 80)

    success_count = 0
    failure_count = 0

    for org in test_organizations:
        result = test_isni_by_id(org["id"], org["name"])
        if result:
            success_count += 1
        else:
            failure_count += 1

    print("\n" + "=" * 80)
    print("PART 2: Testing by Organization Name Search")
    print("=" * 80)

    found_isni_ids = []

    for org in test_organizations:
        found_isni = test_search_by_name(org["name"])
        if found_isni:
            found_isni_ids.append({
                "expected_id": org["id"],
                "found_isni": found_isni,
                "name": org["name"]
            })

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nDirect ID Lookup Results:")
    print(f"  ✓ Success: {success_count}")
    print(f"  ✗ Failures: {failure_count}")
    print(f"  Total: {len(test_organizations)}")

    if found_isni_ids:
        print(f"\nOrganizations Found by Name Search:")
        for item in found_isni_ids:
            print(f"  - {item['name']}")
            print(f"    Expected ID: {item['expected_id']}")
            print(f"    Found ISNI: {item['found_isni']}")

    print("\n" + "=" * 80)
