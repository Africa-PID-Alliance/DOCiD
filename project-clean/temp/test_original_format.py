#!/usr/bin/env python3
"""
Test the original curl command format to verify fix
"""
import requests

def test_original_format():
    print("Testing original curl command format...")
    
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
    
    # Original format - exactly as the curl command
    data = {
        "comment_text": "ttttt",
        "comment_type": "general",
        "parent_comment_id": 0,  # Original problematic value
        "user_id": 2
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            print("\n🎉 SUCCESS! The original curl command format now works!")
        else:
            print(f"\n❌ Still failing with status {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_original_format()