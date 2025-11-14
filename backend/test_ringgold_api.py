#!/usr/bin/env python3
"""
Test script for Ringgold API endpoints
"""

import requests
import json

# Base URL - adjust if your Flask app is running on a different port
BASE_URL = "http://localhost:5001/api/v1/ringgold"

def test_get_by_isni_id():
    """Test fetching organization by ISNI ID"""
    print("\n" + "="*60)
    print("TEST: Get organization by ISNI ID")
    print("="*60)

    # Test with ISNI from Narmer Language School
    isni_id = "0000000480216003"

    url = f"{BASE_URL}/get-by-isni/{isni_id}"
    print(f"Testing URL: {url}")

    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        except json.JSONDecodeError:
            print(f"Response (text):\n{response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def test_search_organizations():
    """Test searching for organizations"""
    print("\n" + "="*60)
    print("TEST: Search organizations")
    print("="*60)

    # Search for a university
    query = "University of Nairobi"

    url = f"{BASE_URL}/search?q={query}&limit=5"
    print(f"Testing URL: {url}")

    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        except json.JSONDecodeError:
            print(f"Response (text):\n{response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def test_search_single_organization():
    """Test searching for a single organization"""
    print("\n" + "="*60)
    print("TEST: Search single organization")
    print("="*60)

    # Search for a specific organization
    org_name = "Narmer Language School"
    country = "EG"  # Egypt

    url = f"{BASE_URL}/search-organization?name={org_name}&country={country}"
    print(f"Testing URL: {url}")

    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        except json.JSONDecodeError:
            print(f"Response (text):\n{response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def main():
    print("\n" + "="*60)
    print("RINGGOLD API ENDPOINT TESTS")
    print("="*60)
    print("Make sure your Flask app is running on http://localhost:5001")
    print("="*60)

    results = []

    # Run all tests
    results.append(("Get by ISNI ID", test_get_by_isni_id()))
    results.append(("Search organizations", test_search_organizations()))
    results.append(("Search single organization", test_search_single_organization()))

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")

    # Overall result
    all_passed = all(result[1] for result in results)
    print("="*60)
    if all_passed:
        print("All tests PASSED!")
    else:
        print("Some tests FAILED!")
    print("="*60)


if __name__ == "__main__":
    main()
