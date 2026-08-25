"""Auth: password login, optional TOTP, and passkeys (WebAuthn).

Sessions live in the ``sessions`` table and are handed out as an httponly
cookie. Short-lived state that only matters mid-ceremony — a pending TOTP
login, or a WebAuthn challenge — is kept in an in-process dict rather than
the database: it's gone in minutes either way, and losing it on a restart
just means the user retries.
"""

import hashlib
import io
import re
import secrets
import time
from datetime import datetime, timedelta

import bcrypt
import pyotp
import qrcode
import qrcode.image.svg
from fastapi import Request, Response
from sqlalchemy import select

from db import ApiToken, Session, User, UserSession

SESSION_COOKIE = "session_token"
SESSION_TTL_DAYS = 30
PENDING_TTL_SECONDS = 300
API_TOKEN_PREFIX = "ib_"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value))


async def touch_last_login(user_id: int) -> None:
    async with Session.begin() as session:
        user = await session.get(User, user_id)
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
    expires_at = (datetime.now() + timedelta(days=SESSION_TTL_DAYS)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
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
        return await session.get(User, row.user_id)


async def delete_session(token: str) -> None:
    async with Session.begin() as session:
        row = await session.get(UserSession, token)
        if row is not None:
            await session.delete(row)


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_TTL_DAYS * 86400,
        httponly=True,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


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
    return user


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
