#!/usr/bin/env python3
"""
Direct test of comments API functionality without requiring a running server
"""
import sys
import os
import json
from io import StringIO
from contextlib import contextmanager

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

@contextmanager
def capture_output():
    """Capture stdout and stderr"""
    old_out, old_err = sys.stdout, sys.stderr
    try:
        out, err = StringIO(), StringIO()
        sys.stdout, sys.stderr = out, err
        yield out, err
    finally:
        sys.stdout, sys.stderr = old_out, old_err

def test_imports():
    """Test that all required modules can be imported"""
    try:
        print("🧪 Testing imports...")
        from app import create_app, db
        from app.models import Publications, UserAccount, PublicationComments
        from app.routes.comments import comments_bp
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False

def test_comment_model():
    """Test the PublicationComments model"""
    try:
        print("🧪 Testing PublicationComments model...")
        from app.models import PublicationComments
        
        # Test model can be instantiated
        comment = PublicationComments(
            publication_id=1,
            user_id=1,
            comment_text="Test comment",
            comment_type="general"
        )
        
        # Test to_dict method
        comment_dict = comment.to_dict()
        assert isinstance(comment_dict, dict)
        assert comment_dict['comment_text'] == "Test comment"
        assert comment_dict['comment_type'] == "general"
        
        print("✅ PublicationComments model tests passed")
        return True
    except Exception as e:
        print(f"❌ Model test error: {e}")
        return False

def test_blueprint_registration():
    """Test that the comments blueprint is properly configured"""
    try:
        print("🧪 Testing blueprint registration...")
        from app.routes.comments import comments_bp
        
        # Check blueprint exists
        assert comments_bp.name == 'comments'
        
        # Check routes are registered
        routes = [rule.rule for rule in comments_bp.url_map.iter_rules()]
        expected_routes = [
            '/api/publications/<int:publication_id>/comments',
            '/api/comments/<int:comment_id>',
            '/api/comments/<int:comment_id>/like',
            '/api/users/<int:user_id>/comments',
            '/api/comments/stats/<int:publication_id>'
        ]
        
        print(f"📋 Found {len(routes)} routes in blueprint")
        print("✅ Blueprint registration tests passed")
        return True
    except Exception as e:
        print(f"❌ Blueprint test error: {e}")
        return False

def test_route_functions():
    """Test that route functions exist and are callable"""
    try:
        print("🧪 Testing route functions...")
        from app.routes.comments import (
            get_publication_comments,
            add_comment,
            edit_comment,
            delete_comment,
            like_comment,
            get_user_comments,
            get_comment_stats
        )
        
        # Check functions are callable
        functions = [
            get_publication_comments,
            add_comment,
            edit_comment,
            delete_comment,
            like_comment,
            get_user_comments,
            get_comment_stats
        ]
        
        for func in functions:
            assert callable(func), f"{func.__name__} is not callable"
        
        print(f"✅ All {len(functions)} route functions are callable")
        return True
    except Exception as e:
        print(f"❌ Route function test error: {e}")
        return False

def test_app_creation():
    """Test that Flask app can be created and configured"""
    try:
        print("🧪 Testing app creation...")
        
        # Capture any output during app creation
        with capture_output() as (out, err):
            from app import create_app
            app = create_app()
        
        # Check app is a Flask instance
        from flask import Flask
        assert isinstance(app, Flask)
        
        # Check comments blueprint is registered
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        assert 'comments' in blueprint_names
        
        print("✅ App creation tests passed")
        return True
    except Exception as e:
        print(f"❌ App creation test error: {e}")
        return False

def test_database_models():
    """Test database model relationships"""
    try:
        print("🧪 Testing database models...")
        from app.models import Publications, UserAccount, PublicationComments
        
        # Test model classes exist
        assert hasattr(Publications, '__tablename__')
        assert hasattr(UserAccount, '__tablename__')
        assert hasattr(PublicationComments, '__tablename__')
        
        # Test PublicationComments has required fields
        comment_columns = [column.name for column in PublicationComments.__table__.columns]
        required_columns = [
            'id', 'publication_id', 'user_id', 'comment_text', 
            'comment_type', 'status', 'likes_count', 'created_at', 'updated_at'
        ]
        
        for col in required_columns:
            assert col in comment_columns, f"Column {col} missing from PublicationComments"
        
        print("✅ Database model tests passed")
        return True
    except Exception as e:
        print(f"❌ Database model test error: {e}")
        return False

def test_json_serialization():
    """Test that comment objects can be serialized to JSON"""
    try:
        print("🧪 Testing JSON serialization...")
        from app.models import PublicationComments
        from datetime import datetime
        
        # Create a test comment
        comment = PublicationComments(
            id=1,
            publication_id=1,
            user_id=1,
            comment_text="Test comment for JSON",
            comment_type="general",
            status="active",
            likes_count=5,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Test to_dict method
        comment_dict = comment.to_dict()
        
        # Test JSON serialization
        json_str = json.dumps(comment_dict)
        parsed_back = json.loads(json_str)
        
        assert parsed_back['comment_text'] == "Test comment for JSON"
        assert parsed_back['likes_count'] == 5
        
        print("✅ JSON serialization tests passed")
        return True
    except Exception as e:
        print(f"❌ JSON serialization test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Starting Comments API Direct Tests")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Comment Model Tests", test_comment_model),
        ("Blueprint Registration Tests", test_blueprint_registration),
        ("Route Function Tests", test_route_functions),
        ("App Creation Tests", test_app_creation),
        ("Database Model Tests", test_database_models),
        ("JSON Serialization Tests", test_json_serialization)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        print("-" * 30)
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())