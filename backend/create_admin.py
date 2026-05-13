#!/usr/bin/env python3
"""
Simple script to create admin user for the attendance system
"""

import os
import sys
from flask import Flask
from werkzeug.security import generate_password_hash
from datetime import datetime
from dotenv import load_dotenv
from flask_pymongo import PyMongo

# Load environment variables
load_dotenv()

# Create Flask app (only to configure PyMongo)
app = Flask(__name__)

# Initialize Mongo (required)
mongo = None
mongo_uri = os.getenv('MONGODB_URI') or os.getenv('MONGO_URI')
if mongo_uri:
    app.config['MONGO_URI'] = mongo_uri
    try:
        mongo = PyMongo(app)
    except Exception:
        mongo = None

def _hash_password(password):
    return generate_password_hash(password)

def create_admin_user():
    """Create admin user"""
    try:
        if not mongo:
            print('MongoDB not configured. Set MONGODB_URI and retry.')
            return False

        users = mongo.db.users
        existing = users.find_one({'username': 'admin'})
        if existing:
            print("Admin user already exists in MongoDB")
            print(f"Username: {existing.get('username')}")
            print(f"Email: {existing.get('email')}")
            print(f"Role: {existing.get('role')}")
            return True

        admin_doc = {
            'username': 'admin',
            'email': 'admin@school.edu',
            'full_name': 'System Administrator',
            'role': 'admin',
            'is_active': True,
            'password_hash': _hash_password('admin123'),
            'created_at': datetime.utcnow().isoformat(),
        }
        users.insert_one(admin_doc)
        print("OK Admin user created in MongoDB!")
        print("Username: admin")
        print("Password: admin123")
        print("Email: admin@school.edu")
        print("Role: admin")
        return True
    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        return False

if __name__ == '__main__':
    print("Creating admin user for Attendance System...")
    success = create_admin_user()
    if success:
        print("\n🎉 Admin user setup completed!")
        print("\nYou can now login with:")
        print("Username: admin")
        print("Password: admin123")
    else:
        print("\n❌ Failed to create admin user")
        sys.exit(1)