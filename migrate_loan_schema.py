#!/usr/bin/env python3
"""
Database migration script to add loan application tables and missing user fields
"""

import pymysql
import sys
import logging
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_to_database():
    """Connect to the MySQL database"""
    try:
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=int(Config.MYSQL_PORT),
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        return connection
    except pymysql.Error as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def add_missing_user_columns(connection):
    """Add missing columns to the user table"""
    missing_columns = [
        "savings_level VARCHAR(20)",
        "debt_status VARCHAR(20)",
        "exercise_habits VARCHAR(20)",
        "smoking_status VARCHAR(20)",
        "chronic_conditions VARCHAR(100)",
        "business_ownership VARCHAR(20)",
        "monthly_income FLOAT"
    ]

    with connection.cursor() as cursor:
        # Check which columns already exist
        cursor.execute("DESCRIBE user")
        existing_columns = [row[0] for row in cursor.fetchall()]

        for column_def in missing_columns:
            column_name = column_def.split()[0]
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE user ADD COLUMN {column_def}")
                    logger.info(f"Added column: {column_name}")
                except pymysql.Error as e:
                    logger.error(f"Error adding column {column_name}: {e}")
            else:
                logger.info(f"Column {column_name} already exists")

def fix_purchase_table(connection):
    """Fix the purchase table to match the model"""
    with connection.cursor() as cursor:
        # Check if purchase table exists and get its structure
        try:
            cursor.execute("DESCRIBE purchase")
            existing_columns = [row[0] for row in cursor.fetchall()]
            logger.info(f"Purchase table columns: {existing_columns}")

            # Add missing columns
            missing_purchase_columns = [
                ("amount", "FLOAT NOT NULL DEFAULT 0"),
                ("status", "VARCHAR(20) DEFAULT 'active'")
            ]

            for column_name, column_def in missing_purchase_columns:
                if column_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE purchase ADD COLUMN {column_name} {column_def}")
                        logger.info(f"Added purchase column: {column_name}")
                    except pymysql.Error as e:
                        logger.error(f"Error adding purchase column {column_name}: {e}")
                else:
                    logger.info(f"Purchase column {column_name} already exists")

        except pymysql.Error as e:
            logger.error(f"Error checking purchase table: {e}")
            # If purchase table doesn't exist, create it
            create_purchase_table_sql = """
            CREATE TABLE IF NOT EXISTS purchase (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                product_id INT NOT NULL,
                purchase_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                amount FLOAT NOT NULL DEFAULT 0,
                status VARCHAR(20) DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            try:
                cursor.execute(create_purchase_table_sql)
                logger.info("Created purchase table")
            except pymysql.Error as e:
                logger.error(f"Error creating purchase table: {e}")

def ensure_product_table(connection):
    """Ensure product table exists with correct structure"""
    with connection.cursor() as cursor:
        try:
            # Check if product table exists and get its structure
            cursor.execute("DESCRIBE product")
            existing_columns = [row[0] for row in cursor.fetchall()]
            logger.info(f"Product table columns: {existing_columns}")

            # Add missing category column if needed
            if 'category' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE product ADD COLUMN category VARCHAR(50) NOT NULL DEFAULT 'general'")
                    logger.info("Added category column to product table")
                except pymysql.Error as e:
                    logger.error(f"Error adding category column: {e}")

            # Add some sample products if table is empty
            cursor.execute("SELECT COUNT(*) FROM product")
            count = cursor.fetchone()[0]

            if count == 0:
                sample_products = [
                    ("Health Insurance Basic", "Basic health coverage for individuals", 25000, "health"),
                    ("Auto Insurance Standard", "Comprehensive auto insurance coverage", 35000, "auto"),
                    ("Life Insurance Premium", "Premium life insurance with full benefits", 45000, "life"),
                    ("Home Insurance Complete", "Complete home and property protection", 55000, "home")
                ]

                insert_sql = "INSERT INTO product (name, description, price, category) VALUES (%s, %s, %s, %s)"
                cursor.executemany(insert_sql, sample_products)
                logger.info(f"Added {len(sample_products)} sample products")

        except pymysql.Error as e:
            logger.error(f"Product table doesn't exist, creating it: {e}")
            # If product table doesn't exist, create it
            create_product_table_sql = """
            CREATE TABLE IF NOT EXISTS product (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT NOT NULL,
                price FLOAT NOT NULL,
                category VARCHAR(50) NOT NULL DEFAULT 'general'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            try:
                cursor.execute(create_product_table_sql)
                logger.info("Created product table")

                # Add sample products
                sample_products = [
                    ("Health Insurance Basic", "Basic health coverage for individuals", 25000, "health"),
                    ("Auto Insurance Standard", "Comprehensive auto insurance coverage", 35000, "auto"),
                    ("Life Insurance Premium", "Premium life insurance with full benefits", 45000, "life"),
                    ("Home Insurance Complete", "Complete home and property protection", 55000, "home")
                ]

                insert_sql = "INSERT INTO product (name, description, price, category) VALUES (%s, %s, %s, %s)"
                cursor.executemany(insert_sql, sample_products)
                logger.info(f"Added {len(sample_products)} sample products")

            except pymysql.Error as e:
                logger.error(f"Error creating product table: {e}")

def fix_notification_table(connection):
    """Fix the notification table to match the model"""
    with connection.cursor() as cursor:
        try:
            cursor.execute("DESCRIBE notification")
            existing_columns = [row[0] for row in cursor.fetchall()]
            logger.info(f"Notification table columns: {existing_columns}")

            # Add missing columns
            missing_notification_columns = [
                ("title", "VARCHAR(100) NOT NULL DEFAULT 'Notification'"),
                ("type", "VARCHAR(20) DEFAULT 'info'"),
                ("is_read", "BOOLEAN DEFAULT FALSE")
            ]

            for column_name, column_def in missing_notification_columns:
                if column_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE notification ADD COLUMN {column_name} {column_def}")
                        logger.info(f"Added notification column: {column_name}")
                    except pymysql.Error as e:
                        logger.error(f"Error adding notification column {column_name}: {e}")
                else:
                    logger.info(f"Notification column {column_name} already exists")

        except pymysql.Error as e:
            logger.error(f"Error checking notification table: {e}")
            # If notification table doesn't exist, create it
            create_notification_table_sql = """
            CREATE TABLE IF NOT EXISTS notification (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(100) NOT NULL DEFAULT 'Notification',
                message TEXT NOT NULL,
                type VARCHAR(20) DEFAULT 'info',
                is_read BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            try:
                cursor.execute(create_notification_table_sql)
                logger.info("Created notification table")
            except pymysql.Error as e:
                logger.error(f"Error creating notification table: {e}")

def create_loan_tables(connection):
    """Create loan application tables"""
    
    # TopUpLoan table
    topup_loan_sql = """
    CREATE TABLE IF NOT EXISTS top_up_loan (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        age INT NOT NULL,
        monthly_income FLOAT NOT NULL,
        loan_amount FLOAT NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        application_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        review_date DATETIME NULL,
        admin_review_notes TEXT,
        loan_history_score VARCHAR(20),
        rejection_reason VARCHAR(100),
        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    # LoanHistory table
    loan_history_sql = """
    CREATE TABLE IF NOT EXISTS loan_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        loan_type VARCHAR(50) NOT NULL,
        loan_amount FLOAT NOT NULL,
        repayment_status VARCHAR(20) NOT NULL,
        loan_date DATETIME NOT NULL,
        completion_date DATETIME NULL,
        repayment_score INT DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    with connection.cursor() as cursor:
        try:
            cursor.execute(topup_loan_sql)
            logger.info("Created/verified top_up_loan table")
            
            cursor.execute(loan_history_sql)
            logger.info("Created/verified loan_history table")
            
        except pymysql.Error as e:
            logger.error(f"Error creating loan tables: {e}")
            raise

def add_sample_loan_history(connection):
    """Add some sample loan history data for testing"""
    sample_data = [
        (1, 'personal', 25000, 'completed', '2023-01-15 10:00:00', '2023-07-15 10:00:00', 95),
        (1, 'topup', 15000, 'completed', '2023-08-01 14:30:00', '2023-12-01 14:30:00', 90),
        (2, 'personal', 30000, 'defaulted', '2023-03-10 09:15:00', None, 20),
        (3, 'topup', 20000, 'completed', '2023-05-20 16:45:00', '2023-11-20 16:45:00', 85),
    ]
    
    with connection.cursor() as cursor:
        # Check if sample data already exists
        cursor.execute("SELECT COUNT(*) FROM loan_history")
        count = cursor.fetchone()[0]
        
        if count == 0:
            insert_sql = """
            INSERT INTO loan_history (user_id, loan_type, loan_amount, repayment_status, 
                                    loan_date, completion_date, repayment_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            try:
                cursor.executemany(insert_sql, sample_data)
                logger.info(f"Added {len(sample_data)} sample loan history records")
            except pymysql.Error as e:
                logger.error(f"Error adding sample data: {e}")
        else:
            logger.info("Sample loan history data already exists")

def main():
    """Main migration function"""
    logger.info("Starting database migration for loan application system...")
    
    connection = connect_to_database()
    if not connection:
        logger.error("Failed to connect to database")
        sys.exit(1)
    
    try:
        # Add missing user columns
        logger.info("Adding missing user table columns...")
        add_missing_user_columns(connection)

        # Ensure product table exists
        logger.info("Ensuring product table exists...")
        ensure_product_table(connection)

        # Fix purchase table
        logger.info("Fixing purchase table structure...")
        fix_purchase_table(connection)

        # Fix notification table
        logger.info("Fixing notification table structure...")
        fix_notification_table(connection)

        # Create loan tables
        logger.info("Creating loan application tables...")
        create_loan_tables(connection)

        # Add sample loan history
        logger.info("Adding sample loan history data...")
        add_sample_loan_history(connection)

        # Commit all changes
        connection.commit()
        logger.info("✅ Database migration completed successfully!")
        
    except Exception as e:
        connection.rollback()
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        connection.close()

if __name__ == '__main__':
    main()
