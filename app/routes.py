from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app import db
from app.models import Device, CheckResult
from sqlalchemy import desc

bp = Blueprint("routes", __name__)

# ------------------------------
# Dashboard page
# ------------------------------
@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Add new device
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
def delete_device(device_id):
    device = Device.query.get_or_404(device_id)

    # also delete check results for that device
    CheckResult.query.filter_by(device_id=device.id).delete()

    db.session.delete(device)
    db.session.commit()
    return redirect(url_for("routes.index"))


# ------------------------------
# JSON API for AJAX updates
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
