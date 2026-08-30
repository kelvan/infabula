"""Sends account-related emails: verification, and notices for security-
relevant changes (TOTP toggled, a passkey added, baby access granted).

Configured with SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD/SMTP_FROM and
APP_BASE_URL (the address the household actually reaches the app at, used
to build links in emails). Without SMTP_HOST set, the email is logged
instead of sent — registration and everything else here still works
everywhere the tests and local dev run, but nobody outside the server can
ever verify or get notified, so a real deployment must set it.
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
    context = ssl.create_default_context()
    # Port 465 is implicit TLS from the first byte; anything else is
    # assumed to be plaintext-then-STARTTLS (587's convention).
    if SMTP_PORT == 465:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context)
    else:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    with server:
        if SMTP_PORT != 465:
            server.starttls(context=context)
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


def send_totp_enabled_email(to: str) -> None:
    send_email(
        to,
        "Two-factor authentication enabled",
        "Two-factor authentication (TOTP) was just enabled on your "
        f"infabula account ({to}). If this wasn't you, change your "
        "password immediately and contact whoever runs your household's "
        "infabula server.",
    )


def send_totp_disabled_email(to: str) -> None:
    send_email(
        to,
        "Two-factor authentication disabled",
        "Two-factor authentication (TOTP) was just disabled on your "
        f"infabula account ({to}). If this wasn't you, change your "
        "password immediately and contact whoever runs your household's "
        "infabula server.",
    )


def send_passkey_added_email(to: str, passkey_name: str) -> None:
    send_email(
        to,
        "New passkey added",
        f'A new passkey ("{passkey_name}") was just added to your '
        f"infabula account ({to}). If this wasn't you, remove it from "
        "Settings → Account and change your password.",
    )


def send_access_granted_email(to: str, baby_name: str, role: str) -> None:
    send_email(
        to,
        f"You now have access to {baby_name}'s journal",
        f"You've been given {role} access to {baby_name}'s journal on "
        f"infabula. Log in at {APP_BASE_URL} to see it.",
    )


def send_access_granted_owner_notice_email(
    to: str, baby_name: str, granted_email: str, role: str
) -> None:
    send_email(
        to,
        f"Access granted to {baby_name}'s journal",
        f"{granted_email} was just given {role} access to {baby_name}'s "
        "journal. If this wasn't you, remove it from Settings → manage "
        "access.",
    )
