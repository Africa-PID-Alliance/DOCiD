#!/usr/bin/env python3
"""
Quick diagnostic script to identify the specific cause of comments API 500 error
"""
import requests
import json
import sys
import traceback

def test_comments_api():
    """Test the comments API and capture detailed error information"""
    
    print("🔍 Diagnosing Comments API 500 Error")
    print("=" * 50)
    
    # Test different scenarios that might cause 500 errors
    test_scenarios = [
        {
            'name': 'Basic GET request',
            'method': 'GET',
            'url': 'http://localhost:5001/api/publications/1/comments',
            'data': None
        },
        {
            'name': 'GET with include_replies=false',
            'method': 'GET', 
            'url': 'http://localhost:5001/api/publications/1/comments?include_replies=false',
            'data': None
        },
        {
            'name': 'GET non-existent publication',
            'method': 'GET',
            'url': 'http://localhost:5001/api/publications/999/comments',
            'data': None
        },
        {
            'name': 'POST new comment',
            'method': 'POST',
            'url': 'http://localhost:5001/api/publications/1/comments',
            'data': {
                'user_id': 1,
                'comment_text': 'Test comment for debugging',
                'comment_type': 'general'
            }
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. Testing: {scenario['name']}")
        print("-" * 40)
        
        try:
            if scenario['method'] == 'GET':
                response = requests.get(
                    scenario['url'], 
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
            elif scenario['method'] == 'POST':
                response = requests.post(
                    scenario['url'],
                    data=json.dumps(scenario['data']),
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 500:
                print("🚨 500 ERROR DETAILS:")
                print(f"Response Body: {response.text}")
                
                # Try to extract useful information
                if 'text/html' in response.headers.get('Content-Type', ''):
                    print("📄 HTML Error Page - This indicates a Flask/server error")
                    
                    # Look for common error patterns
                    error_text = response.text
                    if 'werkzeug.exceptions' in error_text:
                        print("🔍 Werkzeug exception detected")
                    if 'sqlite3' in error_text.lower():
                        print("🔍 SQLite database error detected")
                    if 'sqlalchemy' in error_text.lower():
                        print("🔍 SQLAlchemy ORM error detected")
                    if 'publicationcomments' in error_text.lower():
                        print("🔍 PublicationComments model error detected")
                    if 'foreign key' in error_text.lower():
                        print("🔍 Foreign key constraint error detected")
                        
            elif response.status_code == 200:
                print("✅ SUCCESS")
                try:
                    data = response.json()
                    print(f"Total Comments: {data.get('total_comments', 'unknown')}")
                    print(f"Publication ID: {data.get('publication_id', 'unknown')}")
                except:
                    print("Response is not valid JSON")
                    
            elif response.status_code == 404:
                print("⚠️ NOT FOUND (expected for invalid IDs)")
                try:
                    error_data = response.json()
                    print(f"Error Message: {error_data.get('error', 'No message')}")
                except:
                    print(f"Response: {response.text}")
                    
            else:
                print(f"ℹ️ Status {response.status_code}")
                print(f"Response: {response.text[:200]}")
            
        except requests.ConnectionError:
            print("❌ CONNECTION ERROR: Cannot connect to Flask server")
            print("💡 Make sure the Flask server is running on localhost:5000")
            
        except requests.Timeout:
            print("❌ TIMEOUT: Request took too long")
            
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {str(e)}")
            traceback.print_exc()

def check_server_logs():
    """Provide instructions for checking server logs"""
    print("\n" + "=" * 50)
    print("📋 DEBUGGING STEPS")
    print("=" * 50)
    print("1. Check Flask server console/logs for detailed error messages")
    print("2. Look for these common issues:")
    print("   • Database connection errors")
    print("   • Missing tables (publications, user_accounts, publication_comments)")
    print("   • Missing required data (no users/publications in database)")
    print("   • Environment variable issues")
    print("   • Import errors in the comments route")
    print("\n3. Try these solutions:")
    print("   • Restart the Flask server")
    print("   • Check database migrations are applied")
    print("   • Verify test data exists")
    print("   • Check all required Python packages are installed")
    
def main():
    """Main diagnostic function"""
    test_comments_api()
    check_server_logs()
    return 0

if __name__ == "__main__":
    sys.exit(main())