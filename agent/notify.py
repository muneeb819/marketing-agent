"""Optional notifications for the morning brief (email via SMTP, or webhook)."""
from __future__ import annotations

import os
import smtplib


def send_webhook(url: str, text: str) -> str:
    import requests

    try:
        r = requests.post(url, json={"text": text}, timeout=15)
        return "sent" if r.status_code < 300 else f"webhook status {r.status_code}"
    except Exception as e:
        return f"webhook error: {e}"


def send_email(to: str, subject: str, body: str) -> str:
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    pw = os.environ.get("SMTP_PASS")
    if not (host and user and pw):
        return "email not configured (set SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASS)"
    from email.message import EmailMessage

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to
    try:
        with smtplib.SMTP(host, port, timeout=20) as s:
            s.starttls()
            s.login(user, pw)
            s.send_message(msg)
        return "sent"
    except Exception as e:
        return f"email error: {e}"


def notify(text: str) -> list[str]:
    """Send the brief via any configured channel; return list of status strings."""
    out = []
    wh = os.environ.get("DIGEST_WEBHOOK")
    if wh:
        out.append("webhook: " + send_webhook(wh, text))
    to = os.environ.get("DIGEST_EMAIL_TO")
    if to:
        out.append("email: " + send_email(to, "MarketingOps morning digest", text))
    if not out:
        out.append("no channels configured (set DIGEST_WEBHOOK or SMTP_*/DIGEST_EMAIL_TO)")
    return out
