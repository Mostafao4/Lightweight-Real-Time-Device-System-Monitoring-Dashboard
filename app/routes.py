from flask import (
    Response, Blueprint, render_template, request, redirect,
    url_for, jsonify, session, flash, abort, request as flask_request
)
from app import db
from app.models import Device, CheckResult
from sqlalchemy import desc, asc
from functools import wraps
import os
import re
from datetime import datetime, timezone
import csv
import io
from app.config_store import get_config, set_config

bp = Blueprint("routes", __name__)

# ---- Auth config from environment
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "password")




# ================================
# NEW: History helpers + endpoints
# ================================

# helper to parse ?from= & ?to= (YYYY-MM-DD or full ISO)
def _parse_dt(s):
    if not s:
        return None
    try:
        # accepts '2025-08-24' or '2025-08-24 15:20:00'
        return datetime.fromisoformat(s)
    except ValueError:
        return None

@bp.get("/devices/<int:device_id>")
def device_detail(device_id):
    device = Device.query.get_or_404(device_id)

    # filters
    q_from = _parse_dt(request.args.get("from"))
    q_to   = _parse_dt(request.args.get("to"))
    limit  = int(request.args.get("limit", "200"))  # cap on points shown
    limit  = max(10, min(limit, 2000))

    q = CheckResult.query.filter_by(device_id=device.id)
    if q_from:
        q = q.filter(CheckResult.created_at >= q_from)
    if q_to:
        q = q.filter(CheckResult.created_at <= q_to)

    results = (
        q.order_by(desc(CheckResult.created_at))
         .limit(limit)
         .all()
    )
    # for charts it’s nice to have chronological order
    results_chrono = list(reversed(results))

    return render_template(
        "device_detail.html",
        device=device,
        results=results,               # newest → oldest (for table)
        results_chrono=results_chrono  # oldest → newest (for chart)
    )

@bp.get("/api/devices/<int:device_id>/history")
def api_device_history(device_id):
    device = Device.query.get_or_404(device_id)
    q_from = _parse_dt(request.args.get("from"))
    q_to   = _parse_dt(request.args.get("to"))
    limit  = int(request.args.get("limit", "500"))
    limit  = max(10, min(limit, 5000))

    q = CheckResult.query.filter_by(device_id=device.id)
    if q_from:
        q = q.filter(CheckResult.created_at >= q_from)
    if q_to:
        q = q.filter(CheckResult.created_at <= q_to)

    rows = (
        q.order_by(asc(CheckResult.created_at))
         .limit(limit)
         .all()
    )
    def to_dict(r):
        return {
            "id": r.id,
            "status": r.status,
            "latency_ms": r.latency_ms,
            "message": r.message,
            "created_at": r.created_at.isoformat(sep=" ", timespec="seconds"),
        }
    return jsonify({
        "device": {"id": device.id, "name": device.name, "host": device.host, "kind": device.kind},
        "count": len(rows),
        "items": [to_dict(r) for r in rows]
    })

@bp.get("/devices/<int:device_id>/history.csv")
def device_history_csv(device_id):
    device = Device.query.get_or_404(device_id)
    q_from = _parse_dt(request.args.get("from"))
    q_to   = _parse_dt(request.args.get("to"))

    q = CheckResult.query.filter_by(device_id=device.id)
    if q_from:
        q = q.filter(CheckResult.created_at >= q_from)
    if q_to:
        q = q.filter(CheckResult.created_at <= q_to)
    rows = q.order_by(asc(CheckResult.created_at)).all()

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["timestamp", "status", "latency_ms", "message"])
    for r in rows:
        w.writerow([
            r.created_at.isoformat(sep=" ", timespec="seconds"),
            r.status,
            (r.latency_ms if r.latency_ms is not None else ""),
            r.message or ""
        ])
    out = buf.getvalue()
    return Response(
        out,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{device.name}-history.csv"'}
    )


# =================================
# Existing auth + dashboard endpoints
# =================================

# ---- No-cache for auth-sensitive pages
@bp.after_app_request
def add_no_cache_headers(resp):
    if flask_request.endpoint and flask_request.endpoint.startswith("routes."):
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
    return resp

# ---- login-required decorator
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            flash("You must log in first", "danger")
            return redirect(url_for("routes.login"))
        return f(*args, **kwargs)
    return decorated

# ------------------------------
# Login / Logout
# ------------------------------
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "")
        pw = request.form.get("password", "")
        if user == ADMIN_USER and pw == ADMIN_PASS:
            session["logged_in"] = True
            session["role"] = "admin"
            flash("Welcome back!", "success")
            return redirect(url_for("routes.index"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")

@bp.route("/logout")
def logout():
    session.pop("logged_in", None)
    session.pop("role", None)
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
        host = (request.form.get("host") or "").strip()
        kind = (request.form.get("kind") or "").strip().lower()
        port = (request.form.get("port") or "").strip()

        # Normalize kind (icmp/http/tcp). Heuristic if missing/unknown.
        if kind not in ("icmp", "http", "tcp"):
            kind = "icmp" if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host) else "http"

        # If TCP and port provided, encode as host:port so we don't need a DB column
        if kind == "tcp" and port.isdigit():
            host = f"{host}:{int(port)}"

        if name and host:
            d = Device(name=name, host=host, kind=kind)
            db.session.add(d)
            db.session.commit()
            flash(f"Added {name} ({kind})", "success")
        return redirect(url_for("routes.index"))

    devices = Device.query.order_by(Device.id.asc()).all()
    latest = {}
    for d in devices:
        cr = (CheckResult.query
              .filter_by(device_id=d.id)
              .order_by(desc(CheckResult.created_at))
              .first())
        latest[d.id] = cr

    return render_template("index.html", devices=devices, latest=latest)

# ------------------------------
# Delete device
# ------------------------------
@bp.post("/devices/<int:device_id>/delete")
@login_required
def delete_device(device_id):
    device = Device.query.get_or_404(device_id)
    # Clean up related check results first to avoid FK/NULL issues
    CheckResult.query.filter_by(device_id=device.id).delete()
    db.session.delete(device)
    db.session.commit()
    flash("Device deleted", "success")
    return redirect(url_for("routes.index"))

@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    bot_token = get_config("TELEGRAM_BOT_TOKEN", "")
    chat_id = get_config("TELEGRAM_CHAT_ID", "")
    if request.method == "POST":
        set_config("TELEGRAM_BOT_TOKEN", (request.form.get("telegram_bot_token") or "").strip())
        set_config("TELEGRAM_CHAT_ID", (request.form.get("telegram_chat_id") or "").strip())
        flash("Settings saved", "success")
        return redirect(url_for("routes.settings"))
    return render_template("settings.html", bot_token=bot_token, chat_id=chat_id)

# ------------------------------
# JSON API for AJAX updates (read-only)
# ------------------------------
@bp.get("/api/devices")
def api_devices():
    devices = Device.query.order_by(Device.id.asc()).all()
    out = []
    for d in devices:
        cr = (CheckResult.query
              .filter_by(device_id=d.id)
              .order_by(desc(CheckResult.created_at))
              .first())
        out.append({
            "id": d.id,
            "name": d.name,
            "host": d.host,
            "kind": d.kind,
            "status": (cr.status if cr else "Unknown"),
            "latency_ms": (cr.latency_ms if cr and cr.latency_ms is not None else None),
            "last_check": (cr.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC") if cr else None),
        })
    return jsonify(out)
