#!/usr/bin/env python3
"""
Script to create an admin user for Pod GPT
Usage: python create_admin.py
"""

import os
import sys
from werkzeug.security import generate_password_hash
from models import db, User

# Import the Flask app to get the database context
from app import app

def create_admin_user():
    """Create an admin user interactively"""
    print("Creating Admin User for Pod GPT")
    print("=" * 40)
    
    # Get admin details
    name = input("Enter admin name: ").strip()
    if not name:
        print("Name cannot be empty!")
        return False
        
    email = input("Enter admin email: ").strip()
    if not email:
        print("Email cannot be empty!")
        return False
        
    password = input("Enter admin password: ").strip()
    if not password:
        print("Password cannot be empty!")
        return False
    
    # Create admin user within app context
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"User with email {email} already exists!")
            make_admin = input("Make this user an admin? (y/n): ").strip().lower()
            if make_admin == 'y':
                existing_user.is_admin = True
                existing_user.is_approved = True
                db.session.commit()
                print(f"User {existing_user.name} ({existing_user.email}) is now an admin!")
                return True
            return False
        
        # Create new admin user
        admin_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            is_approved=True,  # Admin is auto-approved
            is_admin=True
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        print(f"Admin user created successfully!")
        print(f"Name: {name}")
        print(f"Email: {email}")
        print("You can now login to the admin panel.")
        
        return True

if __name__ == "__main__":
    if create_admin_user():
        print("\nAdmin user creation completed!")
    else:
        print("\nAdmin user creation failed!")
        sys.exit(1) 