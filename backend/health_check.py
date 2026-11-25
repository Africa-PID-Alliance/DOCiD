#!/usr/bin/env python3
"""
DOCiD Backend System Health Check

This script performs a comprehensive health check of the DOCiD backend system,
verifying all components are working correctly.
"""

import os
import sys
import subprocess
from datetime import datetime

# Add the parent directory to system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_command(command, description, check_output=True):
    """Run a shell command and return the result."""
    try:
        print(f"🔍 {description}...")
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print(f"  ✅ Success")
            if check_output and result.stdout.strip():
                # Show first few lines of output
                lines = result.stdout.strip().split('\n')[:3]
                for line in lines:
                    print(f"    {line}")
            return True
        else:
            print(f"  ❌ Failed: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False

def check_flask_app():
    """Check if Flask app can be imported and configured."""
    try:
        print("🔍 Checking Flask application import...")
        from app import create_app, db
        app = create_app()
        with app.app_context():
            print("  ✅ Flask app created successfully")
            return True
    except Exception as e:
        print(f"  ❌ Flask app import failed: {str(e)}")
        return False

def check_database_connection():
    """Check database connection and seeded data."""
    try:
        print("🔍 Checking database connection and seeded data...")
        from app import create_app, db
        from app.models import UserAccount, ResourceTypes, PublicationTypes
        
        app = create_app()
        with app.app_context():
            # Check if we can query the database
            user_count = db.session.query(UserAccount).count()
            resource_count = db.session.query(ResourceTypes).count()
            pub_type_count = db.session.query(PublicationTypes).count()
            
            print(f"  ✅ Database connected successfully")
            print(f"    Users: {user_count}")
            print(f"    Resource Types: {resource_count}")
            print(f"    Publication Types: {pub_type_count}")
            return True
    except Exception as e:
        print(f"  ❌ Database check failed: {str(e)}")
        return False

def main():
    """Run the complete system health check."""
    print("="*60)
    print("🏥 DOCiD Backend System Health Check")
    print("="*60)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    checks = []
    
    # 1. Check virtual environment
    if 'VIRTUAL_ENV' in os.environ:
        print("✅ Virtual environment is active")
        print(f"   Path: {os.environ['VIRTUAL_ENV']}")
    else:
        print("⚠️  Virtual environment not detected (make sure to activate it)")
    print()
    
    # 2. Check Python dependencies
    checks.append(run_command("python -c 'import flask, flask_migrate; print(\"Flask and Flask-Migrate available\")'", 
                             "Checking Python dependencies"))
    
    # 3. Check Flask app
    checks.append(check_flask_app())
    
    # 4. Check database
    checks.append(check_database_connection())
    
    # 5. Check migrations
    checks.append(run_command(f'"{sys.executable}" -m flask --app run.py db current',
                             "Checking migration status"))
    
    # 6. Check logs directory
    if os.path.exists('logs'):
        print("🔍 Checking logs directory...")
        log_files = os.listdir('logs')
        print(f"  ✅ Logs directory exists with {len(log_files)} files")
        checks.append(True)
    else:
        print("🔍 Checking logs directory...")
        print("  ⚠️  Logs directory not found")
        checks.append(False)
    
    # 7. Check uploads directory
    if os.path.exists('uploads'):
        print("🔍 Checking uploads directory...")
        upload_files = os.listdir('uploads')
        print(f"  ✅ Uploads directory exists with {len(upload_files)} files")
        checks.append(True)
    else:
        print("🔍 Checking uploads directory...")
        print("  ⚠️  Uploads directory not found")
        checks.append(False)
    
    # Summary
    print()
    print("="*60)
    print("📋 HEALTH CHECK SUMMARY")
    print("="*60)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print("🎉 All checks passed! Your DOCiD backend is healthy and ready to use.")
        print()
        print("🚀 You can now:")
        print("   • Run the application: flask run --host=0.0.0.0 --port=5000")
        print("   • Create publications via API")
        print("   • Process CSTR identifiers")
        print("   • Manage database with cleanup tools")
    else:
        print(f"⚠️  {total - passed} out of {total} checks failed.")
        print("   Please review the issues above before deploying to production.")
    
    print()
    print("📚 Available documentation:")
    docs = ['README.md', 'QUICKSTART.md', 'DEV_SETUP.md', 'PRODUCTION_DEPLOYMENT.md', 'DATABASE_TOOLS.md']
    for doc in docs:
        if os.path.exists(doc):
            print(f"   • {doc}")
    
    print(f"\n🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Health check interrupted by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during health check: {e}")
        sys.exit(1)
