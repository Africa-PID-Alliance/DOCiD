#!/usr/bin/env python3
"""
Test script for Analytics API endpoints (view and download counters)
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_track_view():
    """Test tracking a publication view"""
    print("\n=== Testing View Tracking ===")
    url = f"{BASE_URL}/api/publications/1/views"
    payload = {"user_id": 1}

    response = requests.post(url, json=payload)
    print(f"POST {url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 201, "Expected 201 status code"
    assert response.json()['status'] == 'success', "Expected success status"
    print("✓ View tracking test passed")


def test_get_view_count():
    """Test getting view count for a publication"""
    print("\n=== Testing View Count Retrieval ===")
    url = f"{BASE_URL}/api/publications/1/views/count"

    response = requests.get(url)
    print(f"GET {url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, "Expected 200 status code"
    assert 'view_count' in response.json(), "Expected view_count in response"
    print(f"✓ View count test passed - Total views: {response.json()['view_count']}")


def test_track_file_download():
    """Test tracking a file download"""
    print("\n=== Testing File Download Tracking ===")
    url = f"{BASE_URL}/api/publications/files/1/downloads"
    payload = {"user_id": 1}

    response = requests.post(url, json=payload)
    print(f"POST {url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 404:
        print("⚠ File ID 1 not found - this is expected if no files exist yet")
        return

    assert response.status_code == 201, "Expected 201 status code"
    assert response.json()['status'] == 'success', "Expected success status"
    print("✓ File download tracking test passed")


def test_get_download_count():
    """Test getting download count for a publication"""
    print("\n=== Testing Download Count Retrieval ===")
    url = f"{BASE_URL}/api/publications/1/downloads/count"

    response = requests.get(url)
    print(f"GET {url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, "Expected 200 status code"
    assert 'download_count' in response.json(), "Expected download_count in response"
    print(f"✓ Download count test passed - Total downloads: {response.json()['download_count']}")


def test_get_publication_stats():
    """Test getting comprehensive publication statistics"""
    print("\n=== Testing Publication Stats (Combined) ===")
    url = f"{BASE_URL}/api/publications/1/stats"

    response = requests.get(url)
    print(f"GET {url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, "Expected 200 status code"
    assert 'stats' in response.json(), "Expected stats in response"

    stats = response.json()['stats']
    assert 'views' in stats, "Expected views in stats"
    assert 'downloads' in stats, "Expected downloads in stats"
    assert 'comments' in stats, "Expected comments in stats"

    print(f"✓ Publication stats test passed")
    print(f"  - Views: {stats['views']}")
    print(f"  - Downloads: {stats['downloads']}")
    print(f"  - Comments: {stats['comments']}")


def test_get_all_files_stats():
    """Test getting individual file/document statistics"""
    print("\n=== Testing Individual Files/Documents Stats ===")
    url = f"{BASE_URL}/api/publications/1/files-stats"

    response = requests.get(url)
    print(f"GET {url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, "Expected 200 status code"
    assert 'files' in response.json(), "Expected files in response"
    assert 'documents' in response.json(), "Expected documents in response"

    files = response.json()['files']
    documents = response.json()['documents']

    print(f"✓ Individual files stats test passed")
    print(f"  - Number of files: {len(files)}")
    print(f"  - Number of documents: {len(documents)}")

    if files:
        print(f"  - File download counts:")
        for file in files:
            print(f"    • {file['title']}: {file['downloads']} downloads")

    if documents:
        print(f"  - Document download counts:")
        for doc in documents:
            print(f"    • {doc['title']}: {doc['downloads']} downloads")


if __name__ == "__main__":
    print("=" * 60)
    print("DOCiD Analytics API Test Suite")
    print("=" * 60)

    try:
        # Test view endpoints
        test_track_view()
        test_get_view_count()

        # Test download endpoints
        test_track_file_download()
        test_get_download_count()

        # Test combined stats
        test_get_publication_stats()

        # Test individual file/document stats
        test_get_all_files_stats()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to Flask server.")
        print("Make sure the Flask server is running on http://localhost:5001")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
