#!/usr/bin/env python3
"""
Clear all database tables except those seeded in seed_db.py

This script will delete all records from database tables except for the ones that are seeded
with essential data in the seed_db.py script. This is useful for clearing out
test data while preserving reference/lookup data.

Uses DELETE instead of TRUNCATE to avoid requiring superuser privileges.

Seeded tables (preserved):
- UserAccount (demo user)
- ResourceTypes (lookup data)
- CreatorsRoles (lookup data)
- creatorsIdentifiers (lookup data)
- FunderTypes (lookup data)
- PublicationIdentifierTypes (lookup data)
- PublicationTypes (lookup data)
- DocIdLookup (PID lookup data)

Tables to be cleared:
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
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to system path to import from app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app import create_app, db
    from app.models import (
        # Models to keep (seeded models)
        UserAccount, ResourceTypes, CreatorsRoles, creatorsIdentifiers,
        FunderTypes, PublicationIdentifierTypes, PublicationTypes, DocIdLookup,
        
        # Models to clear
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

def clear_table(model_class, session):
    """
    Clears all records from a specific table using DELETE.
    
    Args:
        model_class: The SQLAlchemy model class
        session: Database session
    """
    try:
        table_name = model_class.__tablename__
        
        # Use DELETE instead of TRUNCATE to avoid permission issues
        result = session.execute(text(f'DELETE FROM "{table_name}"'))
        count = result.rowcount
        
        # Reset sequence if table has an id column
        if hasattr(model_class, 'id'):
            sequence_name = f"{table_name}_id_seq"
            try:
                session.execute(text(f'ALTER SEQUENCE "{sequence_name}" RESTART WITH 1'))
            except Exception:
                # Sequence might not exist or might have different name
                pass
        
        print(f"✅ Deleted {count} records from table: {table_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing table {model_class.__tablename__}: {str(e)}")
        return False

def main():
    """Main function to clear all non-seeded tables"""
    
    app = create_app()
    
    with app.app_context():
        print("DOCiD Database Cleanup Script")
        print("=" * 40)
        print("This script will DELETE all records from tables EXCEPT those seeded in seed_db.py")
        print("Note: Uses DELETE instead of TRUNCATE to work without superuser privileges")
        print()
        
        # Models that are seeded and should be preserved
        seeded_models = [
            UserAccount, ResourceTypes, CreatorsRoles, creatorsIdentifiers,
            FunderTypes, PublicationIdentifierTypes, PublicationTypes, DocIdLookup
        ]
        
        # Models to be cleared (in order to respect foreign key constraints)
        models_to_clear = [
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
        print("Tables to be cleared:")
        for model in models_to_clear:
            print(f"  - {model.__tablename__}")
        
        print()
        
        # Ask for confirmation
        confirmation = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
        
        if confirmation not in ['yes', 'y']:
            print("❌ Operation cancelled by user")
            return
        
        print()
        print("Starting cleanup process...")
        
        success_count = 0
        failure_count = 0
        
        try:
            # Clear each table in a separate transaction
            for model_class in models_to_clear:
                try:
                    with db.session.begin():
                        if clear_table(model_class, db.session):
                            success_count += 1
                        else:
                            failure_count += 1
                except Exception as e:
                    print(f"❌ Failed to clear {model_class.__tablename__}: {str(e)}")
                    failure_count += 1
            
            print()
            print("Cleanup Summary:")
            print(f"✅ Successfully cleared: {success_count} tables")
            
            if failure_count > 0:
                print(f"❌ Failed to clear: {failure_count} tables")
            else:
                print("🎉 All tables cleared successfully!")
                    
        except Exception as e:
            print(f"❌ Error during cleanup: {str(e)}")
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
        
        # Check cleared tables (should be empty)
        print()
        print("Cleared tables (should be empty):")
        for model in models_to_clear:
            try:
                count = db.session.query(model).count()
                status = "✅ Empty" if count == 0 else f"❌ Still has {count} records"
                print(f"  {model.__tablename__}: {status}")
            except Exception as e:
                print(f"  {model.__tablename__}: Error counting - {str(e)}")
        
        print()
        print("✅ Cleanup process completed successfully!")
        print()
        print("Note: To repopulate seeded data, run:")
        print("  python scripts/seed_db.py")

if __name__ == "__main__":
    main()
