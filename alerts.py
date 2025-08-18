import os, smtplib, ssl, requests
from email.mime.text import MIMEText

def send_email(subject: str, body: str) -> bool:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    pwd  = os.getenv("SMTP_PASS")
    to   = os.getenv("ALERT_EMAIL_TO")
    if not all([host, port, user, pwd, to]):
        print("[alerts] email not configured; skipping")
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to

    ctx = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=10) as s:
        s.starttls(context=ctx)
        s.login(user, pwd)
        s.sendmail(user, [to], msg.as_string())
    print("[alerts] email sent")
    return True

def send_telegram(text: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat  = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("[alerts] telegram not configured; skipping")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat, "text": text}, timeout=8)
        print(f"[alerts] telegram status={r.status_code} ok={r.ok}")
        return r.ok
    except Exception as e:
        print(f"[alerts] telegram error: {e}")
        return False
