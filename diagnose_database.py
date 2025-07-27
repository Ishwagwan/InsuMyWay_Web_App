#!/usr/bin/env python3
"""
Database diagnosis script to identify and fix database issues
"""

import os
import sqlite3
import pymysql
import logging
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_sqlite_databases():
    """Check SQLite databases in the project"""
    logger.info("=== CHECKING SQLITE DATABASES ===")
    
    sqlite_files = [
        'insurance.db',
        'instance/insurance.db',
        'instance/enhanced_insurance.db',
        'instance/insuremyway.db'
    ]
    
    for db_file in sqlite_files:
        if os.path.exists(db_file):
            logger.info(f"Found SQLite database: {db_file}")
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Get table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                logger.info(f"  Tables in {db_file}: {[table[0] for table in tables]}")
                
                # Check user table if it exists
                if any('user' in table[0] for table in tables):
                    cursor.execute("SELECT COUNT(*) FROM user;")
                    user_count = cursor.fetchone()[0]
                    logger.info(f"  User records in {db_file}: {user_count}")
                    
                    # Show sample user data
                    cursor.execute("SELECT id, username, email, is_admin FROM user LIMIT 3;")
                    users = cursor.fetchall()
                    for user in users:
                        logger.info(f"    User: ID={user[0]}, Username={user[1]}, Email={user[2]}, Admin={user[3]}")
                
                conn.close()
            except Exception as e:
                logger.error(f"  Error reading {db_file}: {e}")
        else:
            logger.info(f"SQLite database not found: {db_file}")

def check_mysql_database():
    """Check MySQL database"""
    logger.info("=== CHECKING MYSQL DATABASE ===")
    
    try:
        # Try to connect to MySQL
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=int(Config.MYSQL_PORT),
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        logger.info(f"Successfully connected to MySQL database: {Config.MYSQL_DATABASE}")
        
        with connection.cursor() as cursor:
            # Show tables
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            table_names = [list(table.values())[0] for table in tables]
            logger.info(f"Tables in MySQL: {table_names}")
            
            # Check user table if it exists
            if 'user' in table_names:
                cursor.execute("SELECT COUNT(*) as count FROM user;")
                result = cursor.fetchone()
                user_count = result['count']
                logger.info(f"User records in MySQL: {user_count}")
                
                # Show table structure
                cursor.execute("DESCRIBE user;")
                columns = cursor.fetchall()
                logger.info("User table structure in MySQL:")
                for col in columns:
                    logger.info(f"  {col['Field']}: {col['Type']} {'NULL' if col['Null'] == 'YES' else 'NOT NULL'}")
                
                # Show sample data
                cursor.execute("SELECT id, username, email FROM user LIMIT 3;")
                users = cursor.fetchall()
                for user in users:
                    logger.info(f"  User: ID={user['id']}, Username={user['username']}, Email={user['email']}")
            else:
                logger.warning("No 'user' table found in MySQL database")
        
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"Error connecting to MySQL: {e}")
        return False

def check_current_app_config():
    """Check which database configuration is being used"""
    logger.info("=== CHECKING APPLICATION CONFIGURATION ===")
    
    # Check app.py configuration
    try:
        with open('app.py', 'r') as f:
            content = f.read()
            if 'sqlite:///insurance.db' in content:
                logger.info("app.py is configured to use SQLite: sqlite:///insurance.db")
            elif 'mysql' in content.lower():
                logger.info("app.py appears to be configured for MySQL")
            else:
                logger.info("app.py database configuration unclear")
    except Exception as e:
        logger.error(f"Error reading app.py: {e}")
    
    # Check unified_app.py configuration
    try:
        with open('unified_app.py', 'r') as f:
            content = f.read()
            if 'config[config_name]' in content:
                logger.info("unified_app.py uses config system (defaults to SQLite in development)")
    except Exception as e:
        logger.error(f"Error reading unified_app.py: {e}")
    
    # Check config.py
    logger.info(f"Config.py MySQL settings:")
    logger.info(f"  Host: {Config.MYSQL_HOST}")
    logger.info(f"  Port: {Config.MYSQL_PORT}")
    logger.info(f"  User: {Config.MYSQL_USER}")
    logger.info(f"  Database: {Config.MYSQL_DATABASE}")
    logger.info(f"  MySQL URI: {Config.SQLALCHEMY_DATABASE_URI}")

def main():
    """Main diagnosis function"""
    logger.info("Starting database diagnosis...")
    
    check_current_app_config()
    check_sqlite_databases()
    mysql_available = check_mysql_database()
    
    logger.info("=== DIAGNOSIS SUMMARY ===")
    logger.info("Issues identified:")
    logger.info("1. Multiple database configurations exist (SQLite and MySQL)")
    logger.info("2. Application may be using SQLite while expecting MySQL")
    logger.info("3. Schema mismatch between application models and database tables")
    
    if mysql_available:
        logger.info("✓ MySQL database is accessible")
    else:
        logger.info("✗ MySQL database is not accessible")
    
    logger.info("\nRecommended fixes:")
    logger.info("1. Standardize on one database system (MySQL recommended for production)")
    logger.info("2. Update application configuration to use the correct database")
    logger.info("3. Migrate/sync database schema with application models")

if __name__ == '__main__':
    main()
