from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
db = SQLAlchemy()

class Device(db.Model):
    __tablename__ = "devices"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    host = db.Column(db.String(255), nullable=False)
    kind = db.Column(db.String(50), default="generic")
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class CheckResult(db.Model):
    __tablename__ = "check_results"
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # up|down|degraded
    latency_ms = db.Column(db.Integer)
    cpu_percent = db.Column(db.Float)  # (optional for now)
    mem_percent = db.Column(db.Float)
    message = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    device = db.relationship("Device", backref="checks")

def migrate_db_if_needed():
    db.create_all()
