from app import app, db
from sqlalchemy import create_engine
from sqlalchemy.sql import text

engine = create_engine('sqlite:///insurance.db')
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE user ADD COLUMN email VARCHAR(120)"))
    print("Added 'email' column to 'user' table (nullable).")