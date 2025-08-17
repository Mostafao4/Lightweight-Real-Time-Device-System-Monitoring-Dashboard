#!/usr/bin/env python3
"""Initialize the database and create tables"""

from app import create_app
from app.models import db

def init_database():
    app = create_app()
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")
        print("You can now run the application.")

if __name__ == "__main__":
    init_database() 