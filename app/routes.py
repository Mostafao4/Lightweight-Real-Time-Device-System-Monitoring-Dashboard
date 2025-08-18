from flask import Blueprint, render_template, request, redirect, url_for
from .models import db, Device

bp = Blueprint("routes", __name__)

@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        host = request.form.get("host")
        kind = request.form.get("kind")
        if name and host:
            d = Device(name=name, host=host, kind=kind or "generic")
            db.session.add(d)
            db.session.commit()
        return redirect(url_for("routes.index"))

    devices = Device.query.all()
    return render_template("index.html", devices=devices)

@bp.route("/delete/<int:device_id>", methods=["POST"])
def delete_device(device_id):
    d = Device.query.get_or_404(device_id)
    db.session.delete(d)
    db.session.commit()
    return redirect(url_for("routes.index"))
