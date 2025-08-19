from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import desc
from .models import db, Device, CheckResult

# Make sure this name matches what you use in url_for(...)
bp = Blueprint("routes", __name__)

@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        host = request.form.get("host", "").strip()
        kind = request.form.get("kind", "generic").strip()
        if not name or not host:
            flash("Name and host are required.", "danger")
            return redirect(url_for("routes.index"))
        db.session.add(Device(name=name, host=host, kind=kind))
        db.session.commit()
        flash("Device added.", "success")
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

# Use POST-only route for deletion
@bp.post("/devices/<int:device_id>/delete")
def delete_device(device_id):
    d = Device.query.get_or_404(device_id)
    db.session.delete(d)
    db.session.commit()
    flash("Device deleted.", "success")
    return redirect(url_for("routes.index"))
