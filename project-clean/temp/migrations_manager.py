#!/usr/bin/env python3
"""
Flask-Migrate management script for DOCiD application
"""

import os
from flask import Flask
from flask_migrate import Migrate, init as migrate_init, migrate as create_migration, upgrade, downgrade, revision
from app import create_app, db

# Import all models to ensure they're registered with SQLAlchemy
from app.models import (
    UserAccount, Publications, PublicationFiles, PublicationDocuments,
    PublicationCreators, PublicationOrganization, PublicationFunders,
    PublicationProjects, ResourceTypes, FunderTypes, CreatorsRoles,
    creatorsIdentifiers, PublicationIdentifierTypes, PublicationTypes,
    DocIdLookup, CrossrefMetadata
)

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        print("DOCiD Flask-Migrate Management")
        print("==============================")
        print("Available commands:")
        print("1. Initialize migrations")
        print("2. Create migration")
        print("3. Upgrade database")
        print("4. Downgrade database")
        print("5. Show current revision")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            # Initialize migrations
            print("Initializing migrations...")
            try:
                migrate_init()
                print("✅ Migrations initialized successfully!")
                print("A 'migrations' folder has been created.")
            except Exception as e:
                print(f"❌ Error initializing migrations: {e}")
                
        elif choice == "2":
            # Create a new migration
            message = input("Enter migration message: ").strip()
            if not message:
                message = "Auto-generated migration"
            
            print(f"Creating migration: {message}")
            try:
                create_migration(message=message)
                print("✅ Migration created successfully!")
            except Exception as e:
                print(f"❌ Error creating migration: {e}")
                
        elif choice == "3":
            # Upgrade database
            print("Upgrading database...")
            try:
                upgrade()
                print("✅ Database upgraded successfully!")
            except Exception as e:
                print(f"❌ Error upgrading database: {e}")
                
        elif choice == "4":
            # Downgrade database
            revision = input("Enter revision to downgrade to (or press Enter for previous): ").strip()
            if not revision:
                revision = None
                
            print("Downgrading database...")
            try:
                downgrade(revision)
                print("✅ Database downgraded successfully!")
            except Exception as e:
                print(f"❌ Error downgrading database: {e}")
                
        elif choice == "5":
            # Show current revision
            from flask_migrate import current
            try:
                rev = current()
                print(f"Current revision: {rev}")
            except Exception as e:
                print(f"❌ Error getting current revision: {e}")
                
        else:
            print("Invalid choice. Please run the script again.")
