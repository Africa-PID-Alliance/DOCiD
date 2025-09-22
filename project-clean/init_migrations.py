#!/usr/bin/env python3
"""
Simple Flask-Migrate initialization script for DOCiD
"""

import os
import sys
from flask import Flask
from flask_migrate import Migrate, init, migrate, upgrade, downgrade, current, history

# Add the parent directory to system path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the app and database
from app import create_app, db

# Import all models to ensure they're registered
from app.models import (
    UserAccount, Publications, PublicationFiles, PublicationDocuments,
    PublicationCreators, PublicationOrganization, PublicationFunders,
    PublicationProjects, ResourceTypes, FunderTypes, CreatorsRoles,
    creatorsIdentifiers, PublicationIdentifierTypes, PublicationTypes,
    DocIdLookup, CrossrefMetadata
)

def main():
    app = create_app()
    
    with app.app_context():
        print("DOCiD Flask-Migrate Setup")
        print("=" * 30)
        
        while True:
            print("\nAvailable commands:")
            print("1. Initialize migrations repository")
            print("2. Create a new migration")
            print("3. Apply migrations (upgrade)")
            print("4. Rollback migrations (downgrade)")
            print("5. Show current migration")
            print("6. Show migration history")
            print("7. Exit")
            
            choice = input("\nEnter your choice (1-7): ").strip()
            
            try:
                if choice == "1":
                    print("Initializing migrations repository...")
                    init()
                    print("✅ Migrations repository initialized!")
                    print("📁 A 'migrations' folder has been created.")
                    
                elif choice == "2":
                    message = input("Enter migration message (or press Enter for auto-generated): ").strip()
                    if not message:
                        message = None
                    
                    print("Creating migration...")
                    migrate(message=message)
                    print("✅ Migration created successfully!")
                    
                elif choice == "3":
                    print("Applying migrations to database...")
                    upgrade()
                    print("✅ Database upgraded successfully!")
                    
                elif choice == "4":
                    revision = input("Enter revision to downgrade to (or press Enter for previous): ").strip()
                    if not revision:
                        revision = "-1"
                    
                    print(f"Downgrading to revision: {revision}")
                    downgrade(revision)
                    print("✅ Database downgraded successfully!")
                    
                elif choice == "5":
                    print("Current migration revision:")
                    try:
                        current()
                    except Exception as e:
                        print(f"Error: {e}")
                        
                elif choice == "6":
                    print("Migration history:")
                    try:
                        history()
                    except Exception as e:
                        print(f"Error: {e}")
                        
                elif choice == "7":
                    print("Goodbye!")
                    break
                    
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Please check your database connection and try again.")

if __name__ == "__main__":
    main()
