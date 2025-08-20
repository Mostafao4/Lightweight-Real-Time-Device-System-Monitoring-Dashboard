from flask import (
    Blueprint, render_template, request, redirect,
    url_for, jsonify, session, flash
)
from app import db
from app.models import Device, CheckResult
from sqlalchemy import desc
from functools import wraps
import os

bp = Blueprint("routes", __name__)

# Load admin creds from environment
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "password")


# ------------------------------
# Helper: login required decorator
# ------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("You must log in first", "danger")
            return redirect(url_for("routes.login"))
        return f(*args, **kwargs)
    return decorated_function


# ------------------------------
# Login + Logout
# ------------------------------
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        pw = request.form.get("password")
        if user == ADMIN_USER and pw == ADMIN_PASS:
            session["logged_in"] = True
            flash("Welcome back!", "success")
            return redirect(url_for("routes.index"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("Logged out", "info")
    return redirect(url_for("routes.login"))


# ------------------------------
# Dashboard
# ------------------------------
@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if not session.get("logged_in"):
            flash("Login required to add devices", "danger")
            return redirect(url_for("routes.login"))

        name = request.form.get("name")
        host = request.form.get("host")
        kind = request.form.get("kind", "generic")

        if name and host:
            device = Device(name=name, host=host, kind=kind)
            db.session.add(device)
            db.session.commit()
        return redirect(url_for("routes.index"))

    devices = Device.query.order_by(Device.id.asc()).all()
    latest = {}
    for d in devices:
        cr = (
            CheckResult.query.filter_by(device_id=d.id)
            .order_by(desc(CheckResult.created_at))
            .first()
        )
        latest[d.id] = cr

    return render_template("index.html", devices=devices, latest=latest)


# ------------------------------
# Delete device
# ------------------------------
@bp.post("/devices/<int:device_id>/delete")
@login_required
def delete_device(device_id):
    device = Device.query.get_or_404(device_id)

    # Clean up related results first
    CheckResult.query.filter_by(device_id=device.id).delete()

    db.session.delete(device)
    db.session.commit()
    flash("Device deleted", "success")
    return redirect(url_for("routes.index"))


# ------------------------------
# JSON API (open, read-only)
# ------------------------------
@bp.get("/api/devices")
def api_devices():
    devices = Device.query.order_by(Device.id.asc()).all()
    out = []
    for d in devices:
        cr = (
            CheckResult.query.filter_by(device_id=d.id)
            .order_by(desc(CheckResult.created_at))
            .first()
        )
        out.append(
            {
                "id": d.id,
                "name": d.name,
                "host": d.host,
                "kind": d.kind,
                "status": cr.status if cr else "Unknown",
                "latency_ms": cr.latency_ms if cr and cr.latency_ms is not None else None,
                "last_check": cr.created_at.strftime("%Y-%m-%d %H:%M:%S") if cr else None,
            }
        )
    return jsonify(out)
