from app.models import db, Config

def get_config(key, default=None):
    row = Config.query.get(key)
    return row.value if row else default

def set_config(key, value):
    row = Config.query.get(key)
    if not row:
        row = Config(key=key, value=value)
        db.session.add(row)
    else:
        row.value = value
    db.session.commit()
