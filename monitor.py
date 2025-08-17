import time, socket
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from app.models import Device, CheckResult

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
            cr = CheckResult(device_id=d.id, status=status, latency_ms=latency, message=err)
            s.add(cr)
        s.commit()
        s.close()
        time.sleep(interval)

if __name__ == "__main__":
    run_loop()
