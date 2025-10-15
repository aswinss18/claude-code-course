#!/usr/bin/env python3
"""
Simple test script to verify the user API endpoints work correctly.
Run this after the API server is running.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_create_user():
    """Test creating a new user"""
    print("Testing user creation...")
    
    # Test data
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "subscriber": False,
        "ai_personality": "friendly"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/user", json=user_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            print("✅ User created successfully!")
        elif response.status_code == 409:
            print("⚠️  User already exists (expected if running multiple times)")
        else:
            print("❌ Unexpected response")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def test_duplicate_user():
    """Test creating a duplicate user (should fail gracefully)"""
    print("\nTesting duplicate user creation...")
    
    # Same email as existing user
    user_data = {
        "username": "anothertestuser",
        "email": "john@example.com",  # This should already exist
        "password": "anotherpassword123",
        "subscriber": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/user", json=user_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 409:
            print("✅ Duplicate user correctly rejected!")
        else:
            print("❌ Expected 409 Conflict status")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def test_get_users():
    """Test getting all users"""
    print("\nTesting get all users...")
    
    try:
        response = requests.get(f"{BASE_URL}/users")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            users = response.json()["data"]
            print(f"✅ Found {len(users)} users")
            for user in users[:3]:  # Show first 3 users
                print(f"  - {user['username']} ({user['email']})")
        else:
            print("❌ Failed to get users")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def test_get_user_by_email():
    """Test getting a user by email"""
    print("\nTesting get user by email...")
    
    try:
        # Test with existing email
        response = requests.get(f"{BASE_URL}/users/john@example.com")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            user = response.json()["data"]
            print(f"✅ Found user: {user['username']} ({user['email']})")
        elif response.status_code == 404:
            print("⚠️  User not found (might not exist)")
        else:
            print("❌ Unexpected response")
            
        # Test with non-existing email
        response = requests.get(f"{BASE_URL}/users/nonexistent@example.com")
        if response.status_code == 404:
            print("✅ Non-existent user correctly returned 404")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("🚀 Testing User API Endpoints")
    print("=" * 40)
    
    test_create_user()
    test_duplicate_user()
    test_get_users()
    test_get_user_by_email()
    
    print("\n" + "=" * 40)
    print("✅ Testing complete!")