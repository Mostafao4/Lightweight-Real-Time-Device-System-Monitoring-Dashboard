import os, smtplib, requests
from email.mime.text import MIMEText
from email.utils import formatdate

from app.config_store import get_config

# ---- Telegram (prefer DB settings, fallback to .env)
ENV_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ENV_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# ---- Email (still via .env for simplicity)
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASS = os.getenv("SMTP_PASS", "").strip()
ALERT_EMAIL_TO   = os.getenv("ALERT_EMAIL_TO", "").strip()
ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM", SMTP_USER).strip() or "noreply@example.com"

def notify_telegram(text: str):
    token = get_config("TELEGRAM_BOT_TOKEN", ENV_BOT_TOKEN)
    chat_id = get_config("TELEGRAM_CHAT_ID", ENV_CHAT_ID)
    if not token or not chat_id:
        return False, "telegram disabled (missing token/chat_id)"
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=5
        )
        if r.ok:
            return True, f"telegram {r.status_code}"
        return False, f"telegram {r.status_code}: {r.text[:200]}"
    except requests.RequestException as e:
        return False, f"telegram error: {e}"

def send_email(subject: str, body: str):
    if not SMTP_HOST or not ALERT_EMAIL_TO:
        return False, "email disabled (missing SMTP_HOST/ALERT_EMAIL_TO)"
    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = ALERT_EMAIL_FROM
    msg["To"] = ALERT_EMAIL_TO
    msg["Date"] = formatdate(localtime=True)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
            s.starttls()
            if SMTP_USER:
                s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(ALERT_EMAIL_FROM, [ALERT_EMAIL_TO], msg.as_string())
        return True, "email sent"
    except Exception as e:
        return False, f"email error: {e}"
