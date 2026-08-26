"""Sends the account-verification email.

Configured with SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD/SMTP_FROM and
APP_BASE_URL (the address the household actually reaches the app at, used
to build the link in the email). Without SMTP_HOST set, the email is
logged instead of sent — registration still works everywhere the tests
and local dev run, but nobody outside the server can ever verify, so a
real deployment must set it.
"""

import os
import smtplib
import ssl
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT") or "587")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM") or SMTP_USER or "infabula@localhost"
APP_BASE_URL = (os.getenv("APP_BASE_URL") or "http://localhost:8080").rstrip("/")


def send_email(to: str, subject: str, body: str) -> None:
    if not SMTP_HOST:
        print(f"[mailer] SMTP_HOST not set, not sending. To: {to}\n{subject}\n{body}")
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg.set_content(body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls(context=ssl.create_default_context())
        if SMTP_USER and SMTP_PASSWORD:
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def send_verification_email(to: str, token: str) -> None:
    link = f"{APP_BASE_URL}/api/auth/verify-email?token={token}"
    send_email(
        to,
        "Confirm your infabula account",
        "Click the link below to confirm your email and finish creating "
        f"your infabula account:\n\n{link}\n\n"
        "This link expires in 24 hours. If you didn't request this, "
        "ignore this email.",
    )
