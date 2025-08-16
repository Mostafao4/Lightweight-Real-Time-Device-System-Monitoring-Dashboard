from flask import Flask, jsonify, render_template_string
import socket, time

app = Flask(__name__)

def tcp_ping(host, port=80, timeout_ms=1000):
    start = time.time()
    try:
        with socket.create_connection((host, port), timeout=timeout_ms/1000):
            pass
        latency_ms = int((time.time()-start)*1000)
        return True, latency_ms, None
    except Exception as e:
        return False, None, str(e)

@app.route("/")
def home():
    up, latency, err = tcp_ping("google.com", 80)
    status = "UP" if up else "DOWN"
    html = """
    <!doctype html>
    <html><head><meta charset="utf-8"><title>Monitoring MVP</title></head>
    <body style="font-family:system-ui;margin:2rem">
      <h1>Monitoring MVP</h1>
      <p>google.com: <b style="color:{{'green' if status=='UP' else 'red'}}">{{ status }}</b>
      {% if latency %} ({{ latency }} ms){% endif %}</p>
      {% if err %}<pre style="color:#b00">{{ err }}</pre>{% endif %}
    </body></html>
    """
    return render_template_string(html, status=status, latency=latency, err=err)

@app.route("/health")
def health():
    return jsonify(ok=True)

if __name__ == "__main__":
    app.run(debug=True)
