#!/usr/bin/env python3
"""
Script to add Author and Contributor roles to creators_roles table
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import CreatorsRoles

def add_creator_roles():
    """Add Author and Contributor roles if they don't exist"""
    app = create_app()

    with app.app_context():
        # Check if Author role exists
        author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
        if not author_role:
            author_role = CreatorsRoles(role_id='8', role_name='Author')
            db.session.add(author_role)
            print("✓ Added 'Author' role")
        else:
            print("✓ 'Author' role already exists")

        # Check if Contributor role exists
        contributor_role = CreatorsRoles.query.filter_by(role_name='Contributor').first()
        if not contributor_role:
            contributor_role = CreatorsRoles(role_id='9', role_name='Contributor')
            db.session.add(contributor_role)
            print("✓ Added 'Contributor' role")
        else:
            print("✓ 'Contributor' role already exists")

        db.session.commit()
        print("\n✓ Creator roles setup completed!")

if __name__ == '__main__':
    add_creator_roles()
