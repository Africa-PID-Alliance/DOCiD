#!/usr/bin/env python3
"""
Interactive script to manage users in the database
Usage: python manage_users.py
"""

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tabulate import tabulate

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import UserAccount
from config import Config

class UserManager:
    def __init__(self):
        self.engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def list_users(self):
        """List all users in the database"""
        users = self.session.query(UserAccount).all()
        if not users:
            print("No users found in the database.")
            return
        
        # Prepare data for tabulate
        headers = ["ID", "Email", "Username", "Full Name", "Type", "Role", "Date Joined"]
        data = []
        for user in users:
            data.append([
                user.user_id,
                user.email,
                user.user_name,
                user.full_name,
                user.type,
                user.role or "user",
                user.date_joined.strftime("%Y-%m-%d %H:%M") if user.date_joined else "N/A"
            ])
        
        print("\n" + tabulate(data, headers=headers, tablefmt="grid"))
        print(f"\nTotal users: {len(users)}")
    
    def add_user(self):
        """Add a new user interactively"""
        print("\n=== Add New User ===")
        
        # Get user input
        email = input("Email: ").strip()
        if not email:
            print("Email is required!")
            return
        
        # Check if user exists
        existing_user = self.session.query(UserAccount).filter_by(email=email).first()
        if existing_user:
            print(f"User with email {email} already exists!")
            return
        
        password = input("Password: ").strip()
        if not password:
            print("Password is required!")
            return
        
        user_name = input("Username: ").strip()
        if not user_name:
            user_name = email.split('@')[0]
        
        full_name = input("Full Name: ").strip()
        if not full_name:
            full_name = user_name.title()
        
        affiliation = input("Affiliation/Organization (optional): ").strip()
        country = input("Country (optional): ").strip()
        city = input("City (optional): ").strip()
        
        role = input("Role (admin/user) [default: user]: ").strip().lower()
        if role not in ['admin', 'user']:
            role = 'user'
        
        # Create user
        try:
            new_user = UserAccount(
                email=email,
                password=generate_password_hash(password),
                user_name=user_name,
                full_name=full_name,
                type="email",
                affiliation=affiliation or None,
                role=role,
                first_time=1,
                country=country or None,
                city=city or None,
                timestamp=datetime.utcnow(),
                date_joined=datetime.utcnow()
            )
            
            self.session.add(new_user)
            self.session.commit()
            
            print(f"\n✓ User created successfully!")
            print(f"  User ID: {new_user.user_id}")
            print(f"  Email: {new_user.email}")
            print(f"  Username: {new_user.user_name}")
            
        except Exception as e:
            self.session.rollback()
            print(f"\n✗ Error creating user: {str(e)}")
    
    def update_password(self):
        """Update a user's password"""
        print("\n=== Update User Password ===")
        
        email = input("Email of user to update: ").strip()
        if not email:
            print("Email is required!")
            return
        
        user = self.session.query(UserAccount).filter_by(email=email).first()
        if not user:
            print(f"User with email {email} not found!")
            return
        
        new_password = input("New password: ").strip()
        if not new_password:
            print("Password is required!")
            return
        
        try:
            user.password = generate_password_hash(new_password)
            self.session.commit()
            print(f"\n✓ Password updated successfully for {email}")
        except Exception as e:
            self.session.rollback()
            print(f"\n✗ Error updating password: {str(e)}")
    
    def delete_user(self):
        """Delete a user"""
        print("\n=== Delete User ===")
        
        email = input("Email of user to delete: ").strip()
        if not email:
            print("Email is required!")
            return
        
        user = self.session.query(UserAccount).filter_by(email=email).first()
        if not user:
            print(f"User with email {email} not found!")
            return
        
        confirm = input(f"Are you sure you want to delete {email}? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Deletion cancelled.")
            return
        
        try:
            self.session.delete(user)
            self.session.commit()
            print(f"\n✓ User {email} deleted successfully")
        except Exception as e:
            self.session.rollback()
            print(f"\n✗ Error deleting user: {str(e)}")
    
    def quick_add_test_user(self):
        """Quickly add the test user ekariz@gmail.com"""
        email = "ekariz@gmail.com"
        password = "123456"
        
        # Check if user exists
        existing_user = self.session.query(UserAccount).filter_by(email=email).first()
        if existing_user:
            print(f"\nUser {email} already exists!")
            update = input("Update password to '123456'? (y/n): ").strip().lower()
            if update == 'y':
                try:
                    existing_user.password = generate_password_hash(password)
                    self.session.commit()
                    print("✓ Password updated successfully!")
                except Exception as e:
                    self.session.rollback()
                    print(f"✗ Error updating password: {str(e)}")
            return
        
        # Create user
        try:
            new_user = UserAccount(
                email=email,
                password=generate_password_hash(password),
                user_name="ekariz",
                full_name="E. Kariz",
                type="email",
                affiliation="Test Organization",
                role="user",
                first_time=1,
                country="Kenya",
                city="Nairobi",
                timestamp=datetime.utcnow(),
                date_joined=datetime.utcnow()
            )
            
            self.session.add(new_user)
            self.session.commit()
            
            print(f"\n✓ Test user created successfully!")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            print(f"  User ID: {new_user.user_id}")
            
        except Exception as e:
            self.session.rollback()
            print(f"\n✗ Error creating user: {str(e)}")
    
    def close(self):
        """Close database session"""
        self.session.close()

def main():
    manager = UserManager()
    
    while True:
        print("\n=== User Management System ===")
        print("1. List all users")
        print("2. Add new user")
        print("3. Quick add test user (ekariz@gmail.com)")
        print("4. Update user password")
        print("5. Delete user")
        print("0. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            manager.list_users()
        elif choice == '2':
            manager.add_user()
        elif choice == '3':
            manager.quick_add_test_user()
        elif choice == '4':
            manager.update_password()
        elif choice == '5':
            manager.delete_user()
        elif choice == '0':
            print("Exiting...")
            break
        else:
            print("Invalid option. Please try again.")
    
    manager.close()

if __name__ == "__main__":
    # Check if tabulate is installed
    try:
        import tabulate
    except ImportError:
        print("Installing required package: tabulate")
        os.system("pip install tabulate")
        print("Please run the script again.")
        sys.exit(1)
    
    main()