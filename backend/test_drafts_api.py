#!/usr/bin/env python3
"""
Test script for Draft API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:5001"


def test_save_draft():
    """Test saving a draft"""
    print("\n=== Testing Save Draft ===")
    url = f"{BASE_URL}/api/v1/publications/draft"

    draft_data = {
        "email": "test@example.com",
        "formData": {
            "title": "Test Publication",
            "description": "Test description",
            "authors": ["Author 1", "Author 2"]
        }
    }

    response = requests.post(url, json=draft_data)
    print(f"POST {url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 201, "Expected 201 status code"
    print("✓ Save draft test passed")


def test_get_draft_by_email():
    """Test getting draft by email"""
    print("\n=== Testing Get Draft by Email ===")
    email = "test@example.com"
    url = f"{BASE_URL}/api/v1/publications/draft/{email}"

    response = requests.get(url)
    print(f"GET {url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, "Expected 200 status code"
    assert 'hasDraft' in response.json(), "Expected hasDraft in response"

    if response.json()['hasDraft']:
        print(f"✓ Get draft by email test passed - Draft found")
        print(f"  - Last saved: {response.json().get('lastSaved', 'N/A')}")
    else:
        print(f"✓ Get draft by email test passed - No draft found")


def test_get_draft_by_user_id():
    """Test getting draft by user_id"""
    print("\n=== Testing Get Draft by User ID (NEW) ===")
    user_id = 1  # Change this to a valid user_id in your database
    url = f"{BASE_URL}/api/v1/publications/draft/by-user/{user_id}"

    response = requests.get(url)
    print(f"GET {url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 404:
        print(f"⚠ User ID {user_id} not found - update the test with a valid user_id")
        return

    assert response.status_code == 200, "Expected 200 status code"
    assert 'hasDraft' in response.json(), "Expected hasDraft in response"

    if response.json()['hasDraft']:
        print(f"✓ Get draft by user_id test passed - Draft found")
        print(f"  - User email: {response.json().get('user_email', 'N/A')}")
        print(f"  - Last saved: {response.json().get('lastSaved', 'N/A')}")
    else:
        print(f"✓ Get draft by user_id test passed - No draft found for user")
        print(f"  - User email: {response.json().get('user_email', 'N/A')}")


def test_delete_draft():
    """Test deleting a draft"""
    print("\n=== Testing Delete Draft ===")
    email = "test@example.com"
    url = f"{BASE_URL}/api/v1/publications/draft/{email}"

    response = requests.delete(url)
    print(f"DELETE {url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, "Expected 200 status code"
    print("✓ Delete draft test passed")


def test_get_draft_stats():
    """Test getting draft statistics"""
    print("\n=== Testing Get Draft Statistics ===")
    url = f"{BASE_URL}/api/v1/publications/drafts/stats"

    response = requests.get(url)
    print(f"GET {url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, "Expected 200 status code"
    assert 'totalDrafts' in response.json(), "Expected totalDrafts in response"

    print(f"✓ Get draft stats test passed")
    print(f"  - Total drafts: {response.json()['totalDrafts']}")


if __name__ == "__main__":
    print("=" * 60)
    print("DOCiD Draft API Test Suite")
    print("=" * 60)

    try:
        # Test save draft
        test_save_draft()

        # Test get by email
        test_get_draft_by_email()

        # Test get by user_id (NEW)
        test_get_draft_by_user_id()

        # Test stats
        test_get_draft_stats()

        # Test delete (run last)
        test_delete_draft()

        print("\n" + "=" * 60)
        print("✅ All draft tests passed!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to Flask server.")
        print("Make sure the Flask server is running on http://localhost:5001")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
