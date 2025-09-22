#!/usr/bin/env python3
"""
Truncate all database tables except those seeded in seed_db.py

This script will truncate all database tables except for the ones that are seeded
with essential data in the seed_db.py script. This is useful for clearing out
test data while preserving reference/lookup data.

Seeded tables (preserved):
- UserAccount (demo user)
- ResourceTypes (lookup data)
- CreatorsRoles (lookup data)
- creatorsIdentifiers (lookup data)
- FunderTypes (lookup data)
- PublicationIdentifierTypes (lookup data)
- PublicationTypes (lookup data)
- DocIdLookup (PID lookup data)

Tables to be truncated:
- RegistrationTokens
- PasswordResets
- DocIDObject
- ObjectDataset
- ObjectDataSetType
- Publications
- PublicationFiles
- PublicationDocuments
- PublicationCreators
- PublicationOrganization
- PublicationFunders
- PublicationProjects
- CrossrefMetadata
"""

import os
import sys
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to system path to import from app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app import create_app, db
    from app.models import (
        # Models to keep (seeded models)
        UserAccount, ResourceTypes, CreatorsRoles, creatorsIdentifiers,
        FunderTypes, PublicationIdentifierTypes, PublicationTypes, DocIdLookup,
        
        # Models to truncate
        RegistrationTokens, PasswordResets, DocIDObject, ObjectDataset, 
        ObjectDataSetType, Publications, PublicationFiles, PublicationDocuments,
        PublicationCreators, PublicationOrganization, PublicationFunders,
        PublicationProjects, CrossrefMetadata
    )
    print("✅ Successfully imported all required modules")
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running this script from the correct directory")
    sys.exit(1)

def truncate_table(model_class, session):
    """
    Truncates a specific table, fallback to DELETE if TRUNCATE fails.
    
    Args:
        model_class: The SQLAlchemy model class
        session: Database session
    """
    try:
        table_name = model_class.__tablename__
        
        # Try TRUNCATE first (faster), fallback to DELETE if permission denied
        try:
            # Try with foreign key constraints disabled
            session.execute(text("SET session_replication_role = replica;"))
            session.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
            session.execute(text("SET session_replication_role = DEFAULT;"))
            print(f"✅ Truncated table: {table_name}")
            
        except Exception as truncate_error:
            if "permission denied" in str(truncate_error).lower() or "insufficient" in str(truncate_error).lower():
                # Rollback the failed transaction first
                session.rollback()
                
                # Fallback to DELETE method (works without superuser privileges)
                print(f"⚠️  TRUNCATE failed for {table_name}, using DELETE instead...")
                result = session.execute(text(f'DELETE FROM "{table_name}"'))
                count = result.rowcount
                print(f"✅ Deleted {count} records from table: {table_name}")
            else:
                raise truncate_error
        
        # Reset sequence if table has an id column
        if hasattr(model_class, 'id'):
            sequence_name = f"{table_name}_id_seq"
            try:
                session.execute(text(f'ALTER SEQUENCE "{sequence_name}" RESTART WITH 1'))
            except Exception:
                # Sequence might not exist or might have different name
                pass
        
        return True
        
    except Exception as e:
        print(f"❌ Error clearing table {model_class.__tablename__}: {str(e)}")
        return False

def main():
    """Main function to truncate all non-seeded tables"""
    
    app = create_app()
    
    with app.app_context():
        print("DOCiD Database Truncation Script")
        print("=" * 40)
        print("This script will truncate all tables EXCEPT those seeded in seed_db.py")
        print()
        
        # Models that are seeded and should be preserved
        seeded_models = [
            UserAccount, ResourceTypes, CreatorsRoles, creatorsIdentifiers,
            FunderTypes, PublicationIdentifierTypes, PublicationTypes, DocIdLookup
        ]
        
        # Models to be truncated (in order to respect foreign key constraints)
        models_to_truncate = [
            # Start with child tables first to avoid foreign key issues
            PublicationDocuments,
            PublicationFiles,
            PublicationCreators,
            PublicationOrganization,
            PublicationFunders,
            PublicationProjects,
            Publications,  # Parent table for publication-related tables
            
            # Other independent tables
            CrossrefMetadata,
            ObjectDataset,
            DocIDObject,
            ObjectDataSetType,
            PasswordResets,
            RegistrationTokens,
        ]
        
        print("Tables to be preserved (seeded data):")
        for model in seeded_models:
            print(f"  - {model.__tablename__}")
        
        print()
        print("Tables to be truncated:")
        for model in models_to_truncate:
            print(f"  - {model.__tablename__}")
        
        print()
        
        # Ask for confirmation
        confirmation = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
        
        if confirmation not in ['yes', 'y']:
            print("❌ Operation cancelled by user")
            return
        
        print()
        print("Starting truncation process...")
        
        success_count = 0
        failure_count = 0
        
        try:
            # Process each table individually to avoid transaction rollback issues
            for model_class in models_to_truncate:
                try:
                    # Each table gets its own transaction to avoid cascade failures
                    if truncate_table(model_class, db.session):
                        db.session.commit()
                        success_count += 1
                    else:
                        db.session.rollback()
                        failure_count += 1
                except Exception as e:
                    print(f"❌ Failed to process {model_class.__tablename__}: {str(e)}")
                    db.session.rollback()
                    failure_count += 1
            
            print()
            print("Truncation Summary:")
            print(f"✅ Successfully cleared: {success_count} tables")
            
            if failure_count > 0:
                print(f"❌ Failed to clear: {failure_count} tables")
            else:
                print("🎉 All tables cleared successfully!")
                    
        except Exception as e:
            print(f"❌ Error during truncation: {str(e)}")
            sys.exit(1)
        
        print()
        print("Verification - Checking record counts:")
        
        # Check seeded tables (should have data)
        print()
        print("Seeded tables (should contain data):")
        for model in seeded_models:
            try:
                count = db.session.query(model).count()
                print(f"  {model.__tablename__}: {count} records")
            except Exception as e:
                print(f"  {model.__tablename__}: Error counting - {str(e)}")
        
        # Check truncated tables (should be empty)
        print()
        print("Truncated tables (should be empty):")
        for model in models_to_truncate:
            try:
                count = db.session.query(model).count()
                status = "✅ Empty" if count == 0 else f"❌ Still has {count} records"
                print(f"  {model.__tablename__}: {status}")
            except Exception as e:
                print(f"  {model.__tablename__}: Error counting - {str(e)}")
        
        print()
        print("✅ Truncation process completed successfully!")
        print()
        print("Note: To repopulate seeded data, run:")
        print("  python scripts/seed_db.py")

if __name__ == "__main__":
    main()
