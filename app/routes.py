from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import db, Device

bp = Blueprint("routes", __name__)

@bp.route("/")
def index():
    devices = Device.query.order_by(Device.id.asc()).all()
    return render_template("index.html", devices=devices)

@bp.route("/devices/new", methods=["POST"])
def add_device():
    name = request.form.get("name","").strip()
    host = request.form.get("host","").strip()
    kind = request.form.get("kind","generic").strip()
    if not name or not host:
        flash("Name and host are required.", "error")
        return redirect(url_for("routes.index"))
    db.session.add(Device(name=name, host=host, kind=kind))
    db.session.commit()
    flash("Device added.", "ok")
    return redirect(url_for("routes.index"))

@bp.route("/devices/<int:device_id>/delete", methods=["POST"])
def delete_device(device_id):
    d = Device.query.get_or_404(device_id)
    db.session.delete(d)
    db.session.commit()
    flash("Device deleted.", "ok")
    return redirect(url_for("routes.index"))
