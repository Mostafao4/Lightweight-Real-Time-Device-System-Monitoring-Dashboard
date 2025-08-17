import os, smtplib, requests
from email.mime.text import MIMEText

def send_email(subject, body):
    host=os.getenv("SMTP_HOST"); port=int(os.getenv("SMTP_PORT","587"))
    user=os.getenv("SMTP_USER"); pwd=os.getenv("SMTP_PASS")
    to=os.getenv("ALERT_EMAIL_TO")
    if not all([host, port, user, pwd, to]): return
    msg=MIMEText(body); msg["Subject"]=subject; msg["From"]=user; msg["To"]=to
    with smtplib.SMTP(host, port, timeout=10) as s:
        s.starttls(); s.login(user, pwd); s.sendmail(user, [to], msg.as_string())

def send_telegram(text):
    token=os.getenv("TELEGRAM_BOT_TOKEN"); chat=os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat: return
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": text}, timeout=5)
    except Exception:
        pass
