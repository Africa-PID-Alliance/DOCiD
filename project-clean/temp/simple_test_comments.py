#!/usr/bin/env python3
"""
Simple test script for comments API without pytest dependency
"""
import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:5000"
ENDPOINTS = {
    'get_comments': '/api/publications/1/comments',
    'add_comment': '/api/publications/1/comments',
    'edit_comment': '/api/comments/1',
    'delete_comment': '/api/comments/1',
    'like_comment': '/api/comments/1/like',
    'user_comments': '/api/users/1/comments',
    'comment_stats': '/api/comments/stats/1'
}

def test_endpoint(method, endpoint, data=None, expected_status=None):
    """Test a single endpoint"""
    url = BASE_URL + endpoint
    headers = {'Content-Type': 'application/json'}
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url)
        elif method.upper() == 'POST':
            response = requests.post(url, data=json.dumps(data) if data else None, headers=headers)
        elif method.upper() == 'PUT':
            response = requests.put(url, data=json.dumps(data) if data else None, headers=headers)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, data=json.dumps(data) if data else None, headers=headers)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
            
        print(f"🔗 {method.upper()} {endpoint}")
        print(f"📊 Status: {response.status_code}")
        
        if expected_status and response.status_code != expected_status:
            print(f"❌ Expected {expected_status}, got {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
        
        try:
            response_data = response.json()
            print(f"✅ Response: {json.dumps(response_data, indent=2)[:200]}...")
        except:
            print(f"📄 Response (non-JSON): {response.text[:200]}...")
            
        print("-" * 50)
        return True
        
    except requests.ConnectionError:
        print(f"❌ Connection failed to {url}")
        print("💡 Make sure the Flask server is running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error testing {endpoint}: {str(e)}")
        return False

def main():
    """Run all API tests"""
    print("🧪 Starting Comments API Tests")
    print("=" * 50)
    
    # Test data
    sample_comment = {
        "user_id": 1,
        "comment_text": "This is a test comment",
        "comment_type": "general"
    }
    
    sample_reply = {
        "user_id": 1,
        "comment_text": "This is a test reply",
        "parent_comment_id": 1
    }
    
    sample_edit = {
        "user_id": 1,
        "comment_text": "This is an updated comment"
    }
    
    sample_delete = {
        "user_id": 1
    }
    
    # Test cases
    tests = [
        # Get publication comments
        {
            'name': 'Get Publication Comments',
            'method': 'GET',
            'endpoint': ENDPOINTS['get_comments'],
            'data': None
        },
        
        # Get publication comments without replies
        {
            'name': 'Get Publication Comments (no replies)',
            'method': 'GET', 
            'endpoint': ENDPOINTS['get_comments'] + '?include_replies=false',
            'data': None
        },
        
        # Add a new comment
        {
            'name': 'Add New Comment',
            'method': 'POST',
            'endpoint': ENDPOINTS['add_comment'],
            'data': sample_comment
        },
        
        # Add a reply
        {
            'name': 'Add Reply',
            'method': 'POST',
            'endpoint': ENDPOINTS['add_comment'],
            'data': sample_reply
        },
        
        # Edit comment
        {
            'name': 'Edit Comment',
            'method': 'PUT',
            'endpoint': ENDPOINTS['edit_comment'],
            'data': sample_edit
        },
        
        # Like comment
        {
            'name': 'Like Comment',
            'method': 'POST',
            'endpoint': ENDPOINTS['like_comment'],
            'data': None
        },
        
        # Get user comments
        {
            'name': 'Get User Comments',
            'method': 'GET',
            'endpoint': ENDPOINTS['user_comments'],
            'data': None
        },
        
        # Get comment statistics
        {
            'name': 'Get Comment Statistics',
            'method': 'GET',
            'endpoint': ENDPOINTS['comment_stats'],
            'data': None
        },
        
        # Delete comment (last to avoid affecting other tests)
        {
            'name': 'Delete Comment',
            'method': 'DELETE',
            'endpoint': ENDPOINTS['delete_comment'],
            'data': sample_delete
        }
    ]
    
    # Error test cases
    error_tests = [
        {
            'name': 'Get Comments - Invalid Publication',
            'method': 'GET',
            'endpoint': '/api/publications/999/comments',
            'data': None,
            'expected_status': 404
        },
        
        {
            'name': 'Add Comment - Missing Data',
            'method': 'POST',
            'endpoint': ENDPOINTS['add_comment'],
            'data': {},
            'expected_status': 400
        },
        
        {
            'name': 'Edit Comment - Invalid ID',
            'method': 'PUT',
            'endpoint': '/api/comments/999',
            'data': sample_edit,
            'expected_status': 404
        },
        
        {
            'name': 'Delete Comment - Invalid ID',
            'method': 'DELETE',
            'endpoint': '/api/comments/999',
            'data': sample_delete,
            'expected_status': 404
        }
    ]
    
    # Run successful test cases
    print("🟢 Running Success Test Cases")
    print("=" * 50)
    success_count = 0
    for test in tests:
        print(f"🧪 Test: {test['name']}")
        if test_endpoint(test['method'], test['endpoint'], test['data']):
            success_count += 1
        print()
    
    # Run error test cases
    print("🔴 Running Error Test Cases")
    print("=" * 50)
    error_success_count = 0
    for test in error_tests:
        print(f"🧪 Test: {test['name']}")
        if test_endpoint(test['method'], test['endpoint'], test['data'], test.get('expected_status')):
            error_success_count += 1
        print()
    
    # Summary
    total_tests = len(tests) + len(error_tests)
    total_success = success_count + error_success_count
    
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {total_success}")
    print(f"Failed: {total_tests - total_success}")
    print(f"Success Rate: {(total_success/total_tests)*100:.1f}%")
    
    if total_success == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())