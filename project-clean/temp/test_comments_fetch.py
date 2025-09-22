#!/usr/bin/env python3
"""
Test script to diagnose comments fetching issues and 500 errors
"""
import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5001"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def log_message(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def test_server_connection():
    """Test if the server is running and accessible"""
    log_message("Testing server connection...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        log_message(f"✅ Server is running (Status: {response.status_code})")
        return True
    except requests.ConnectionError:
        log_message("❌ Cannot connect to server at http://localhost:5000", "ERROR")
        log_message("💡 Make sure Flask server is running: python run.py", "INFO")
        return False
    except Exception as e:
        log_message(f"❌ Connection error: {str(e)}", "ERROR")
        return False

def test_comments_endpoint():
    """Test the comments endpoint that's causing 500 error"""
    log_message("Testing comments endpoints...")
    
    # Test cases with different publication IDs
    test_cases = [
        {'pub_id': 1, 'desc': 'Publication ID 1'},
        {'pub_id': 2, 'desc': 'Publication ID 2'},  
        {'pub_id': 999, 'desc': 'Non-existent publication'},
        {'pub_id': 0, 'desc': 'Invalid publication ID (0)'},
    ]
    
    results = []
    
    for test_case in test_cases:
        pub_id = test_case['pub_id']
        desc = test_case['desc']
        
        log_message(f"🔍 Testing: {desc}")
        
        try:
            url = f"{BASE_URL}/api/publications/{pub_id}/comments"
            log_message(f"   GET {url}")
            
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            log_message(f"   Status: {response.status_code}")
            log_message(f"   Headers: {dict(response.headers)}")
            
            if response.status_code == 500:
                log_message(f"   ❌ 500 Error - Server Internal Error", "ERROR")
                log_message(f"   Response body: {response.text[:500]}", "ERROR")
                results.append(({'test': desc, 'status': 500, 'error': response.text}))
            elif response.status_code == 404:
                log_message(f"   ⚠️  404 - Resource not found (expected for invalid IDs)")
                try:
                    error_data = response.json()
                    log_message(f"   Error message: {error_data.get('error', 'No error message')}")
                    results.append({'test': desc, 'status': 404, 'data': error_data})
                except:
                    results.append({'test': desc, 'status': 404, 'raw': response.text})
            elif response.status_code == 200:
                log_message(f"   ✅ 200 - Success")
                try:
                    data = response.json()
                    log_message(f"   Comments found: {data.get('total_comments', 'unknown')}")
                    log_message(f"   Publication ID: {data.get('publication_id', 'unknown')}")
                    results.append({'test': desc, 'status': 200, 'data': data})
                except json.JSONDecodeError as e:
                    log_message(f"   ❌ Invalid JSON response: {str(e)}", "ERROR")
                    results.append({'test': desc, 'status': 200, 'error': 'Invalid JSON', 'raw': response.text})
            else:
                log_message(f"   ⚠️  Unexpected status: {response.status_code}")
                results.append({'test': desc, 'status': response.status_code, 'raw': response.text})
                
        except requests.Timeout:
            log_message(f"   ❌ Request timed out", "ERROR")
            results.append({'test': desc, 'error': 'timeout'})
        except Exception as e:
            log_message(f"   ❌ Request failed: {str(e)}", "ERROR")
            results.append({'test': desc, 'error': str(e)})
        
        log_message("")  # Empty line for readability
        time.sleep(0.5)  # Brief delay between requests
    
    return results

def test_with_query_parameters():
    """Test comments endpoint with various query parameters"""
    log_message("Testing with query parameters...")
    
    pub_id = 1  # Use a likely existing publication
    base_url = f"{BASE_URL}/api/publications/{pub_id}/comments"
    
    test_cases = [
        {'params': '?include_replies=true', 'desc': 'Include replies'},
        {'params': '?include_replies=false', 'desc': 'Exclude replies'},
        {'params': '?include_replies=invalid', 'desc': 'Invalid include_replies value'},
        {'params': '?limit=10', 'desc': 'With limit parameter'},
        {'params': '?offset=0', 'desc': 'With offset parameter'},
        {'params': '', 'desc': 'No parameters (default)'},
    ]
    
    for test_case in test_cases:
        params = test_case['params']
        desc = test_case['desc']
        url = base_url + params
        
        log_message(f"🔍 Testing: {desc}")
        log_message(f"   GET {url}")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            log_message(f"   Status: {response.status_code}")
            
            if response.status_code == 500:
                log_message(f"   ❌ 500 Error with query params", "ERROR")
                log_message(f"   Response: {response.text[:200]}...", "ERROR")
            elif response.status_code == 200:
                try:
                    data = response.json()
                    log_message(f"   ✅ Success - {data.get('total_comments', 0)} comments")
                except:
                    log_message(f"   ⚠️  Success but invalid JSON")
            else:
                log_message(f"   Status {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            log_message(f"   ❌ Request failed: {str(e)}", "ERROR")
        
        log_message("")

def test_database_dependencies():
    """Test if database-related issues might be causing 500 errors"""
    log_message("Testing potential database issues...")
    
    # Test other endpoints that might use the database
    endpoints_to_test = [
        '/api/publications',
        '/api/users/1',
        '/api/comments/stats/1',
        '/health',  # If available
        '/',        # Root endpoint
    ]
    
    for endpoint in endpoints_to_test:
        url = BASE_URL + endpoint
        log_message(f"🔍 Testing: {endpoint}")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=5)
            log_message(f"   Status: {response.status_code}")
            
            if response.status_code == 500:
                log_message(f"   ❌ 500 Error - Database issue likely", "ERROR")
            elif response.status_code == 404:
                log_message(f"   ⚠️  404 - Endpoint not found (normal)")
            elif response.status_code == 200:
                log_message(f"   ✅ Success")
            else:
                log_message(f"   Status: {response.status_code}")
                
        except Exception as e:
            log_message(f"   ❌ Error: {str(e)}", "ERROR")
        
        time.sleep(0.2)

def create_test_data():
    """Try to create test data to ensure we have something to fetch"""
    log_message("Attempting to create test data...")
    
    # Try to add a test comment
    test_comment_data = {
        "user_id": 1,
        "comment_text": "Test comment for debugging fetch issues",
        "comment_type": "general"
    }
    
    try:
        url = f"{BASE_URL}/api/publications/1/comments"
        response = requests.post(
            url,
            data=json.dumps(test_comment_data),
            headers=HEADERS,
            timeout=10
        )
        
        log_message(f"POST {url}")
        log_message(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            log_message("✅ Test comment created successfully")
            try:
                data = response.json()
                comment_id = data.get('comment', {}).get('id')
                log_message(f"Created comment ID: {comment_id}")
                return comment_id
            except:
                pass
        elif response.status_code == 500:
            log_message("❌ 500 error when creating test data", "ERROR")
            log_message(f"Response: {response.text[:200]}", "ERROR")
        else:
            log_message(f"Unexpected status: {response.status_code}")
            log_message(f"Response: {response.text[:200]}")
            
    except Exception as e:
        log_message(f"❌ Failed to create test data: {str(e)}", "ERROR")
    
    return None

def main():
    """Main test function"""
    print("🧪 Comments Fetch Testing Script")
    print("=" * 60)
    
    # Step 1: Test server connection
    if not test_server_connection():
        return 1
    
    print("\n" + "=" * 60)
    
    # Step 2: Test basic comments fetching
    results = test_comments_endpoint()
    
    print("\n" + "=" * 60)
    
    # Step 3: Test with query parameters
    test_with_query_parameters()
    
    print("\n" + "=" * 60)
    
    # Step 4: Test database dependencies
    test_database_dependencies()
    
    print("\n" + "=" * 60)
    
    # Step 5: Try to create test data
    create_test_data()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    # Analyze results
    errors_500 = [r for r in results if r.get('status') == 500]
    success_200 = [r for r in results if r.get('status') == 200]
    not_found_404 = [r for r in results if r.get('status') == 404]
    
    print(f"Total tests: {len(results)}")
    print(f"✅ Successful (200): {len(success_200)}")
    print(f"⚠️  Not Found (404): {len(not_found_404)}")
    print(f"❌ Server Errors (500): {len(errors_500)}")
    
    if errors_500:
        print(f"\n🚨 DIAGNOSIS:")
        print(f"The API is returning 500 errors, which indicates:")
        print(f"1. Database connection issues")
        print(f"2. Missing required data (publications/users)")
        print(f"3. Code errors in the comments endpoint")
        print(f"4. Missing environment variables")
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"1. Check Flask server logs for detailed error messages")
        print(f"2. Verify database is running and accessible")
        print(f"3. Ensure test data exists (publications, users)")
        print(f"4. Check environment variables are set")
    elif success_200:
        print(f"\n✅ DIAGNOSIS:")
        print(f"Comments API is working correctly!")
    else:
        print(f"\n⚠️  DIAGNOSIS:")
        print(f"No successful responses - check server setup")
    
    return 0 if not errors_500 else 1

if __name__ == "__main__":
    sys.exit(main())