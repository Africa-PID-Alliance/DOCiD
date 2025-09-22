#!/usr/bin/env python3
"""
Test comments API on the correct port (5001)
"""
import requests
import json
import sys

def test_comments_api_correct_port():
    """Test the comments API on port 5001"""
    
    BASE_URL = "http://localhost:5001"
    
    print("🔍 Testing Comments API on Port 5001")
    print("=" * 50)
    
    # Test scenarios
    tests = [
        {
            'name': 'Basic GET - Publication 1',
            'method': 'GET',
            'url': f'{BASE_URL}/api/publications/1/comments'
        },
        {
            'name': 'GET with include_replies=false',
            'method': 'GET',
            'url': f'{BASE_URL}/api/publications/1/comments?include_replies=false'
        },
        {
            'name': 'GET non-existent publication',
            'method': 'GET',
            'url': f'{BASE_URL}/api/publications/999/comments'
        },
        {
            'name': 'POST new comment',
            'method': 'POST',
            'url': f'{BASE_URL}/api/publications/1/comments',
            'data': {
                'user_id': 1,
                'comment_text': 'Test comment for debugging',
                'comment_type': 'general'
            }
        },
        {
            'name': 'GET comment stats',
            'method': 'GET',
            'url': f'{BASE_URL}/api/comments/stats/1'
        }
    ]
    
    for i, test in enumerate(tests, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 30)
        
        try:
            headers = {'Content-Type': 'application/json'}
            
            if test['method'] == 'GET':
                response = requests.get(test['url'], headers=headers, timeout=10)
            elif test['method'] == 'POST':
                response = requests.post(
                    test['url'], 
                    data=json.dumps(test['data']),
                    headers=headers, 
                    timeout=10
                )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 500:
                print("🚨 500 ERROR - Server Internal Error")
                print("Error Details:")
                print(response.text[:1000])
                
                # Look for specific error patterns
                error_text = response.text.lower()
                if 'sqlalchemy' in error_text:
                    print("🔍 SQLAlchemy database error detected")
                if 'foreign key' in error_text:
                    print("🔍 Foreign key constraint error")
                if 'no such table' in error_text:
                    print("🔍 Missing database table error")
                if 'publications' in error_text:
                    print("🔍 Publications table issue")
                if 'user_accounts' in error_text:
                    print("🔍 User accounts table issue")
                    
            elif response.status_code == 200:
                print("✅ SUCCESS")
                try:
                    data = response.json()
                    if 'total_comments' in data:
                        print(f"Total Comments: {data['total_comments']}")
                    if 'statistics' in data:
                        print(f"Statistics: {data['statistics']}")
                    if 'message' in data:
                        print(f"Message: {data['message']}")
                except:
                    print("Response is valid but not JSON")
                    
            elif response.status_code == 201:
                print("✅ CREATED")
                try:
                    data = response.json()
                    print(f"Message: {data.get('message', 'No message')}")
                    if 'comment' in data:
                        print(f"Comment ID: {data['comment'].get('id')}")
                except:
                    pass
                    
            elif response.status_code == 404:
                print("⚠️ NOT FOUND")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data.get('error', 'No error message')}")
                except:
                    print(f"Response: {response.text}")
                    
            elif response.status_code == 400:
                print("⚠️ BAD REQUEST")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data.get('error', 'No error message')}")
                except:
                    print(f"Response: {response.text}")
                    
            else:
                print(f"Unexpected Status: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except requests.ConnectionError:
            print("❌ CONNECTION ERROR")
            print("Flask server is not running on port 5001")
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")

def main():
    test_comments_api_correct_port()
    return 0

if __name__ == "__main__":
    sys.exit(main())