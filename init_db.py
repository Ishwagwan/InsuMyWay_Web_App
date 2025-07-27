from app import app, db, User  # Explicitly import User to ensure model is loaded

with app.app_context():
    db.create_all()
    # Check if the user table exists by querying the metadata
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    if 'user' in tables:
        print("Database tables created successfully, including 'user' table.")
    else:
        print("Error: 'user' table was not created. Check model definitions.")