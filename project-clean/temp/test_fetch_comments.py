#!/usr/bin/env python3
"""
Test script specifically for fetching comments from various endpoints
Tests multiple endpoint variations to find the correct API path
"""
import requests
import json
import sys
from datetime import datetime
from urllib.parse import urljoin

# Base URLs to test
BASE_URLS = [
    "https://docid.africapidalliance.org",
    "http://docid.africapidalliance.org",
]

# Possible API path variations
API_PATHS = [
    "/api/v1/comments/get-comments",
    "/api/v1/comments/get_comments", 
    "/api/v1/comments",
    "/api/comments/get-comments",
    "/api/comments",
    "/api/v1/publication/comments",
    "/api/v1/publications/comments",
    "/api/publication/comments",
    "/api/publications/comments",
]

# Test publication IDs
TEST_PUBLICATION_IDS = [1, 2, 3, 10, 100, "test", "sample"]

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def print_result(success, message):
    """Print a formatted result"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

def test_endpoint(url, method="GET", headers=None, params=None, timeout=5):
    """Test a single endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=params, timeout=timeout)
        else:
            response = requests.request(method, url, headers=headers, params=params, timeout=timeout)
        
        return {
            'success': True,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'body': response.text[:500] if response.text else None,
            'json': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
        }
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Timeout'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Connection Error'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': str(e)[:100]}
    except json.JSONDecodeError:
        return {'success': False, 'error': 'Invalid JSON response'}
    except Exception as e:
        return {'success': False, 'error': str(e)[:100]}

def test_fetch_comments_variations():
    """Test various endpoint variations to find working comments API"""
    print_section("TESTING COMMENTS ENDPOINT VARIATIONS")
    
    working_endpoints = []
    
    for base_url in BASE_URLS:
        for api_path in API_PATHS:
            for pub_id in TEST_PUBLICATION_IDS[:3]:  # Test first 3 IDs for each combination
                # Try different URL patterns
                url_patterns = [
                    f"{base_url}{api_path}/{pub_id}",
                    f"{base_url}{api_path}?publication_id={pub_id}",
                    f"{base_url}{api_path}?pub_id={pub_id}",
                    f"{base_url}{api_path}?id={pub_id}",
                ]
                
                for url in url_patterns:
                    print(f"\nTesting: {url}")
                    result = test_endpoint(url)
                    
                    if result['success']:
                        status = result['status_code']
                        if status == 200:
                            print_result(True, f"SUCCESS! Status: {status}")
                            
                            # Check if it's actually comments data
                            if result['json']:
                                data = result['json']
                                if 'comments' in data or 'data' in data or 'results' in data:
                                    print(f"  📊 Found comments data structure")
                                    working_endpoints.append({
                                        'url': url,
                                        'pattern': api_path,
                                        'publication_id': pub_id,
                                        'data': data
                                    })
                                print(f"  📝 Response keys: {list(data.keys())[:5]}")
                        elif status == 404:
                            print_result(False, f"Not Found (404)")
                        elif status == 500:
                            print_result(False, f"Server Error (500)")
                        elif status == 401:
                            print_result(False, f"Unauthorized (401) - May need authentication")
                        elif status == 405:
                            print_result(False, f"Method Not Allowed (405)")
                        else:
                            print_result(False, f"Status: {status}")
                    else:
                        print_result(False, f"Failed: {result.get('error', 'Unknown error')}")
    
    return working_endpoints

def test_api_discovery():
    """Try to discover API structure through common patterns"""
    print_section("API DISCOVERY - TESTING COMMON PATTERNS")
    
    discovery_urls = [
        "https://docid.africapidalliance.org/api",
        "https://docid.africapidalliance.org/api/v1",
        "https://docid.africapidalliance.org/api/docs",
        "https://docid.africapidalliance.org/api/swagger",
        "https://docid.africapidalliance.org/apidocs",
        "https://docid.africapidalliance.org/api/v1/docs",
    ]
    
    for url in discovery_urls:
        print(f"\nChecking: {url}")
        result = test_endpoint(url)
        
        if result['success']:
            status = result['status_code']
            if status == 200:
                print_result(True, f"Found active endpoint!")
                if result['json']:
                    print(f"  📝 Response type: JSON")
                    print(f"  📝 Keys: {list(result['json'].keys())[:10]}")
                else:
                    print(f"  📝 Response type: {result.get('headers', {}).get('content-type', 'unknown')}")
            else:
                print_result(False, f"Status: {status}")

