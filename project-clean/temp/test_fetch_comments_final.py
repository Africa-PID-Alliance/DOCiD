#!/usr/bin/env python3
"""
Final test script for fetching comments by publication ID
"""
import requests
import json
from datetime import datetime

BASE_URL = "https://docid.africapidalliance.org/api/v1"

def test_fetch_comments_by_publication():
    """Test fetching comments by publication ID"""
    print("=" * 60)
    print("TEST: FETCHING COMMENTS BY PUBLICATION ID")
    print("=" * 60)
    
    # First, add some test comments to ensure we have data
    publication_id = 1
    
    # Add first comment
    comment_data = {
        "publication_id": publication_id,
        "user_id": 1,
        "comment_text": f"This is a test comment created at {datetime.now().isoformat()}",
        "comment_type": "general"
    }
    
    print(f"\n1. Adding a test comment to publication {publication_id}...")
    response = requests.post(f"{BASE_URL}/comments/add-comment", json=comment_data)
    if response.status_code == 201:
        comment1 = response.json()['comment']
        print(f"   ✅ Comment added with ID: {comment1['id']}")
    else:
        print(f"   ❌ Failed to add comment: {response.status_code}")
    
    # Add a reply to the first comment
    reply_data = {
        "publication_id": publication_id,
        "user_id": 2,
        "comment_text": f"This is a reply to the first comment at {datetime.now().isoformat()}",
        "comment_type": "general",
        "parent_comment_id": comment1['id'] if 'comment1' in locals() else None
    }
    
    print(f"\n2. Adding a reply to the first comment...")
    response = requests.post(f"{BASE_URL}/comments/add-comment", json=reply_data)
    if response.status_code == 201:
        comment2 = response.json()['comment']
        print(f"   ✅ Reply added with ID: {comment2['id']}")
    else:
        print(f"   ❌ Failed to add reply: {response.status_code}")
    
    # Add another top-level comment
    comment_data2 = {
        "publication_id": publication_id,
        "user_id": 3,
        "comment_text": f"Another comment for testing at {datetime.now().isoformat()}",
        "comment_type": "review"
    }
    
    print(f"\n3. Adding another comment to publication {publication_id}...")
    response = requests.post(f"{BASE_URL}/comments/add-comment", json=comment_data2)
    if response.status_code == 201:
        comment3 = response.json()['comment']
        print(f"   ✅ Comment added with ID: {comment3['id']}")
    else:
        print(f"   ❌ Failed to add comment: {response.status_code}")
    
    # Now fetch all comments for the publication
    print(f"\n4. FETCHING ALL COMMENTS FOR PUBLICATION {publication_id}...")
    print("-" * 60)
    
    url = f"{BASE_URL}/comments/get-comments/{publication_id}"
    response = requests.get(url)
    
    print(f"   URL: {url}")
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n   ✅ SUCCESS! Retrieved comments for publication {publication_id}")
        print(f"\n   📊 SUMMARY:")
        print(f"      - Publication ID: {data['publication_id']}")
        print(f"      - Total Comments: {data['total_comments']}")
        print(f"      - Comments Retrieved: {len(data['comments'])}")
        
        if data['comments']:
            print(f"\n   📝 COMMENTS DETAILS:")
            for i, comment in enumerate(data['comments'], 1):
                print(f"\n      Comment {i}:")
                print(f"         - ID: {comment['id']}")
                print(f"         - User: {comment.get('user_name', 'Unknown')} (ID: {comment['user_id']})")
                print(f"         - Text: {comment['comment_text'][:50]}...")
                print(f"         - Type: {comment['comment_type']}")
                print(f"         - Status: {comment['status']}")
                print(f"         - Likes: {comment['likes_count']}")
                print(f"         - Is Reply: {'Yes' if comment['parent_comment_id'] else 'No'}")
                if comment['parent_comment_id']:
                    print(f"         - Parent Comment ID: {comment['parent_comment_id']}")
                print(f"         - Created: {comment['created_at']}")
        else:
            print(f"\n   ℹ️ No comments found for this publication")
        
        # Test fetching comments without replies
        print(f"\n5. FETCHING TOP-LEVEL COMMENTS ONLY...")
        print("-" * 60)
        
        url_no_replies = f"{url}?include_replies=false"
        response_no_replies = requests.get(url_no_replies)
        
        if response_no_replies.status_code == 200:
            data_no_replies = response_no_replies.json()
            print(f"   ✅ Top-level comments only: {len(data_no_replies['comments'])} comments")
        
        return True
    else:
        print(f"\n   ❌ FAILED to fetch comments")
        print(f"   Error: {response.text}")
        return False

def main():
    print("\n🔍 COMMENTS FETCHING TEST")
    print("=" * 60)
    print(f"API Endpoint: {BASE_URL}/comments/get-comments/<publication_id>")
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_fetch_comments_by_publication()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED - Comments fetching is working correctly!")
    else:
        print("❌ TEST FAILED - Issues with fetching comments")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())