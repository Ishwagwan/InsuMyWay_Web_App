from app import app, db
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.sql import text

# Create an engine to connect to the database
engine = create_engine('sqlite:///insurance.db')
metadata = MetaData()

# Reflect the existing user table
user_table = Table('user', metadata, autoload_with=engine)

# Step 1: Create a new table with the updated schema
with engine.connect() as conn:
    # Create a new temporary table with the updated schema
    conn.execute(text("""
        CREATE TABLE user_temp (
            id INTEGER PRIMARY KEY,
            username VARCHAR(80) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(120) NOT NULL UNIQUE,
            age INTEGER,
            occupation VARCHAR(100),
            lifestyle VARCHAR(50),
            health_status VARCHAR(50)
        )
    """))

    # Step 2: Copy data from the old table to the new table (set a default email for existing users)
    conn.execute(text("""
        INSERT INTO user_temp (id, username, password, age, occupation, lifestyle, health_status, email)
        SELECT id, username, password, age, occupation, lifestyle, health_status, 'unknown@example.com'
        FROM user
    """))

    # Step 3: Drop the old table
    conn.execute(text("DROP TABLE user"))

    # Step 4: Rename the new table to the original name
    conn.execute(text("ALTER TABLE user_temp RENAME TO user"))

    print("Database schema updated successfully: Added 'email' column to 'user' table.")