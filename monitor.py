import time, socket, os
from dotenv import load_dotenv
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from app.models import Device, CheckResult
from alerts import send_email, send_telegram

load_dotenv()
engine = create_engine("sqlite:///monitor.db", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)

def tcp_ping(host, timeout_ms=1000):
    start = time.time()
    try:
        with socket.create_connection((host, 80), timeout=timeout_ms/1000.0):
            pass
        latency = int((time.time()-start)*1000)
        return True, latency, None
    except Exception as e:
        return False, None, str(e)

def run_loop(interval=30):
    while True:
        s = SessionLocal()
        devices = s.query(Device).filter(Device.enabled == True).all()
        for d in devices:
            up, latency, err = tcp_ping(d.host)
            status = "up" if up else "down"
            prev = s.query(CheckResult).filter_by(device_id=d.id).order_by(desc(CheckResult.created_at)).first()
            changed = prev is None or prev.status != status
            cr = CheckResult(device_id=d.id, status=status, latency_ms=latency, message=err)
            s.add(cr)
            s.commit()
            if changed:
                msg = f"[{d.name} @ {d.host}] {prev.status if prev else 'N/A'} → {status.upper()}"
                send_email("Device status change", msg)
                send_telegram(msg)
        s.close()
        time.sleep(interval)

if __name__ == "__main__":
    run_loop()
