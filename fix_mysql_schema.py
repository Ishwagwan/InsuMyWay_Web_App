#!/usr/bin/env python3
"""
Script to fix MySQL database schema to match application models
"""

import pymysql
import logging
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connect_to_mysql():
    """Connect to MySQL database"""
    try:
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=int(Config.MYSQL_PORT),
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        logger.info("Successfully connected to MySQL database")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to MySQL: {e}")
        return None

def fix_user_table_schema(connection):
    """Fix the user table schema to match application models"""
    cursor = connection.cursor()
    
    try:
        # Check if password_hash column exists and password doesn't
        cursor.execute("DESCRIBE user;")
        columns = cursor.fetchall()
        column_names = [col['Field'] for col in columns]
        
        logger.info(f"Current user table columns: {column_names}")
        
        # If password_hash exists but password doesn't, rename it
        if 'password_hash' in column_names and 'password' not in column_names:
            logger.info("Renaming password_hash column to password...")
            cursor.execute("ALTER TABLE user CHANGE COLUMN password_hash password VARCHAR(200) NOT NULL;")
            logger.info("✓ Renamed password_hash to password")
            # Update column_names list after rename
            column_names = [name if name != 'password_hash' else 'password' for name in column_names]

        # Ensure password column has correct length
        elif 'password' in column_names:
            logger.info("Updating password column length...")
            cursor.execute("ALTER TABLE user MODIFY COLUMN password VARCHAR(200) NOT NULL;")
            logger.info("✓ Updated password column length")

        # Add missing columns if they don't exist
        missing_columns = []
        expected_columns = {
            'username': 'VARCHAR(80) UNIQUE NOT NULL',
            'password': 'VARCHAR(200) NOT NULL',
            'email': 'VARCHAR(120) UNIQUE',
            'is_admin': 'BOOLEAN DEFAULT FALSE',
            'age': 'INTEGER',
            'occupation': 'VARCHAR(50)',
            'lifestyle': 'VARCHAR(50)',
            'health_status': 'VARCHAR(50)',
            'marital_status': 'VARCHAR(20)',
            'dependents': 'INTEGER DEFAULT 0',
            'annual_income': 'VARCHAR(20)',
            'education_level': 'VARCHAR(30)',
            'employment_type': 'VARCHAR(30)',
            'residence_type': 'VARCHAR(30)',
            'vehicle_ownership': 'VARCHAR(20)',
            'travel_frequency': 'VARCHAR(20)',
            'risk_tolerance': 'VARCHAR(20)',
            'insurance_experience': 'VARCHAR(20)',
            'coverage_priority': 'VARCHAR(30)',
            'family_medical_history': 'VARCHAR(20)',
            'hobbies_activities': 'VARCHAR(100)',
            'location': 'VARCHAR(50)'
        }

        for col_name, col_def in expected_columns.items():
            if col_name not in column_names:
                missing_columns.append((col_name, col_def))
        
        # Add missing columns
        for col_name, col_def in missing_columns:
            logger.info(f"Adding missing column: {col_name}")
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_def};")
            logger.info(f"✓ Added column {col_name}")
        
        connection.commit()
        logger.info("✓ User table schema updated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing user table schema: {e}")
        connection.rollback()
        return False

def verify_other_tables(connection):
    """Verify other tables exist and have correct structure"""
    cursor = connection.cursor()
    
    try:
        # Check if all required tables exist
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        table_names = [list(table.values())[0] for table in tables]
        
        required_tables = ['user', 'policy', 'recommendation', 'notification']
        missing_tables = [table for table in required_tables if table not in table_names]
        
        if missing_tables:
            logger.warning(f"Missing tables: {missing_tables}")
            logger.info("These tables will be created when the application runs with db.create_all()")
        else:
            logger.info("✓ All required tables exist")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verifying tables: {e}")
        return False

def test_schema_compatibility():
    """Test if the schema is compatible with the application models"""
    try:
        # Import Flask app and models to test compatibility
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from app import app, db, User
        
        with app.app_context():
            # Try to query the User model
            user_count = User.query.count()
            logger.info(f"✓ Schema compatibility test passed. Found {user_count} users.")
            
            # Try to create a test user (but don't commit)
            test_user = User(username='test_schema', password='test', email='test@schema.com')
            db.session.add(test_user)
            db.session.rollback()  # Don't actually save
            logger.info("✓ User model creation test passed")
            
        return True
        
    except Exception as e:
        logger.error(f"Schema compatibility test failed: {e}")
        return False

def main():
    """Main function to fix MySQL schema"""
    logger.info("Starting MySQL schema fix...")
    
    connection = connect_to_mysql()
    if not connection:
        logger.error("Cannot proceed without database connection")
        return False
    
    try:
        # Fix user table schema
        if not fix_user_table_schema(connection):
            logger.error("Failed to fix user table schema")
            return False
        
        # Verify other tables
        if not verify_other_tables(connection):
            logger.error("Failed to verify other tables")
            return False
        
        logger.info("✓ MySQL schema fix completed successfully")
        
        # Test schema compatibility
        logger.info("Testing schema compatibility with application models...")
        if test_schema_compatibility():
            logger.info("✓ Schema is compatible with application models")
        else:
            logger.warning("⚠ Schema compatibility test failed - may need additional fixes")
        
        return True
        
    finally:
        connection.close()
        logger.info("Database connection closed")

if __name__ == '__main__':
    success = main()
    if success:
        print("\n🎉 MySQL schema fix completed successfully!")
        print("You can now run your application with MySQL database.")
    else:
        print("\n❌ MySQL schema fix failed!")
        print("Please check the logs above for details.")
