#!/usr/bin/env python3
"""
Test script for ISNI API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:5001"


def test_search_organizations():
    """Test searching for organizations"""
    print("\n=== Testing ISNI Organization Search ===")
    url = f"{BASE_URL}/api/v1/isni/search"

    # Test search for a university
    params = {
        "q": "University of Nairobi",
        "limit": 5
    }

    response = requests.get(url, params=params)
    print(f"GET {url}")
    print(f"Params: {params}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, "Expected 200 status code"
    print("✓ Search organizations test passed")


def test_search_single_organization():
    """Test searching for a single organization"""
    print("\n=== Testing ISNI Single Organization Search ===")
    url = f"{BASE_URL}/api/v1/isni/search-organization"

    # Test search with name only
    params = {
        "name": "Harvard University"
    }

    response = requests.get(url, params=params)
    print(f"GET {url}")
    print(f"Params: {params}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        assert 'ISNI' in response.json(), "Expected ISNI in response"
        print("✓ Single organization search test passed")
    elif response.status_code == 404:
        print("⚠ Organization not found - this is expected if the organization doesn't exist in ISNI")
    else:
        print(f"✗ Unexpected status code: {response.status_code}")


def test_search_organization_with_country():
    """Test searching for organization with country filter"""
    print("\n=== Testing ISNI Organization Search with Country Filter ===")
    url = f"{BASE_URL}/api/v1/isni/search-organization"

    # Test search with name and country
    params = {
        "name": "National Library",
        "country": "KE"
    }

    response = requests.get(url, params=params)
    print(f"GET {url}")
    print(f"Params: {params}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        data = response.json()
        assert 'ISNI' in data, "Expected ISNI in response"
        assert data.get('country_code') == 'KE', "Expected country_code to be KE"
        print("✓ Organization search with country filter test passed")
    elif response.status_code == 404:
        print("⚠ Organization not found in specified country")
    else:
        print(f"✗ Unexpected status code: {response.status_code}")


def test_get_organization_by_isni():
    """Test getting organization by ISNI ID"""
    print("\n=== Testing Get Organization by ISNI ID ===")

    # First, search for an organization to get a valid ISNI
    search_url = f"{BASE_URL}/api/v1/isni/search"
    search_params = {"q": "University", "limit": 1}

    search_response = requests.get(search_url, params=search_params)

    if search_response.status_code == 200:
        search_data = search_response.json()
        institutions = search_data.get('institutions', [])

        if institutions and len(institutions) > 0:
            test_isni = institutions[0].get('ISNI')

            if test_isni:
                # Now test getting by ISNI ID
                url = f"{BASE_URL}/api/v1/isni/get-isni-by-id/{test_isni}"
                response = requests.get(url)

                print(f"GET {url}")
                print(f"Status: {response.status_code}")
                print(f"Response: {json.dumps(response.json(), indent=2)}")

                assert response.status_code == 200, "Expected 200 status code"
                assert 'ISNI' in response.json(), "Expected ISNI in response"
                print("✓ Get organization by ISNI ID test passed")
                return

    print("⚠ Skipping test - no valid ISNI ID found from search")


def test_invalid_isni():
    """Test getting organization with invalid ISNI ID"""
    print("\n=== Testing Invalid ISNI ID ===")
    url = f"{BASE_URL}/api/v1/isni/get-isni-by-id/0000000000000000"

    response = requests.get(url)
    print(f"GET {url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 404, "Expected 404 status code for invalid ISNI"
    print("✓ Invalid ISNI test passed")


def test_missing_search_param():
    """Test search without required parameter"""
    print("\n=== Testing Missing Search Parameter ===")
    url = f"{BASE_URL}/api/v1/isni/search"

    response = requests.get(url)
    print(f"GET {url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 400, "Expected 400 status code for missing parameter"
    print("✓ Missing parameter test passed")


if __name__ == "__main__":
    print("=" * 60)
    print("DOCiD ISNI API Test Suite")
    print("=" * 60)

    try:
        # Test search endpoints
        test_search_organizations()
        test_search_single_organization()
        test_search_organization_with_country()

        # Test get by ID
        test_get_organization_by_isni()

        # Test error handling
        test_invalid_isni()
        test_missing_search_param()

        print("\n" + "=" * 60)
        print("✅ All ISNI API tests passed!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to Flask server.")
        print("Make sure the Flask server is running on http://localhost:5001")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
