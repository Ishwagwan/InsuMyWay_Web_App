#!/usr/bin/env python3
"""
Check all database files to see which one has data
"""

import sqlite3
import os
from datetime import datetime

def check_database(db_path):
    """Check a specific database file"""
    print(f"\n🔍 Checking: {db_path}")
    print("-" * 50)
    
    if not os.path.exists(db_path):
        print(f"❌ File does not exist")
        return False
    
    file_size = os.path.getsize(db_path)
    file_mtime = datetime.fromtimestamp(os.path.getmtime(db_path))
    print(f"📁 File size: {file_size} bytes")
    print(f"🕒 Last modified: {file_mtime}")
    
    if file_size == 0:
        print("⚠️  File is empty")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📊 Tables: {len(tables)}")
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} rows")
            
            # Show users if it's the user table
            if table_name == 'user' and count > 0:
                cursor.execute("SELECT id, username, email, is_admin FROM user LIMIT 10")
                users = cursor.fetchall()
                print("    Users:")
                for user in users:
                    print(f"      ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Admin: {user[3]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")
        return False

def main():
    """Check all database files"""
    print("🗄️ Database File Analysis")
    print("=" * 60)
    
    # List of potential database files
    db_files = [
        "insuremyway.db",
        "instance/insuremyway.db",
        "instance/insurance.db",
        "instance/enhanced_insurance.db"
    ]
    
    working_dbs = []
    
    for db_file in db_files:
        if check_database(db_file):
            working_dbs.append(db_file)
    
    print(f"\n📋 Summary")
    print("=" * 30)
    print(f"Working databases: {len(working_dbs)}")
    for db in working_dbs:
        print(f"  ✅ {db}")
    
    if not working_dbs:
        print("❌ No working databases found!")
    
    # Check which database Flask should be using
    print(f"\n🔧 Flask Configuration Check")
    print("-" * 30)
    print("Flask config: sqlite:///insuremyway.db")
    print("This should create: ./insuremyway.db")
    
    if "insuremyway.db" in working_dbs:
        print("✅ Flask database file exists and has data")
    else:
        print("❌ Flask database file missing or empty")
        print("This explains why the database isn't working properly!")

if __name__ == "__main__":
    main()
