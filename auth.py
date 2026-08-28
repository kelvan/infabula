"""Auth: password login, optional TOTP, and passkeys (WebAuthn).

Sessions live in the ``sessions`` table and are handed out as an httponly
cookie. Short-lived state that only matters mid-ceremony — a pending TOTP
login, or a WebAuthn challenge — is kept in an in-process dict rather than
the database: it's gone in minutes either way, and losing it on a restart
just means the user retries.
"""

import hashlib
import io
import ipaddress
import re
import secrets
import time
from datetime import datetime, timedelta, timezone

import bcrypt
import pyotp
import qrcode
import qrcode.image.svg
from fastapi import Request, Response
from sqlalchemy import delete, select

from db import (
    ApiToken,
    EmailVerification,
    Session,
    User,
    UserSession,
    WebauthnCredential,
)

SESSION_COOKIE = "session_token"
SESSION_TTL_DAYS = 30
PENDING_TTL_SECONDS = 300
API_TOKEN_PREFIX = "ib_"
EMAIL_VERIFY_TTL_HOURS = 24

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def now_str() -> str:
    """Bookkeeping stamp, in UTC like everything else stored."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value))


async def touch_last_login(user_id: int) -> None:
    async with Session.begin() as session:
        user = await session.get(User, user_id)
        assert user is not None
        user.last_login_at = now_str()


# ── password ──
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# A hash of no real password, checked when the account doesn't exist (or has
# none) so a login attempt costs the same either way — otherwise an unknown
# username short-circuits before bcrypt runs, and the timing gives it away.
_DUMMY_HASH = hash_password(secrets.token_hex(32))


def verify_password(password: str, hashed: str | None) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), (hashed or _DUMMY_HASH).encode())
    except (ValueError, TypeError):
        return False


# ── sessions ──
async def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = (
        datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)
    ).strftime("%Y-%m-%d %H:%M:%S")
    async with Session.begin() as session:
        session.add(UserSession(token=token, user_id=user_id, expires_at=expires_at))
    return token


async def get_session_user(request: Request) -> User | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return await get_api_token_user(auth_header.removeprefix("Bearer ").strip())

    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    async with Session() as session:
        row = await session.get(UserSession, token)
        if row is None or row.expires_at < now_str():
            return None
        user = await session.get(User, row.user_id)
        # Belt and braces: disabling a user also deletes their sessions,
        # but a cookie presented in the same instant shouldn't slip through.
        if user is not None and user.disabled:
            return None
        return user


async def delete_session(token: str) -> None:
    async with Session.begin() as session:
        row = await session.get(UserSession, token)
        if row is not None:
            await session.delete(row)


async def kill_sessions_for_user(user_id: int) -> None:
    """Ends every session and API token for a user right now.

    Used when disabling an account: flipping the flag alone would still
    honor a cookie or bearer token already in hand until it expired.
    """
    async with Session.begin() as session:
        await session.execute(delete(UserSession).where(UserSession.user_id == user_id))
        await session.execute(delete(ApiToken).where(ApiToken.user_id == user_id))


async def delete_auth_records_for_user(user_id: int) -> None:
    """Removes everything auth owns for a user ahead of deleting the row.

    Baby access, journal entries and the User row itself belong to the
    app's own models and are the caller's job.
    """
    async with Session.begin() as session:
        await session.execute(delete(UserSession).where(UserSession.user_id == user_id))
        await session.execute(delete(ApiToken).where(ApiToken.user_id == user_id))
        await session.execute(
            delete(WebauthnCredential).where(WebauthnCredential.user_id == user_id)
        )
        await session.execute(
            delete(EmailVerification).where(EmailVerification.user_id == user_id)
        )


def set_session_cookie(response: Response, token: str, request: Request) -> None:
    """Hand out the session cookie, marked Secure whenever the request
    arrived over TLS.

    Tracking the actual scheme rather than hardcoding it keeps plain-HTTP
    local dev and the tests working, while a real deployment behind TLS
    always gets the flag — provided uvicorn is started with
    --proxy-headers so the reverse proxy's scheme is what's read here.
    """
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_TTL_DAYS * 86400,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


# ── email verification ──
async def create_email_verification(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = (
        datetime.now(timezone.utc) + timedelta(hours=EMAIL_VERIFY_TTL_HOURS)
    ).strftime("%Y-%m-%d %H:%M:%S")
    async with Session.begin() as session:
        # A fresh link replaces any earlier one for the same account, so
        # an old, still-open email can't be used once a resend was asked
        # for.
        await session.execute(
            delete(EmailVerification).where(EmailVerification.user_id == user_id)
        )
        session.add(
            EmailVerification(token=token, user_id=user_id, expires_at=expires_at)
        )
    return token


async def consume_email_verification(token: str) -> int | None:
    """Marks the token used and returns the user_id it verified, or None."""
    async with Session.begin() as session:
        row = await session.get(EmailVerification, token)
        if row is None or row.expires_at < now_str():
            return None
        user_id = row.user_id
        await session.delete(row)
    return user_id


# ── API tokens ──
def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def generate_api_token() -> tuple[str, str, str]:
    """Returns (raw_token, token_hash, prefix). The raw token is only ever
    seen here and by the caller who hands it to the user once."""
    raw_token = API_TOKEN_PREFIX + secrets.token_urlsafe(32)
    return raw_token, hash_token(raw_token), raw_token[: len(API_TOKEN_PREFIX) + 8]


async def get_api_token_user(raw_token: str) -> User | None:
    if not raw_token:
        return None
    token_hash = hash_token(raw_token)
    async with Session.begin() as session:
        row = await session.scalar(
            select(ApiToken).where(ApiToken.token_hash == token_hash)
        )
        if row is None:
            return None
        row.last_used_at = now_str()
        user = await session.get(User, row.user_id)
    if user is not None and user.disabled:
        return None
    return user


# ── failed-attempt throttling ──
# In-process, like the pending-ceremony state below: a restart clears it,
# which is acceptable for a household-sized deployment and keeps the
# database out of the hot path of every login attempt.
FAIL_WINDOW_SECONDS = 900
MAX_LOGIN_FAILS = 10
MAX_TOTP_FAILS = 5
MAX_RESEND_ATTEMPTS = 5

# The per-account limit alone still lets someone spray one stolen password
# across account after account, ten tries each, indefinitely. Counting
# failures per source address too catches that, and repeat offenders get a
# ban that doubles each time rather than a window that just rolls off.
MAX_IP_FAILS = 20
BAN_BASE_SECONDS = 900
BAN_MAX_SECONDS = 86400

_fails: dict[str, list[float]] = {}
# key -> (ban expires at, how many bans this key has earned)
_bans: dict[str, tuple[float, int]] = {}


def _recent_fails(key: str) -> list[float]:
    cutoff = time.time() - FAIL_WINDOW_SECONDS
    kept = [ts for ts in _fails.get(key, []) if ts > cutoff]
    if kept:
        _fails[key] = kept
    else:
        _fails.pop(key, None)
    return kept


def too_many_fails(key: str, limit: int) -> bool:
    return len(_recent_fails(key)) >= limit


def record_fail(key: str) -> None:
    _fails.setdefault(key, []).append(time.time())


def clear_fails(key: str) -> None:
    _fails.pop(key, None)


def is_lan_address(ip: str) -> bool:
    """Whether an address belongs to the household's own network.

    LAN clients are exempt from IP bans: the router NATs hairpinned
    traffic to a single address, so every device in the house shares one
    source IP and one person mistyping their password repeatedly would
    otherwise lock out everybody. The per-account limit still applies to
    them; the ban is aimed at the internet.

    Anything not publicly routable counts, which is what ``is_private``
    already means — it spans the RFC1918 ranges, loopback, link-local
    and the reserved documentation blocks.
    """
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def is_banned(key: str) -> bool:
    entry = _bans.get(key)
    if entry is None:
        return False
    expires_at, offences = entry
    if time.time() < expires_at:
        return True
    # Ban lapsed, but remember the offence count so a repeat offender is
    # banned for longer next time rather than starting from scratch.
    _bans[key] = (0.0, offences)
    return False


def record_ip_fail(ip: str) -> None:
    """Count a failed credential check, banning the address once it has
    failed too often. No-op for LAN addresses."""
    if not ip or is_lan_address(ip):
        return
    key = f"ip:{ip}"
    record_fail(key)
    if not too_many_fails(key, MAX_IP_FAILS):
        return
    offences = _bans.get(key, (0.0, 0))[1] + 1
    duration = min(BAN_BASE_SECONDS * (2 ** (offences - 1)), BAN_MAX_SECONDS)
    _bans[key] = (time.time() + duration, offences)
    # Start the next window clean so the ban, not a stale backlog of
    # failures, is what gates the address from here on.
    clear_fails(key)


# ── ephemeral ceremony state (pending TOTP logins, WebAuthn challenges) ──
_pending: dict[str, dict] = {}


def _prune_pending() -> None:
    now = time.time()
    for k in [k for k, v in _pending.items() if v["expires"] < now]:
        del _pending[k]


def store_pending(kind: str, data: dict) -> str:
    _prune_pending()
    token = secrets.token_urlsafe(24)
    expires = time.time() + PENDING_TTL_SECONDS
    _pending[token] = {"kind": kind, "expires": expires, **data}
    return token


def peek_pending(token: str, kind: str) -> dict | None:
    _prune_pending()
    entry = _pending.get(token)
    if entry is None or entry["kind"] != kind:
        return None
    return entry


def pop_pending(token: str, kind: str) -> dict | None:
    entry = peek_pending(token, kind)
    if entry is not None:
        del _pending[token]
    return entry


# ── TOTP ──
def new_totp_secret() -> str:
    return pyotp.random_base32()


def totp_uri(secret: str, username: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name="infabula")


def totp_qr_svg(uri: str) -> str:
    img = qrcode.make(uri, image_factory=qrcode.image.svg.SvgPathImage)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue().decode()


def verify_totp(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)


# ── WebAuthn ──
def rp_id_from_request(request: Request) -> str:
    """The Relying Party id WebAuthn ceremonies are scoped to.

    Must be an exact match (or registrable-domain suffix) of the origin's
    hostname. Browsers only allow WebAuthn in a secure context, so this
    only actually works once the app is served over HTTPS or localhost —
    over plain LAN HTTP the browser will refuse the ceremony regardless of
    what's returned here.
    """
    return request.url.hostname or "localhost"


def origin_from_request(request: Request) -> str:
    return f"{request.url.scheme}://{request.url.netloc}"
