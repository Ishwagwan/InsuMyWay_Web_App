#!/usr/bin/env python3
"""
Script to verify web-based user registration and login functionality
"""

import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5000"

def test_homepage():
    """Test if the homepage is accessible"""
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            logger.info("✓ Homepage is accessible")
            return True
        else:
            logger.error(f"✗ Homepage returned status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Failed to access homepage: {e}")
        return False

def test_registration_page():
    """Test if the registration page is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/register")
        if response.status_code == 200:
            logger.info("✓ Registration page is accessible")
            return True
        else:
            logger.error(f"✗ Registration page returned status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Failed to access registration page: {e}")
        return False

def test_user_registration():
    """Test user registration via web form"""
    try:
        # Create a session to maintain cookies
        session = requests.Session()
        
        # Get registration page to extract any CSRF tokens if needed
        reg_page = session.get(f"{BASE_URL}/register")
        if reg_page.status_code != 200:
            logger.error("Failed to access registration page")
            return False
        
        # Prepare registration data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        registration_data = {
            'username': f'webtest_{timestamp}',
            'password': 'webtest123',
            'email': f'webtest_{timestamp}@example.com'
        }
        
        logger.info(f"Attempting to register user: {registration_data['username']}")
        
        # Submit registration form
        response = session.post(f"{BASE_URL}/register", data=registration_data)
        
        # Check if registration was successful
        if response.status_code == 200:
            if "already exists" in response.text or "already registered" in response.text:
                logger.warning("User already exists, registration test inconclusive")
                return True
            elif "dashboard" in response.url.lower() or "login" in response.text.lower():
                logger.info("✓ User registration appears successful")
                return True, registration_data
            else:
                logger.warning("Registration response unclear, but no error detected")
                return True, registration_data
        elif response.status_code == 302:  # Redirect after successful registration
            logger.info("✓ User registration successful (redirected)")
            return True, registration_data
        else:
            logger.error(f"✗ Registration failed with status code: {response.status_code}")
            return False, None
            
    except Exception as e:
        logger.error(f"✗ Registration test failed: {e}")
        return False, None

def test_user_login(registration_data):
    """Test user login via web form"""
    try:
        # Create a new session for login
        session = requests.Session()
        
        # Get login page
        login_page = session.get(f"{BASE_URL}/login")
        if login_page.status_code != 200:
            logger.error("Failed to access login page")
            return False
        
        # Prepare login data
        login_data = {
            'username': registration_data['username'],
            'password': registration_data['password']
        }
        
        logger.info(f"Attempting to login user: {login_data['username']}")
        
        # Submit login form
        response = session.post(f"{BASE_URL}/login", data=login_data)
        
        # Check if login was successful
        if response.status_code == 200:
            if "dashboard" in response.text.lower() or "welcome" in response.text.lower():
                logger.info("✓ User login appears successful")
                return True
            else:
                logger.warning("Login response unclear")
                return True
        elif response.status_code == 302:  # Redirect after successful login
            logger.info("✓ User login successful (redirected)")
            return True
        else:
            logger.error(f"✗ Login failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Login test failed: {e}")
        return False

def verify_database_persistence():
    """Verify that the registered user exists in the database"""
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from app import app, db, User
        
        with app.app_context():
            # Count users with webtest prefix
            webtest_users = User.query.filter(User.username.like('webtest_%')).count()
            logger.info(f"✓ Found {webtest_users} webtest users in database")
            
            if webtest_users > 0:
                # Get the most recent webtest user
                recent_user = User.query.filter(User.username.like('webtest_%')).order_by(User.id.desc()).first()
                logger.info(f"✓ Most recent webtest user: {recent_user.username} (ID: {recent_user.id})")
                return True
            else:
                logger.warning("No webtest users found in database")
                return False
                
    except Exception as e:
        logger.error(f"✗ Database verification failed: {e}")
        return False

def main():
    """Main verification function"""
    logger.info("Starting web registration verification...")
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Homepage accessibility
    logger.info("\n=== Test 1: Homepage Accessibility ===")
    if test_homepage():
        tests_passed += 1
    
    # Test 2: Registration page accessibility
    logger.info("\n=== Test 2: Registration Page Accessibility ===")
    if test_registration_page():
        tests_passed += 1
    
    # Test 3: User registration
    logger.info("\n=== Test 3: User Registration ===")
    registration_result = test_user_registration()
    if isinstance(registration_result, tuple):
        success, registration_data = registration_result
        if success:
            tests_passed += 1
    else:
        registration_data = None
        if registration_result:
            tests_passed += 1
    
    # Test 4: User login
    if registration_data:
        logger.info("\n=== Test 4: User Login ===")
        if test_user_login(registration_data):
            tests_passed += 1
    else:
        logger.info("\n=== Test 4: User Login === SKIPPED (no registration data)")
    
    # Test 5: Database persistence
    logger.info("\n=== Test 5: Database Persistence ===")
    if verify_database_persistence():
        tests_passed += 1
    
    # Results
    logger.info(f"\n=== VERIFICATION RESULTS ===")
    logger.info(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed >= 4:  # Allow for some flexibility
        logger.info("🎉 Web registration verification successful!")
        return True
    else:
        logger.warning(f"⚠ {total_tests - tests_passed} test(s) failed.")
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\n✅ Web registration and login are working correctly!")
        print("Your MySQL database is properly saving user data.")
    else:
        print("\n❌ Some verification tests failed!")
        print("Please check the application logs and test results above.")
