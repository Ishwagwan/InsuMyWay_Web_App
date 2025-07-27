#!/usr/bin/env python3
"""
MySQL Database Setup Script for InsureMyWay
This script creates the MySQL database and tables for the InsureMyWay application.
"""

import pymysql
import sys
import logging
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database():
    """Create the InsureMyWay database if it doesn't exist"""
    try:
        # Connect to MySQL server (without specifying database)
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=int(Config.MYSQL_PORT),
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"Database '{Config.MYSQL_DATABASE}' created or already exists")
            
            # Grant privileges (optional, for security)
            cursor.execute(f"GRANT ALL PRIVILEGES ON {Config.MYSQL_DATABASE}.* TO '{Config.MYSQL_USER}'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            
        connection.commit()
        connection.close()
        logger.info("Database setup completed successfully")
        return True
        
    except pymysql.Error as e:
        logger.error(f"Error creating database: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def test_connection():
    """Test the database connection"""
    try:
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=int(Config.MYSQL_PORT),
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            logger.info(f"Successfully connected to MySQL version: {version[0]}")
            
        connection.close()
        return True
        
    except pymysql.Error as e:
        logger.error(f"Error connecting to database: {e}")
        return False

def check_xampp_status():
    """Check if XAMPP MySQL is running"""
    try:
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=int(Config.MYSQL_PORT),
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        connection.close()
        logger.info("XAMPP MySQL is running and accessible")
        return True
    except pymysql.Error as e:
        logger.error(f"XAMPP MySQL is not accessible: {e}")
        logger.error("Please make sure XAMPP is running and MySQL service is started")
        return False

if __name__ == '__main__':
    logger.info("Starting MySQL database setup for InsureMyWay...")
    logger.info(f"Configuration:")
    logger.info(f"  Host: {Config.MYSQL_HOST}")
    logger.info(f"  Port: {Config.MYSQL_PORT}")
    logger.info(f"  User: {Config.MYSQL_USER}")
    logger.info(f"  Database: {Config.MYSQL_DATABASE}")
    
    # Check XAMPP status
    if not check_xampp_status():
        logger.error("Please start XAMPP and ensure MySQL service is running")
        sys.exit(1)
    
    # Create database
    if create_database():
        # Test connection
        if test_connection():
            logger.info("✅ MySQL database setup completed successfully!")
            logger.info("You can now run the unified_app.py to create tables and start the application")
        else:
            logger.error("❌ Database connection test failed")
            sys.exit(1)
    else:
        logger.error("❌ Database creation failed")
        sys.exit(1)
