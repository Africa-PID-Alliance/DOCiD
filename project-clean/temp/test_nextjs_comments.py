#!/usr/bin/env python3
"""
Test Next.js comments API repeatedly until success
"""
import requests
import json
import time

def test_nextjs_comments():
    url = 'http://localhost:3000/api/publications/27/comments'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:142.0) Gecko/20100101 Firefox/142.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:3000',
        'Connection': 'keep-alive',
        'Referer': 'http://localhost:3000/docid/20.500.14351%2Fd6c0cff6f7267e2f75ba',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Priority': 'u=0'
    }
    
    # Test data variations
    test_data_variations = [
        # Original data
        {"comment_text": "ttttt", "comment_type": "general", "parent_comment_id": 0, "user_id": 2},
        # Try with null
        {"comment_text": "ttttt with null", "comment_type": "general", "parent_comment_id": None, "user_id": 2},
        # Try without parent_comment_id
        {"comment_text": "ttttt no parent", "comment_type": "general", "user_id": 2},
    ]
    
    attempt = 1
    max_attempts = 10
    
    while attempt <= max_attempts:
        print(f"\n=== ATTEMPT {attempt} ===")
        
        for i, data in enumerate(test_data_variations):
            print(f"\nTesting variation {i+1}: {json.dumps(data)}")
            
            try:
                response = requests.post(url, headers=headers, json=data, timeout=10)
                
                print(f"Status Code: {response.status_code}")
                print(f"Response Headers: {dict(response.headers)}")
                
                try:
                    response_json = response.json()
                    print(f"Response Body: {json.dumps(response_json, indent=2)}")
                    
                    # Check for success
                    if response.status_code == 201 or response.status_code == 200:
                        if 'error' not in response_json:
                            print(f"\n🎉 SUCCESS! Comment created successfully!")
                            print(f"Final working payload: {json.dumps(data, indent=2)}")
                            return True
                        
                except json.JSONDecodeError:
                    print(f"Response Body (raw): {response.text}")
                
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
            
            print("-" * 50)
        
        attempt += 1
        if attempt <= max_attempts:
            print(f"Waiting 2 seconds before next attempt...")
            time.sleep(2)
    
    print(f"\n❌ All {max_attempts} attempts failed.")
    return False

if __name__ == "__main__":
    print("Testing Next.js Comments API...")
    print("=" * 60)
    
    success = test_nextjs_comments()
    
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed after all attempts.")
        print("\nPossible issues:")
        print("1. Next.js API route has a bug with parent_comment_id transformation")
        print("2. Flask endpoint URL mismatch in Next.js API")
        print("3. Authentication/authorization issues")
        print("4. Next.js server not running or reachable")