#!/usr/bin/env python3
"""
Database migration script to add new profile fields to existing InsureMyWay database
"""

import pymysql
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connect_to_database():
    """Connect to WAMPP MySQL database"""
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='insuremyway',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        logger.info("Successfully connected to WAMPP MySQL database")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    try:
        cursor.execute(f"""
            SELECT COUNT(*) as count 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'insuremyway' 
            AND TABLE_NAME = '{table_name}' 
            AND COLUMN_NAME = '{column_name}'
        """)
        result = cursor.fetchone()
        return result['count'] > 0
    except Exception as e:
        logger.error(f"Error checking column {column_name}: {e}")
        return False

def add_new_profile_fields(connection):
    """Add new profile fields to the user table"""
    cursor = connection.cursor()
    
    # Define new columns to add
    new_columns = [
        ('savings_level', "VARCHAR(20) DEFAULT NULL COMMENT 'low, moderate, high, substantial'"),
        ('debt_status', "VARCHAR(20) DEFAULT NULL COMMENT 'none, low, moderate, high'"),
        ('exercise_habits', "VARCHAR(20) DEFAULT NULL COMMENT 'never, rarely, regularly, daily'"),
        ('smoking_status', "VARCHAR(20) DEFAULT NULL COMMENT 'never, former, current'"),
        ('chronic_conditions', "VARCHAR(100) DEFAULT NULL COMMENT 'diabetes, hypertension, etc.'"),
        ('business_ownership', "VARCHAR(20) DEFAULT NULL COMMENT 'none, small, medium, large'")
    ]
    
    try:
        for column_name, column_definition in new_columns:
            if not check_column_exists(cursor, 'user', column_name):
                sql = f"ALTER TABLE user ADD COLUMN {column_name} {column_definition}"
                cursor.execute(sql)
                logger.info(f"Added column: {column_name}")
            else:
                logger.info(f"Column {column_name} already exists, skipping")
        
        connection.commit()
        logger.info("Successfully added all new profile fields")
        return True
        
    except Exception as e:
        logger.error(f"Error adding new profile fields: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()

def verify_table_structure(connection):
    """Verify the updated table structure"""
    cursor = connection.cursor()
    try:
        cursor.execute("DESCRIBE user")
        columns = cursor.fetchall()
        
        logger.info("Current user table structure:")
        for column in columns:
            logger.info(f"  {column['Field']} - {column['Type']} - {column['Null']} - {column['Default']}")
        
        return True
    except Exception as e:
        logger.error(f"Error verifying table structure: {e}")
        return False
    finally:
        cursor.close()

def main():
    """Main migration function"""
    logger.info("Starting database migration...")
    
    # Connect to database
    connection = connect_to_database()
    if not connection:
        logger.error("Cannot proceed without database connection")
        return False
    
    try:
        # Add new profile fields
        if add_new_profile_fields(connection):
            logger.info("Migration completed successfully")
            
            # Verify the changes
            verify_table_structure(connection)
            return True
        else:
            logger.error("Migration failed")
            return False
            
    finally:
        connection.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Database migration completed successfully!")
        print("You can now run the unified application with the enhanced profile fields.")
    else:
        print("\n❌ Database migration failed!")
        print("Please check the logs and try again.")
