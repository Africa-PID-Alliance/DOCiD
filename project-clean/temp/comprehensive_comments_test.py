#!/usr/bin/env python3
"""
Comprehensive Comments API Testing and Analysis
"""
import requests
import json
import time

def test_comprehensive():
    print("=" * 80)
    print("COMPREHENSIVE COMMENTS API ANALYSIS")
    print("=" * 80)
    
    # Test configurations
    nextjs_base = 'http://localhost:3000'
    flask_base = 'http://localhost:5001'
    publication_id = 27
    
    print("\n1. TESTING FLASK API DIRECTLY (Working)")
    print("-" * 50)
    
    # Test Flask direct POST with null parent_comment_id (should work)
    flask_url = f'{flask_base}/api/publications/{publication_id}/comments'
    flask_data = {
        "comment_text": "Direct Flask test - should work",
        "comment_type": "general",
        "parent_comment_id": None,  # Correct: null for root comments
        "user_id": 2
    }
    
    try:
        response = requests.post(flask_url, json=flask_data, timeout=10)
        print(f"Flask Direct POST: {response.status_code}")
        print(f"Flask Response: {response.json()}")
    except Exception as e:
        print(f"Flask Direct Error: {e}")
    
    print("\n2. TESTING FLASK WITH INVALID DATA (Should fail)")
    print("-" * 50)
    
    # Test Flask direct POST with 0 parent_comment_id (should fail)
    flask_bad_data = {
        "comment_text": "Direct Flask test - should fail",
        "comment_type": "general", 
        "parent_comment_id": 0,  # Wrong: causes foreign key error
        "user_id": 2
    }
    
    try:
        response = requests.post(flask_url, json=flask_bad_data, timeout=10)
        print(f"Flask Bad Data POST: {response.status_code}")
        print(f"Flask Bad Response: {response.json()}")
    except Exception as e:
        print(f"Flask Bad Data Error: {e}")
    
    print("\n3. TESTING NEXT.JS API (Currently Broken)")
    print("-" * 50)
    
    # Test Next.js API POST
    nextjs_url = f'{nextjs_base}/api/publications/{publication_id}/comments'
    nextjs_data = {
        "comment_text": "Next.js API test",
        "comment_type": "general",
        "parent_comment_id": None,  # We send null
        "user_id": 2
    }
    
    try:
        response = requests.post(nextjs_url, json=nextjs_data, timeout=15)
        print(f"Next.js POST Status: {response.status_code}")
        print(f"Next.js Response: {response.json()}")
    except Exception as e:
        print(f"Next.js Error: {e}")
    
    print("\n4. ANALYSIS AND ROOT CAUSE")
    print("-" * 50)
    print("✅ Flask API works with parent_comment_id: null")
    print("❌ Flask API fails with parent_comment_id: 0 (Foreign Key Violation)")
    print("❌ Next.js API converts null to 0 in line 179: parent_comment_id: body.parent_comment_id || 0")
    print("🔧 FIX: Change line 179 to use null instead of 0")
    
    print("\n5. PROPOSED FIX")
    print("-" * 50)
    fix_code = """
    // BEFORE (line 179):
    parent_comment_id: body.parent_comment_id || 0,
    
    // AFTER (proposed fix):
    parent_comment_id: body.parent_comment_id === 0 ? null : body.parent_comment_id,
    
    // OR even better:
    parent_comment_id: body.parent_comment_id || null,
    """
    print(fix_code)
    
    print("\n6. TESTING VERIFICATION")
    print("-" * 50)
    print("After applying the fix, the Next.js API should:")
    print("- Accept parent_comment_id: 0 from frontend") 
    print("- Convert it to null before sending to Flask")
    print("- Successfully create root comments")
    print("- Return 201 Created instead of 503 Service Unavailable")

if __name__ == "__main__":
    test_comprehensive()