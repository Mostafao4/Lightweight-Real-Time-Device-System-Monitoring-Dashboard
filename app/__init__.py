from flask import Flask
from .models import db, migrate_db_if_needed

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///monitor.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "change-me"
    db.init_app(app)
    with app.app_context():
        migrate_db_if_needed()
    from .routes import bp
    app.register_blueprint(bp)
    return app