def test_direct_database_style():
    """Test if the API uses direct database-style endpoints"""
    print_section("TESTING DIRECT DATABASE-STYLE ENDPOINTS")
    
    db_style_urls = [
        "https://docid.africapidalliance.org/api/v1/publication_comments",
        "https://docid.africapidalliance.org/api/v1/publicationcomments",
        "https://docid.africapidalliance.org/api/v1/comments",
        "https://docid.africapidalliance.org/api/comments",
        "https://docid.africapidalliance.org/comments",
    ]
    
    for base_url in db_style_urls:
        # Try with and without publication filter
        test_urls = [
            base_url,
            f"{base_url}?publication_id=1",
            f"{base_url}/1",
        ]
        
        for url in test_urls:
            print(f"\nTesting: {url}")
            result = test_endpoint(url)
            
            if result['success']:
                status = result['status_code']
                if status == 200:
                    print_result(True, f"Found working endpoint!")
                    if result['json']:
                        data = result['json']
                        print(f"  📊 Response structure: {type(data).__name__}")
                        if isinstance(data, list):
                            print(f"  📊 Array with {len(data)} items")
                            if data:
                                print(f"  📊 First item keys: {list(data[0].keys())[:5]}")
                        elif isinstance(data, dict):
                            print(f"  📊 Object with keys: {list(data.keys())[:5]}")
                    return url
                else:
                    print_result(False, f"Status: {status}")

def test_with_authentication():
    """Test endpoints with different authentication methods"""
    print_section("TESTING WITH AUTHENTICATION")
    
    # Try different auth headers
    auth_variations = [
        {"Authorization": "Bearer test_token"},
        {"X-API-Key": "test_key"},
        {"API-Key": "test_key"},
        {"X-Auth-Token": "test_token"},
    ]
    
    test_url = "https://docid.africapidalliance.org/api/v1/comments/get-comments/1"
    
    for auth_header in auth_variations:
        print(f"\nTesting with auth header: {list(auth_header.keys())[0]}")
        result = test_endpoint(test_url, headers=auth_header)
        
        if result['success']:
            status = result['status_code']
            if status == 200:
                print_result(True, f"Success with this auth method!")
                return auth_header
            elif status == 401:
                print_result(False, f"Invalid credentials (401)")
            elif status == 403:
                print_result(False, f"Forbidden (403)")
            else:
                print_result(False, f"Status: {status}")

def analyze_error_responses():
    """Analyze error responses for clues about correct endpoint"""
    print_section("ANALYZING ERROR RESPONSES")
    
    test_url = "https://docid.africapidalliance.org/api/v1/comments/get-comments/1"
    
    print(f"\nAnalyzing error from: {test_url}")
    result = test_endpoint(test_url)
    
    if result['success']:
        if result['status_code'] == 500 and result['json']:
            error_data = result['json']
            print("Server Error Details:")
            print(f"  Error message: {error_data.get('error', 'N/A')}")
            
            # Check if error mentions correct path
            if 'error' in error_data:
                error_msg = error_data['error']
                if 'not found' in error_msg.lower():
                    print("  💡 Endpoint doesn't exist - need different path")
                elif 'database' in error_msg.lower():
                    print("  💡 Database issue - endpoint might be correct")
                elif 'internal' in error_msg.lower():
                    print("  💡 Internal server error - endpoint might be correct but broken")

def main():
    """Run all tests to find working comments endpoint"""
    print("🔍 COMMENTS API ENDPOINT DISCOVERY TOOL")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run discovery tests
    test_api_discovery()
    
    # Test endpoint variations
    working_endpoints = test_fetch_comments_variations()
    
    # Test database-style endpoints
    db_endpoint = test_direct_database_style()
    
    # Test with authentication
    auth_method = test_with_authentication()
    
    # Analyze errors
    analyze_error_responses()
    
    # Summary
    print_section("SUMMARY")
    
    if working_endpoints:
        print_result(True, f"Found {len(working_endpoints)} working endpoint(s)!")
        for ep in working_endpoints:
            print(f"\n  📍 Working: {ep['url']}")
            print(f"     Pattern: {ep['pattern']}")
            print(f"     Publication ID: {ep['publication_id']}")
    else:
        print_result(False, "No working comments endpoints found")
        print("\nPossible issues:")
        print("  1. Comments API not deployed yet")
        print("  2. Different endpoint structure needed")
        print("  3. Authentication required")
        print("  4. Server-side configuration issue")
    
    if db_endpoint:
        print(f"\n  📍 Database-style endpoint found: {db_endpoint}")
    
    if auth_method:
        print(f"\n  🔐 Authentication method that worked: {list(auth_method.keys())[0]}")
    
    print(f"\n⏱️ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if working_endpoints or db_endpoint else 1

if __name__ == "__main__":
    sys.exit(main())