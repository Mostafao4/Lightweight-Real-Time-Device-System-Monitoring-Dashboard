import os
from dotenv import load_dotenv
from flask import Flask
from .models import db

def create_app():
    load_dotenv()
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///instance\monitor.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me")

    # Debug line so you can confirm both web & worker share the same DB
    print("WEB DB_URL =", app.config["SQLALCHEMY_DATABASE_URI"])

    db.init_app(app)
    with app.app_context():
        db.create_all()

    from .routes import bp
    app.register_blueprint(bp)
    return app
