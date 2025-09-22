#!/usr/bin/env python3
"""
Script to add a user to the database
Usage: python add_user.py
"""

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import UserAccount
from config import Config

def add_user():
    """Add a user to the database"""
    
    # Database connection
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # User details
        email = "ekariz@gmail.com"
        password = "123456"
        
        # Check if user already exists
        existing_user = session.query(UserAccount).filter_by(email=email).first()
        if existing_user:
            print(f"User with email {email} already exists!")
            print(f"User ID: {existing_user.user_id}")
            print(f"Username: {existing_user.user_name}")
            
            # Ask if they want to update the password
            update = input("Do you want to update the password? (y/n): ")
            if update.lower() == 'y':
                existing_user.password = generate_password_hash(password)
                session.commit()
                print("Password updated successfully!")
            return
        
        # Create new user
        new_user = UserAccount(
            email=email,
            password=generate_password_hash(password),  # Hash the password
            user_name="ekariz",
            full_name="E. Kariz",
            type="email",  # Login type: email
            affiliation="",
            role="user",
            first_time=1,
            country="Kenya",
            city="Nairobi",
            timestamp=datetime.utcnow(),
            date_joined=datetime.utcnow()
        )
        
        # Add and commit
        session.add(new_user)
        session.commit()
        
        print(f"User created successfully!")
        print(f"Email: {email}")
        print(f"User ID: {new_user.user_id}")
        print(f"Username: {new_user.user_name}")
        print(f"Password: {password} (stored as hash)")
        
    except Exception as e:
        session.rollback()
        print(f"Error adding user: {str(e)}")
        
    finally:
        session.close()

if __name__ == "__main__":
    add_user()