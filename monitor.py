import os, time, platform, subprocess, socket, re
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

from app import create_app, db
from app.models import Device, CheckResult

load_dotenv()

INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", "30"))
PING_TIMEOUT_MS  = int(os.getenv("PING_TIMEOUT_MS", "1000"))  # 1s
HTTP_TIMEOUT_S   = float(os.getenv("HTTP_TIMEOUT_S", "3.0"))  # 3s
TCP_TIMEOUT_S    = float(os.getenv("TCP_TIMEOUT_S", "2.0"))   # 2s
DEGRADED_MS      = int(os.getenv("DEGRADED_MS", "800"))       # HTTP latency >= degraded

IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")

app = create_app()

def now_utc():
    return datetime.now(timezone.utc)

def to_status(latency_ms, ok, kind):
    if not ok:
        return "down"
    if kind == "http" and latency_ms is not None and latency_ms >= DEGRADED_MS:
        return "degraded"
    return "up"

def check_icmp(host):
    sys = platform.system().lower()
    if sys.startswith("win"):
        cmd = ["ping", "-n", "1", "-w", str(PING_TIMEOUT_MS), host]
    else:
        timeout_s = max(1, int(PING_TIMEOUT_MS / 1000))
        cmd = ["ping", "-c", "1", "-W", str(timeout_s), host]
    t0 = time.monotonic()
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elapsed = int((time.monotonic() - t0) * 1000)
        ok = (p.returncode == 0)
        return to_status(elapsed if ok else None, ok, "icmp"), (elapsed if ok else None), ("ok" if ok else "no reply")
    except Exception as e:
        return "down", None, f"ping error: {e}"

def normalize_url(host_or_url):
    return host_or_url if host_or_url.startswith(("http://","https://")) else "http://" + host_or_url

def check_http(host_or_url):
    url = normalize_url(host_or_url)
    try:
        t0 = time.monotonic()
        r = requests.get(url, timeout=HTTP_TIMEOUT_S)
        elapsed = int((time.monotonic() - t0) * 1000)
        ok = 200 <= r.status_code < 400
        return to_status(elapsed if ok else None, ok, "http"), (elapsed if ok else None), f"http {r.status_code}"
    except requests.exceptions.Timeout:
        return "down", None, "http timeout"
    except requests.RequestException as e:
        return "down", None, f"http error: {e}"

def parse_host_port(host_with_port):
    if ":" in host_with_port:
        h, p = host_with_port.rsplit(":", 1)
        try:
            return h, int(p)
        except ValueError:
            return host_with_port, None
    return host_with_port, None

def check_tcp(host_with_port):
    host, port = parse_host_port(host_with_port)
    if not port:
        return "down", None, "no port"
    t0 = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=TCP_TIMEOUT_S):
            elapsed = int((time.monotonic() - t0) * 1000)
            return "up", elapsed, "tcp ok"
    except (socket.timeout, OSError) as e:
        return "down", None, f"tcp error: {e}"

def run_once():
    with app.app_context():
        devices = Device.query.filter_by(enabled=True).order_by(Device.id.asc()).all()
        for d in devices:
            k = (d.kind or "").lower()
            if k not in ("icmp", "http", "tcp"):
                # fallback heuristic for legacy rows
                k = "icmp" if IP_RE.match(d.host) else "http"

            if k == "icmp":
                status, latency, msg = check_icmp(d.host)
            elif k == "http":
                status, latency, msg = check_http(d.host)
            else:
                status, latency, msg = check_tcp(d.host)

            prev = (CheckResult.query
                    .filter_by(device_id=d.id)
                    .order_by(CheckResult.created_at.desc())
                    .first())
            changed = (not prev) or (prev.status != status)

            db.session.add(CheckResult(
                device_id=d.id,
                status=status,
                latency_ms=latency,
                message=msg,
                created_at=now_utc(),
            ))
            db.session.commit()

            print(f"[monitor] {d.name}@{d.host} kind={k} status={status} latency={latency}ms changed={changed} msg={msg}", flush=True)

def run_loop():
    while True:
        try:
            run_once()
        except Exception as e:
            print("monitor loop error:", e, flush=True)
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    run_loop()
