#!/usr/bin/env python3
"""
Truncate ALL database tables

This script truncates all database tables, including seeded data.
Use this when you want to completely reset the database.

After running this script, you should run:
1. ./run_migrations.sh upgrade (to recreate table structure if needed)
2. python scripts/seed_db.py (to repopulate lookup data)
"""

import os
import sys
from sqlalchemy import inspect, text, MetaData
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to system path to import from app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app import create_app, db
    print("✅ Successfully imported app modules")
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running this script from the correct directory")
    sys.exit(1)

def truncate_all_tables():
    """Truncate all tables in the database"""
    
    app = create_app()
    
    with app.app_context():
        print("DOCiD Database Complete Reset Script")
        print("=" * 40)
        print("⚠️  WARNING: This will delete ALL data from ALL tables!")
        print()
        
        # Ask for double confirmation
        confirmation1 = input("Are you sure you want to delete ALL data? (yes/no): ").strip().lower()
        if confirmation1 not in ['yes', 'y']:
            print("❌ Operation cancelled")
            return
            
        confirmation2 = input("This action cannot be undone. Type 'DELETE ALL' to confirm: ").strip()
        if confirmation2 != 'DELETE ALL':
            print("❌ Operation cancelled - confirmation text did not match")
            return
        
        try:
            print()
            print("🗑️  Starting complete database truncation...")
            
            # Get all table names from the database
            inspector = inspect(db.engine)
            table_names = inspector.get_table_names()
            
            print(f"Found {len(table_names)} tables to truncate:")
            for table_name in table_names:
                print(f"  - {table_name}")
            
            print()
            
            with db.session.begin():
                # Disable foreign key checks
                db.session.execute(text("SET session_replication_role = replica;"))
                
                # Truncate all tables
                success_count = 0
                for table_name in table_names:
                    try:
                        # Skip migration history table
                        if table_name == 'alembic_version':
                            print(f"⏭️  Skipping migration table: {table_name}")
                            continue
                            
                        db.session.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
                        print(f"✅ Truncated: {table_name}")
                        success_count += 1
                        
                    except Exception as e:
                        print(f"❌ Error truncating {table_name}: {str(e)}")
                
                # Reset all sequences
                sequences = inspector.get_sequence_names()
                print(f"\n🔄 Resetting {len(sequences)} sequences...")
                
                for sequence_name in sequences:
                    try:
                        db.session.execute(text(f"ALTER SEQUENCE {sequence_name} RESTART WITH 1"))
                        print(f"✅ Reset sequence: {sequence_name}")
                    except Exception as e:
                        print(f"❌ Error resetting sequence {sequence_name}: {str(e)}")
                
                # Re-enable foreign key checks
                db.session.execute(text("SET session_replication_role = DEFAULT;"))
                
                print()
                print(f"🎉 Successfully truncated {success_count} tables!")
                
        except Exception as e:
            print(f"❌ Error during truncation: {str(e)}")
            print("Changes have been rolled back")
            sys.exit(1)
        
        print()
        print("✅ Complete database reset completed!")
        print()
        print("Next steps:")
        print("1. Run migrations (if needed): ./run_migrations.sh upgrade")
        print("2. Seed lookup data: python scripts/seed_db.py")

if __name__ == "__main__":
    truncate_all_tables()
