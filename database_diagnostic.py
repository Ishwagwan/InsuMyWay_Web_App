#!/usr/bin/env python3
"""
Comprehensive database diagnostic script to check database functionality
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_database_file():
    """Check if database file exists and its properties"""
    print("🔍 Checking Database File")
    print("=" * 40)
    
    db_path = "insuremyway.db"
    
    if os.path.exists(db_path):
        file_size = os.path.getsize(db_path)
        file_mtime = datetime.fromtimestamp(os.path.getmtime(db_path))
        print(f"✅ Database file exists: {db_path}")
        print(f"📁 File size: {file_size} bytes")
        print(f"🕒 Last modified: {file_mtime}")
        return True
    else:
        print(f"❌ Database file not found: {db_path}")
        return False

def check_database_tables():
    """Check database tables and their contents"""
    print("\n🗄️ Checking Database Tables")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect("insuremyway.db")
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📊 Found {len(tables)} tables:")
        for table in tables:
            table_name = table[0]
            print(f"  - {table_name}")
            
            # Get row count for each table
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"    Rows: {count}")
            
            # Show table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"    Columns: {[col[1] for col in columns]}")
            
            # Show sample data for user table
            if table_name == 'user' and count > 0:
                cursor.execute(f"SELECT id, username, email, is_admin FROM {table_name} LIMIT 5")
                users = cursor.fetchall()
                print(f"    Sample users:")
                for user in users:
                    print(f"      ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Admin: {user[3]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

def test_database_operations():
    """Test basic database operations"""
    print("\n🧪 Testing Database Operations")
    print("=" * 40)
    
    try:
        # Import Flask app components
        from app import app, db, User, bcrypt
        
        with app.app_context():
            print("✅ Flask app context created")
            
            # Test database connection
            try:
                db.engine.execute("SELECT 1")
                print("✅ Database connection working")
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return False
            
            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✅ Tables accessible via SQLAlchemy: {tables}")
            
            # Test user query
            try:
                user_count = User.query.count()
                print(f"✅ User query working - Found {user_count} users")
                
                # List all users
                users = User.query.all()
                print("📋 Current users in database:")
                for user in users:
                    print(f"  - ID: {user.id}, Username: {user.username}, Email: {user.email}, Admin: {user.is_admin}")
                
            except Exception as e:
                print(f"❌ User query failed: {e}")
                return False
            
            # Test user creation
            try:
                test_username = f"diagnostic_test_{int(datetime.now().timestamp())}"
                test_user = User(
                    username=test_username,
                    password=bcrypt.generate_password_hash("testpass").decode('utf-8'),
                    email=f"{test_username}@test.com"
                )
                
                db.session.add(test_user)
                db.session.commit()
                print(f"✅ Test user created: {test_username}")
                
                # Verify user was created
                created_user = User.query.filter_by(username=test_username).first()
                if created_user:
                    print(f"✅ Test user verified in database: ID {created_user.id}")
                    
                    # Clean up test user
                    db.session.delete(created_user)
                    db.session.commit()
                    print("✅ Test user cleaned up")
                else:
                    print("❌ Test user not found after creation")
                    return False
                
            except Exception as e:
                print(f"❌ User creation test failed: {e}")
                db.session.rollback()
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def test_registration_endpoint():
    """Test the registration endpoint functionality"""
    print("\n🌐 Testing Registration Endpoint")
    print("=" * 40)
    
    try:
        import urllib.request
        import urllib.parse
        
        base_url = "http://127.0.0.1:5000"
        
        # Test registration page access
        try:
            register_req = urllib.request.Request(f"{base_url}/register")
            register_response = urllib.request.urlopen(register_req)
            if register_response.getcode() == 200:
                print("✅ Registration page accessible")
            else:
                print(f"❌ Registration page failed: {register_response.getcode()}")
                return False
        except Exception as e:
            print(f"❌ Cannot access registration page: {e}")
            print("Make sure Flask app is running on http://127.0.0.1:5000")
            return False
        
        # Test user registration
        test_username = f"endpoint_test_{int(datetime.now().timestamp())}"
        registration_data = urllib.parse.urlencode({
            'username': test_username,
            'password': 'testpass123',
            'email': f'{test_username}@test.com'
        }).encode('utf-8')
        
        register_req = urllib.request.Request(f"{base_url}/register", data=registration_data)
        register_response = urllib.request.urlopen(register_req)
        
        if register_response.getcode() in [200, 302]:
            print(f"✅ Registration endpoint working - User {test_username} registered")
            
            # Test login with registered user
            login_data = urllib.parse.urlencode({
                'username': test_username,
                'password': 'testpass123'
            }).encode('utf-8')
            
            login_req = urllib.request.Request(f"{base_url}/login", data=login_data)
            login_response = urllib.request.urlopen(login_req)
            
            if login_response.getcode() in [200, 302]:
                print(f"✅ Login working - User {test_username} can login")
                return True
            else:
                print(f"❌ Login failed for registered user: {login_response.getcode()}")
                return False
        else:
            print(f"❌ Registration failed: {register_response.getcode()}")
            return False
            
    except Exception as e:
        print(f"❌ Registration endpoint test failed: {e}")
        return False

def main():
    """Run all diagnostic tests"""
    print("🏥 Database Diagnostic Tool")
    print("=" * 50)
    
    all_passed = True
    
    # Test 1: Check database file
    if not check_database_file():
        all_passed = False
    
    # Test 2: Check database tables
    if not check_database_tables():
        all_passed = False
    
    # Test 3: Test database operations
    if not test_database_operations():
        all_passed = False
    
    # Test 4: Test registration endpoint
    if not test_registration_endpoint():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All database diagnostic tests passed!")
        print("The database appears to be working correctly.")
    else:
        print("❌ Some database diagnostic tests failed!")
        print("There are issues with the database functionality.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
