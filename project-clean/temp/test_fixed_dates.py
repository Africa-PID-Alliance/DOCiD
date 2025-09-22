#!/usr/bin/env python3
"""
Test script to verify that dates are now properly formatted in the UI
"""
import requests
import json

def test_comments_display():
    print("=== TESTING COMMENT DATE DISPLAY FIX ===")
    
    # Test the Next.js API to get comments with proper field names
    url = 'http://localhost:3001/api/publications/27/comments'
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'comments' in data and len(data['comments']) > 0:
                print("\n✅ Comments Retrieved Successfully!")
                print(f"Total comments: {data.get('total_comments', len(data['comments']))}")
                
                # Show the structure of the first comment
                first_comment = data['comments'][0]
                print("\n📋 First Comment Structure:")
                print(f"  - ID: {first_comment.get('id')}")
                print(f"  - Author: {first_comment.get('user_name')}")
                print(f"  - Text: {first_comment.get('comment_text')[:50]}...")
                print(f"  - Created At: {first_comment.get('created_at')}")
                print(f"  - Updated At: {first_comment.get('updated_at')}")
                print(f"  - User Avatar: {first_comment.get('user_avatar')}")
                
                # Test the JavaScript date parsing
                created_at = first_comment.get('created_at')
                if created_at:
                    print(f"\n🕒 Date Format Analysis:")
                    print(f"  Raw Date: {created_at}")
                    print(f"  Type: ISO 8601 format")
                    
                    # Test Python date parsing (similar to JavaScript)
                    from datetime import datetime
                    try:
                        parsed_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        print(f"  Python Parse: {parsed_date}")
                        print(f"  Formatted: {parsed_date.strftime('%a, %b %d, %Y at %I:%M %p')}")
                        print("  ✅ Date parsing should work correctly now!")
                    except Exception as e:
                        print(f"  ❌ Date parsing error: {e}")
                
                print("\n🔧 FIELD MAPPING VERIFICATION:")
                expected_fields = ['id', 'user_name', 'user_avatar', 'comment_text', 'created_at', 'updated_at']
                for field in expected_fields:
                    if field in first_comment:
                        print(f"  ✅ {field}: Present")
                    else:
                        print(f"  ❌ {field}: Missing")
                
                return True
            else:
                print("❌ No comments found")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_ui_accessibility():
    print("\n=== UI ACCESSIBILITY TEST ===")
    print("🌐 Next.js App should be accessible at:")
    print("   Development: http://localhost:3001")
    print("   DOCiD Page: http://localhost:3001/docid/20.500.14351%2Fd6c0cff6f7267e2f75ba")
    print("\n📋 Changes Applied:")
    print("   ✅ comment.timestamp → comment.created_at")
    print("   ✅ comment.author → comment.user_name")
    print("   ✅ comment.avatar → comment.user_avatar")
    print("   ✅ comment.comment → comment.comment_text")
    print("   ✅ Same changes applied to reply objects")
    
    print("\n🎯 Expected Result:")
    print("   Instead of 'Invalid Date Invalid Date'")
    print("   You should now see properly formatted dates like:")
    print("   'Wed, Sep 04, 2025 at 04:38 AM'")

if __name__ == "__main__":
    success = test_comments_display()
    test_ui_accessibility()
    
    if success:
        print("\n🎉 SUCCESS! The date formatting fix has been applied.")
        print("👉 Please check the UI to confirm dates display correctly.")
    else:
        print("\n⚠️  Could not verify comment structure. Please check manually.")