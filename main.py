import asyncio
import csv
import io
import json
import os
import sqlite3
import time
from datetime import date, datetime, timedelta, timezone
from datetime import time as dtime
from itertools import groupby
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, func, select, update
from sqlalchemy import false as sa_false
from sqlalchemy.exc import IntegrityError
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import PublicKeyCredentialDescriptor

import auth
import mailer
from db import (
    DEFAULT_BABY_ID,
    ROLE_EDITOR,
    ROLE_OWNER,
    ROLE_VIEWER,
    ApiToken,
    Baby,
    BabyAccess,
    Entry,
    Session,
    User,
    WebauthnCredential,
    sqlite_file,
)
from migrate import run_migrations

app = FastAPI(
    title="infabula API",
    description=(
        "Local-network baby journal. Every request needs a logged-in "
        "session cookie or an `Authorization: Bearer <token>` — mint a "
        "token from Settings → Account → API tokens."
    ),
    version="1.0.0",
)
ASSET_VERSION = str(int(time.time()))


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "bearerAuth": {"type": "http", "scheme": "bearer"}
    }
    schema["security"] = [{"bearerAuth": []}]
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi  # ty: ignore[invalid-assignment]

# ── Time ──
# ts_start/ts_end hold an explicit UTC instant, 'YYYY-MM-DDTHH:MMZ'. The
# format is fixed-width, so lexicographic ordering and BETWEEN ranges are
# chronological and no per-row conversion is needed to query.
ENTRY_TS_FMT = "%Y-%m-%dT%H:%MZ"

# Which local day an instant belongs to is a presentation question, and a
# single-household journal has one answer: the household's own zone.
HOUSEHOLD_TZ = ZoneInfo(os.getenv("TZ") or "UTC")

# Open by default (household deployments have always let anyone who can
# reach the app sign up); flip off once the app is reachable from the
# internet and new accounts should only come from an invite.
REGISTRATION_ENABLED = (os.getenv("REGISTRATION_ENABLED") or "true").lower() not in (
    "false",
    "0",
    "no",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_entry_ts(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime(ENTRY_TS_FMT)


def parse_entry_ts(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.strptime(value, ENTRY_TS_FMT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def local_day_bounds(day: str) -> tuple[str, str] | None:
    """The [start, end) UTC instants covering a local calendar date.

    Built from both local midnights rather than start + 24h, so the short
    and long days either side of a DST switch come out right.
    """
    try:
        parsed = date.fromisoformat(day)
    except (TypeError, ValueError):
        return None
    lo = datetime.combine(parsed, dtime.min, tzinfo=HOUSEHOLD_TZ)
    hi = datetime.combine(parsed + timedelta(days=1), dtime.min, tzinfo=HOUSEHOLD_TZ)
    return to_entry_ts(lo), to_entry_ts(hi)


def local_day_of(value: str) -> str:
    """The local calendar date a stored UTC instant falls on."""
    moment = parse_entry_ts(value)
    if moment is None:
        return (value or "")[:10]
    return moment.astimezone(HOUSEHOLD_TZ).strftime("%Y-%m-%d")


def local_time_of(value: str) -> str:
    """The local clock time (HH:MM) of a stored UTC instant."""
    moment = parse_entry_ts(value)
    if moment is None:
        return (value or "")[11:16]
    return moment.astimezone(HOUSEHOLD_TZ).strftime("%H:%M")


def on_local_day(column, day: str):
    """SQL predicate: this timestamp column falls on the given local date."""
    bounds = local_day_bounds(day)
    if bounds is None:
        return sa_false()
    lo, hi = bounds
    return (column >= lo) & (column < hi)


ROLE_RANK = {ROLE_VIEWER: 0, ROLE_EDITOR: 1, ROLE_OWNER: 2}

# Ceilings that keep a runaway script (or a bug) from filling the database.
# All are far above what hand-logging a baby's day could ever reach.
MAX_BABIES_PER_USER = 20
MAX_ENTRIES_PER_DAY = 500
MAX_ENTRIES_LIMIT = 1000
# A journal is written as the day happens: an entry may be logged slightly
# ahead of the clock (a bottle you're about to give) or filled in for the
# past week, but not beyond that.
ENTRY_MAX_FUTURE = timedelta(hours=1)
ENTRY_MAX_PAST = timedelta(days=7)

# A nap runs shorter than this; anything longer is treated as night sleep
# and left out of the average nap duration.
NIGHT_SLEEP_MIN_MINUTES = 240


def entries_of(baby_id: int = DEFAULT_BABY_ID):
    """Base query scoped to one baby's log."""
    return select(Entry).where(Entry.baby_id == baby_id)


def check_entry_window(ts_start: str, allow_old: bool = False) -> JSONResponse | None:
    """None if ts_start is inside the allowed window, else a 400 to return.

    Editing keeps the future cap but drops the past floor (`allow_old`),
    so a typo in a three-week-old entry stays fixable — a PATCH cannot
    add rows, so it is not a flooding risk either way.
    """
    parsed = parse_entry_ts(ts_start)
    if parsed is None:
        return JSONResponse({"error": "invalid ts_start"}, status_code=400)
    now = utc_now()
    if parsed > now + ENTRY_MAX_FUTURE:
        return JSONResponse(
            {"error": "ts_start too far in the future"}, status_code=400
        )
    if not allow_old and parsed < now - ENTRY_MAX_PAST:
        return JSONResponse({"error": "ts_start too far in the past"}, status_code=400)
    return None


async def day_is_full(baby_id: int, day: str) -> bool:
    async with Session() as session:
        count = await session.scalar(
            select(func.count())
            .select_from(Entry)
            .where(Entry.baby_id == baby_id, on_local_day(Entry.ts_start, day))
        )
    return (count or 0) >= MAX_ENTRIES_PER_DAY


async def role_for(user_id: int, baby_id: int) -> str | None:
    async with Session() as session:
        access = await session.get(BabyAccess, (user_id, baby_id))
    return access.role if access else None


async def require_access(
    request: Request, baby_id: int, min_role: str = ROLE_VIEWER
) -> JSONResponse | None:
    """None if the current user meets min_role on baby_id, else a 403 to return."""
    role = await role_for(request.state.user.id, baby_id)
    if role is None or ROLE_RANK[role] < ROLE_RANK[min_role]:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    return None


def require_admin(request: Request) -> JSONResponse | None:
    """None if the current user is an admin, else a 403 to return."""
    if not request.state.user.is_admin:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    return None

# ── SSE pub-sub ──
subscribers: set[asyncio.Queue] = set()


async def broadcast_event(event_type: str):
    for q in list(subscribers):
        q.put_nowait(event_type)


@app.get("/api/events", tags=["Live sync"])
async def sse_events():
    queue: asyncio.Queue = asyncio.Queue()
    subscribers.add(queue)

    async def event_stream():
        try:
            while True:
                try:
                    event_type = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f'data: {{"type": "{event_type}"}}\n\n'
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            subscribers.discard(queue)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def backup_db():
    """Snapshot the database file on startup.

    Only meaningful for SQLite — server-backed databases are expected to have
    their own backup story, so this is skipped for them.
    """
    path = sqlite_file()
    if not path or not os.path.exists(path):
        return
    db_dir = os.path.dirname(os.path.abspath(path))
    backup_dir = os.path.join(db_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    name, ext = os.path.splitext(os.path.basename(path))
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    src = sqlite3.connect(path)
    dst = sqlite3.connect(os.path.join(backup_dir, f"{name}-{timestamp}{ext}"))
    with dst:
        src.backup(dst)
    dst.close()
    src.close()


backup_db()
run_migrations()


class CachedStaticFiles(StaticFiles):
    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


app.mount("/static", CachedStaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates", auto_reload=True)
templates.env.cache = None


def get_client_ip(request: Request) -> str:
    """The address the request actually came from.

    Takes the *last* X-Forwarded-For entry, not the first. A client can
    send its own X-Forwarded-For and a proxy appends to it rather than
    replacing it, so the leftmost entry is attacker-controlled — the
    rightmost is the one the proxy in front of us wrote itself. Caddy is
    also configured to overwrite the header outright; this is the second
    lock on that door.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        hops = [hop.strip() for hop in forwarded.split(",") if hop.strip()]
        if hops:
            return hops[-1]
    return request.client.host if request.client else "unknown"


def row_to_dict(entry: Entry) -> dict:
    return entry.as_dict()


# ── Auth gate ──
# Everything requires a session except the login page, static assets, and
# the handful of auth endpoints a not-yet-logged-in browser needs to reach
# (register/login/TOTP-verify/passkey-login). Auth endpoints that manage an
# *existing* account's credentials — TOTP setup, passkey enrollment, logout —
# stay behind the gate like any other API route. Unauthenticated HTML
# requests bounce to /login; unauthenticated API requests get a plain 401.
PUBLIC_PREFIXES = ("/static/",)
PUBLIC_PATHS = (
    "/login",
    "/api/auth/register",
    "/api/auth/login",
    "/api/auth/totp/verify",
    "/api/auth/passkey/login/options",
    "/api/auth/passkey/login/verify",
    "/api/auth/verify-email",
    "/api/auth/resend-verification",
)


@app.middleware("http")
async def auth_gate(request: Request, call_next):
    path = request.url.path
    if path.startswith(PUBLIC_PREFIXES) or path in PUBLIC_PATHS:
        return await call_next(request)
    user = await auth.get_session_user(request)
    if user is None:
        if path.startswith("/api/"):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return RedirectResponse("/login")
    request.state.user = user
    return await call_next(request)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "v": ASSET_VERSION}
    )


def registration_allowed(request: Request) -> bool:
    """Open globally per REGISTRATION_ENABLED, or always for the LAN —
    closing it to the internet shouldn't stop the household adding a
    new member from their own wifi."""
    return REGISTRATION_ENABLED or auth.is_lan_address(get_client_ip(request))


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if await auth.get_session_user(request) is not None:
        return RedirectResponse("/")
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "v": ASSET_VERSION,
            "registration_enabled": registration_allowed(request),
        },
    )


def user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.username,
        "name": user.name,
        "totp_enabled": user.totp_enabled,
        "is_admin": user.is_admin,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
    }


async def send_verification_email(email: str, user_id: int) -> None:
    token = await auth.create_email_verification(user_id)
    await asyncio.to_thread(mailer.send_verification_email, email, token)


@app.post("/api/auth/register", tags=["Auth"])
async def register(request: Request):
    if not registration_allowed(request):
        return JSONResponse({"error": "registration is closed"}, status_code=403)
    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    if not auth.is_valid_email(email) or len(password) < 8:
        return JSONResponse(
            {"error": "a valid email and an 8+ character password are required"},
            status_code=400,
        )
    try:
        async with Session.begin() as session:
            existing = await session.scalar(
                select(User).where(User.username == email)
            )
            if existing is not None:
                return JSONResponse(
                    {"error": "email already registered"}, status_code=409
                )
            user = User(
                name=email,
                username=email,
                email=email,
                password_hash=auth.hash_password(password),
            )
            session.add(user)
            await session.flush()
            user_id = user.id
    except IntegrityError:
        # A second registration for the same email landed between our
        # check and the insert; the unique constraint is the real guard.
        return JSONResponse({"error": "email already registered"}, status_code=409)
    await send_verification_email(email, user_id)
    return {"ok": True}


@app.get("/api/auth/verify-email", tags=["Auth"])
async def verify_email(token: str = ""):
    user_id = await auth.consume_email_verification(token)
    if user_id is None:
        return RedirectResponse("/login?verify=expired")
    async with Session.begin() as session:
        user = await session.get(User, user_id)
        if user is not None:
            user.email_verified = True
    return RedirectResponse("/login?verify=ok")


@app.post("/api/auth/resend-verification", tags=["Auth"])
async def resend_verification(request: Request):
    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    fail_key = f"resend:{email}"
    if auth.too_many_fails(fail_key, auth.MAX_RESEND_ATTEMPTS):
        return JSONResponse({"error": "too many attempts, try later"}, status_code=429)
    async with Session() as session:
        user = await session.scalar(select(User).where(User.username == email))
    if user is None or not auth.verify_password(password, user.password_hash):
        auth.record_fail(fail_key)
        return JSONResponse({"error": "invalid credentials"}, status_code=401)
    auth.clear_fails(fail_key)
    if user.email_verified:
        return {"ok": True, "already_verified": True}
    await send_verification_email(email, user.id)
    return {"ok": True}


@app.post("/api/auth/login", tags=["Auth"])
async def login(request: Request, response: Response):
    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    client_ip = get_client_ip(request)
    fail_key = f"login:{email}"
    if auth.is_banned(f"ip:{client_ip}") or auth.too_many_fails(
        fail_key, auth.MAX_LOGIN_FAILS
    ):
        return JSONResponse({"error": "too many attempts, try later"}, status_code=429)
    async with Session() as session:
        user = await session.scalar(select(User).where(User.username == email))
    password_ok = auth.verify_password(password, user.password_hash if user else None)
    if user is None or not password_ok:
        auth.record_fail(fail_key)
        auth.record_ip_fail(client_ip)
        return JSONResponse({"error": "invalid credentials"}, status_code=401)
    auth.clear_fails(fail_key)
    if user.disabled:
        return JSONResponse({"error": "account disabled"}, status_code=403)
    if not user.email_verified:
        return JSONResponse({"error": "email not verified"}, status_code=403)
    if user.totp_enabled:
        pending_token = auth.store_pending("totp_login", {"user_id": user.id})
        return {"totp_required": True, "pending_token": pending_token}
    await auth.touch_last_login(user.id)
    token = await auth.create_session(user.id)
    auth.set_session_cookie(response, token, request)
    return {"ok": True}


@app.post("/api/auth/totp/verify", tags=["Auth"])
async def totp_verify_login(request: Request, response: Response):
    body = await request.json()
    pending_token = body.get("pending_token") or ""
    pending = auth.peek_pending(pending_token, "totp_login")
    if pending is None:
        return JSONResponse({"error": "expired, log in again"}, status_code=400)
    # A wrong code deliberately does not consume the pending token, so a
    # typo can just be retried — which is exactly why the attempt count
    # has to be capped, or the 6-digit code would be brute-forceable for
    # as long as the token lives.
    client_ip = get_client_ip(request)
    fail_key = f"totp:{pending_token}"
    if auth.is_banned(f"ip:{client_ip}"):
        return JSONResponse({"error": "too many attempts, try later"}, status_code=429)
    if auth.too_many_fails(fail_key, auth.MAX_TOTP_FAILS):
        auth.pop_pending(pending_token, "totp_login")
        auth.clear_fails(fail_key)
        return JSONResponse(
            {"error": "too many attempts, log in again"}, status_code=429
        )
    async with Session() as session:
        user = await session.get(User, pending["user_id"])
    if user is None or not auth.verify_totp(
        user.totp_secret or "", body.get("code") or ""
    ):
        auth.record_fail(fail_key)
        auth.record_ip_fail(client_ip)
        return JSONResponse({"error": "invalid code"}, status_code=401)
    auth.pop_pending(pending_token, "totp_login")
    auth.clear_fails(fail_key)
    await auth.touch_last_login(user.id)
    token = await auth.create_session(user.id)
    auth.set_session_cookie(response, token, request)
    return {"ok": True}


@app.post("/api/auth/logout", tags=["Auth"])
async def logout(request: Request, response: Response):
    token = request.cookies.get(auth.SESSION_COOKIE)
    if token:
        await auth.delete_session(token)
    auth.clear_session_cookie(response)
    return {"ok": True}


@app.get("/api/auth/me", tags=["Auth"])
async def me(request: Request):
    return user_to_dict(request.state.user)


@app.put("/api/auth/me", tags=["Auth"])
async def update_me(request: Request):
    body = await request.json()
    name = (body.get("name") or "").strip()
    if not name:
        return JSONResponse({"error": "name cannot be empty"}, status_code=400)
    async with Session.begin() as session:
        user = await session.get(User, request.state.user.id)
        assert user is not None
        user.name = name[:128]
    return {"ok": True}


@app.delete("/api/auth/me", tags=["Auth"])
async def delete_me(request: Request, response: Response):
    body = await request.json()
    user = request.state.user
    if not auth.verify_password(body.get("password") or "", user.password_hash):
        return JSONResponse({"error": "wrong password"}, status_code=401)

    async with Session() as session:
        owned = (
            await session.scalars(
                select(BabyAccess.baby_id).where(
                    BabyAccess.user_id == user.id, BabyAccess.role == ROLE_OWNER
                )
            )
        ).all()
        solely_owned = []
        for baby_id in owned:
            other_owner = await session.scalar(
                select(BabyAccess).where(
                    BabyAccess.baby_id == baby_id,
                    BabyAccess.role == ROLE_OWNER,
                    BabyAccess.user_id != user.id,
                )
            )
            if other_owner is None:
                baby = await session.get(Baby, baby_id)
                solely_owned.append(baby.name if baby else str(baby_id))
    if solely_owned:
        return JSONResponse(
            {
                "error": "transfer or delete these babies first: "
                + ", ".join(solely_owned)
            },
            status_code=400,
        )

    await auth.delete_auth_records_for_user(user.id)
    async with Session.begin() as session:
        await session.execute(
            delete(BabyAccess).where(BabyAccess.user_id == user.id)
        )
        await session.execute(
            update(Entry).where(Entry.user_id == user.id).values(user_id=None)
        )
        await session.execute(delete(User).where(User.id == user.id))
    auth.clear_session_cookie(response)
    return {"ok": True}



@app.post("/api/auth/totp/setup", tags=["Auth"])
async def totp_setup(request: Request):
    secret = auth.new_totp_secret()
    async with Session.begin() as session:
        user = await session.get(User, request.state.user.id)
        assert user is not None
        user.totp_secret = secret
        user.totp_enabled = False
        username = user.username
    uri = auth.totp_uri(secret, username or "")
    return {"secret": secret, "qr_svg": auth.totp_qr_svg(uri)}


@app.post("/api/auth/totp/confirm", tags=["Auth"])
async def totp_confirm(request: Request):
    body = await request.json()
    async with Session.begin() as session:
        user = await session.get(User, request.state.user.id)
        assert user is not None
        if not user.totp_secret or not auth.verify_totp(
            user.totp_secret, body.get("code") or ""
        ):
            return JSONResponse({"error": "invalid code"}, status_code=400)
        user.totp_enabled = True
    return {"ok": True}


@app.post("/api/auth/totp/disable", tags=["Auth"])
async def totp_disable(request: Request):
    body = await request.json()
    async with Session.begin() as session:
        user = await session.get(User, request.state.user.id)
        assert user is not None
        ok = auth.verify_password(body.get("password") or "", user.password_hash or "")
        if not ok:
            return JSONResponse({"error": "wrong password"}, status_code=401)
        user.totp_enabled = False
        user.totp_secret = None
    return {"ok": True}


# ── Admin ──
def admin_user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.username,
        "name": user.name,
        "disabled": user.disabled,
        "is_admin": user.is_admin,
        "email_verified": user.email_verified,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
    }


@app.get("/api/admin/users", tags=["Admin"])
async def admin_list_users(request: Request):
    if (denied := require_admin(request)) is not None:
        return denied
    async with Session() as session:
        rows = (
            await session.scalars(select(User).order_by(User.id))
        ).all()
    return [admin_user_to_dict(u) for u in rows]


@app.post("/api/admin/users/{user_id}/disable", tags=["Admin"])
async def admin_disable_user(user_id: int, request: Request):
    if (denied := require_admin(request)) is not None:
        return denied
    if user_id == request.state.user.id:
        return JSONResponse(
            {"error": "cannot disable your own account"}, status_code=400
        )
    async with Session.begin() as session:
        user = await session.get(User, user_id)
        if user is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        user.disabled = True
    await auth.kill_sessions_for_user(user_id)
    return {"ok": True}


@app.post("/api/admin/users/{user_id}/enable", tags=["Admin"])
async def admin_enable_user(user_id: int, request: Request):
    if (denied := require_admin(request)) is not None:
        return denied
    async with Session.begin() as session:
        user = await session.get(User, user_id)
        if user is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        user.disabled = False
    return {"ok": True}


@app.get("/api/auth/tokens", tags=["API tokens"], summary="List your API tokens")
async def list_tokens(request: Request):
    """Personal access tokens for this account. The raw token itself is
    never returned here — only what was shown once at creation time."""
    async with Session() as session:
        rows = (
            await session.scalars(
                select(ApiToken)
                .where(ApiToken.user_id == request.state.user.id)
                .order_by(ApiToken.created_at.desc())
            )
        ).all()
    return [
        {
            "id": tok.id,
            "name": tok.name,
            "prefix": tok.prefix,
            "created_at": tok.created_at,
            "last_used_at": tok.last_used_at,
        }
        for tok in rows
    ]


@app.post("/api/auth/tokens", tags=["API tokens"], summary="Create an API token")
async def create_token(request: Request):
    """Mints a new bearer token for this account and returns it in full —
    the only time it is ever visible. Send it as `Authorization: Bearer
    <token>` on later requests; it grants the same access as the account
    that created it."""
    body = await request.json()
    name = (body.get("name") or "").strip() or "Token"
    raw_token, token_hash, prefix = auth.generate_api_token()
    async with Session.begin() as session:
        row = ApiToken(
            user_id=request.state.user.id,
            name=name[:128],
            token_hash=token_hash,
            prefix=prefix,
        )
        session.add(row)
        await session.flush()
        token_id = row.id
    return {"id": token_id, "name": name, "token": raw_token}


@app.delete(
    "/api/auth/tokens/{token_id}", tags=["API tokens"], summary="Revoke an API token"
)
async def delete_token(token_id: int, request: Request):
    async with Session.begin() as session:
        row = await session.get(ApiToken, token_id)
        if row is not None and row.user_id == request.state.user.id:
            await session.delete(row)
    return {"ok": True}


@app.get("/api/auth/passkeys", tags=["Passkeys"])
async def list_passkeys(request: Request):
    async with Session() as session:
        rows = (
            await session.scalars(
                select(WebauthnCredential).where(
                    WebauthnCredential.user_id == request.state.user.id
                )
            )
        ).all()
    return [
        {"id": c.id, "name": c.name or "Passkey", "created_at": c.created_at}
        for c in rows
    ]


@app.delete("/api/auth/passkeys/{cred_id}", tags=["Passkeys"])
async def delete_passkey(cred_id: int, request: Request):
    async with Session.begin() as session:
        cred = await session.get(WebauthnCredential, cred_id)
        if cred is not None and cred.user_id == request.state.user.id:
            await session.delete(cred)
    return {"ok": True}


@app.post("/api/auth/passkey/register/options", tags=["Passkeys"])
async def passkey_register_options(request: Request):
    async with Session() as session:
        existing = (
            await session.scalars(
                select(WebauthnCredential).where(
                    WebauthnCredential.user_id == request.state.user.id
                )
            )
        ).all()
    options = generate_registration_options(
        rp_id=auth.rp_id_from_request(request),
        rp_name="infabula",
        user_id=str(request.state.user.id).encode(),
        user_name=request.state.user.username,
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(c.credential_id))
            for c in existing
        ],
    )
    challenge_token = auth.store_pending(
        "passkey_register",
        {"user_id": request.state.user.id, "challenge": options.challenge},
    )
    return {
        "options": json.loads(options_to_json(options)),
        "challenge_token": challenge_token,
    }


@app.post("/api/auth/passkey/register/verify", tags=["Passkeys"])
async def passkey_register_verify(request: Request):
    body = await request.json()
    pending = auth.pop_pending(body.get("challenge_token") or "", "passkey_register")
    if pending is None or pending["user_id"] != request.state.user.id:
        return JSONResponse({"error": "expired, try again"}, status_code=400)
    try:
        verification = verify_registration_response(
            credential=body["credential"],
            expected_challenge=pending["challenge"],
            expected_rp_id=auth.rp_id_from_request(request),
            expected_origin=auth.origin_from_request(request),
        )
    except Exception:
        return JSONResponse({"error": "registration failed"}, status_code=400)
    async with Session.begin() as session:
        session.add(
            WebauthnCredential(
                user_id=request.state.user.id,
                credential_id=bytes_to_base64url(verification.credential_id),
                public_key=bytes_to_base64url(verification.credential_public_key),
                sign_count=verification.sign_count,
                name=(body.get("name") or "Passkey").strip()[:128],
            )
        )
    return {"ok": True}


@app.post("/api/auth/passkey/login/options", tags=["Passkeys"])
async def passkey_login_options(request: Request):
    body = await request.json() if await request.body() else {}
    email = (body.get("email") or "").strip().lower()
    allow_credentials = None
    if email:
        async with Session() as session:
            user = await session.scalar(select(User).where(User.username == email))
            creds = (
                (
                    await session.scalars(
                        select(WebauthnCredential).where(
                            WebauthnCredential.user_id == user.id
                        )
                    )
                ).all()
                if user
                else []
            )
        allow_credentials = [
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(c.credential_id))
            for c in creds
        ]
    options = generate_authentication_options(
        rp_id=auth.rp_id_from_request(request), allow_credentials=allow_credentials
    )
    challenge_token = auth.store_pending(
        "passkey_login", {"challenge": options.challenge}
    )
    return {
        "options": json.loads(options_to_json(options)),
        "challenge_token": challenge_token,
    }


@app.post("/api/auth/passkey/login/verify", tags=["Passkeys"])
async def passkey_login_verify(request: Request, response: Response):
    body = await request.json()
    pending = auth.pop_pending(body.get("challenge_token") or "", "passkey_login")
    if pending is None:
        return JSONResponse({"error": "expired, try again"}, status_code=400)
    credential = body["credential"]
    cred_id = credential.get("id") or credential.get("rawId")
    async with Session() as session:
        stored = await session.scalar(
            select(WebauthnCredential).where(
                WebauthnCredential.credential_id == cred_id
            )
        )
    if stored is None:
        return JSONResponse({"error": "unknown passkey"}, status_code=401)
    try:
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=pending["challenge"],
            expected_rp_id=auth.rp_id_from_request(request),
            expected_origin=auth.origin_from_request(request),
            credential_public_key=base64url_to_bytes(stored.public_key),
            credential_current_sign_count=stored.sign_count,
        )
    except Exception:
        return JSONResponse({"error": "verification failed"}, status_code=401)
    async with Session() as session:
        owner = await session.get(User, stored.user_id)
    if owner is None or owner.disabled:
        return JSONResponse({"error": "account disabled"}, status_code=403)
    async with Session.begin() as session:
        row = await session.get(WebauthnCredential, stored.id)
        if row is None:
            return JSONResponse({"error": "unknown passkey"}, status_code=401)
        row.sign_count = verification.new_sign_count
    await auth.touch_last_login(stored.user_id)
    token = await auth.create_session(stored.user_id)
    auth.set_session_cookie(response, token, request)
    return {"ok": True}


@app.post("/api/entries", tags=["Entries"])
async def create_entry(request: Request, baby_id: int = DEFAULT_BABY_ID):
    if (denied := await require_access(request, baby_id, ROLE_EDITOR)) is not None:
        return denied
    body = await request.json()
    entry_type = body.get("type") or ""
    if not entry_type:
        return JSONResponse({"error": "type is required"}, status_code=400)
    ts_start = body.get("ts_start") or ""
    if (bad := check_entry_window(ts_start)) is not None:
        return bad
    if await day_is_full(baby_id, local_day_of(ts_start)):
        return JSONResponse(
            {"error": "too many entries for that day"}, status_code=429
        )
    entry = Entry(
        type=entry_type,
        ts_start=ts_start,
        ts_end=body.get("ts_end"),
        note=body.get("note", ""),
        meta=body.get("meta", {}),
        ip=get_client_ip(request),
        baby_id=baby_id,
        user_id=request.state.user.id,
    )
    async with Session.begin() as session:
        session.add(entry)
    await broadcast_event("entries_changed")
    return row_to_dict(entry)


@app.patch("/api/entries/{entry_id}", tags=["Entries"])
async def patch_entry(entry_id: int, request: Request):
    async with Session() as session:
        existing = await session.get(Entry, entry_id)
    if existing is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    if (
        denied := await require_access(request, existing.baby_id, ROLE_EDITOR)
    ) is not None:
        return denied
    body = await request.json()
    if "ts_start" in body and (
        bad := check_entry_window(body.get("ts_start") or "", allow_old=True)
    ) is not None:
        return bad
    async with Session.begin() as session:
        entry = await session.get(Entry, entry_id)
        if entry is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        for field in ("ts_start", "ts_end", "note", "meta"):
            if field in body:
                setattr(entry, field, body[field])
    await broadcast_event("entries_changed")
    return row_to_dict(entry)


@app.get("/api/entries", tags=["Entries"])
async def get_entries(
    request: Request,
    date: str | None = None,
    limit: int = 300,
    baby_id: int = DEFAULT_BABY_ID,
):
    if (denied := await require_access(request, baby_id, ROLE_VIEWER)) is not None:
        return denied
    limit = max(1, min(limit, MAX_ENTRIES_LIMIT))
    async with Session() as session:
        stmt = (
            select(Entry, User.name)
            .outerjoin(User, User.id == Entry.user_id)
            .where(Entry.baby_id == baby_id)
            .order_by(Entry.ts_start.desc())
        )
        if date:
            stmt = stmt.where(
                on_local_day(Entry.ts_start, date) | on_local_day(Entry.ts_end, date)
            )
        else:
            stmt = stmt.limit(limit)
        rows = (await session.execute(stmt)).all()
    return [{**row_to_dict(e), "username": username} for e, username in rows]


@app.get("/api/entries/dates", tags=["Entries"])
async def get_dates(request: Request, baby_id: int = DEFAULT_BABY_ID):
    """Return list of distinct dates that have entries."""
    if (denied := await require_access(request, baby_id, ROLE_VIEWER)) is not None:
        return denied
    # Which local day a UTC instant lands on depends on the household
    # zone, so the distinct-ing happens here rather than in SQL.
    async with Session() as session:
        rows = (
            await session.scalars(
                select(Entry.ts_start)
                .where(Entry.baby_id == baby_id)
                .order_by(Entry.ts_start.desc())
                .limit(2000)
            )
        ).all()
    days: list[str] = []
    seen: set[str] = set()
    for value in rows:
        day = local_day_of(value)
        if day not in seen:
            seen.add(day)
            days.append(day)
        if len(days) >= 90:
            break
    return days


def baby_to_dict(baby: Baby) -> dict:
    return {"id": baby.id, "name": baby.name, "birthday": baby.birthday or ""}


@app.get("/api/babies", tags=["Babies"])
async def list_babies(request: Request):
    async with Session() as session:
        rows = (
            await session.execute(
                select(Baby, BabyAccess.role)
                .join(BabyAccess, BabyAccess.baby_id == Baby.id)
                .where(BabyAccess.user_id == request.state.user.id)
                .order_by(Baby.id)
            )
        ).all()
    return [{**baby_to_dict(b), "role": role} for b, role in rows]


@app.post("/api/babies", tags=["Babies"])
async def create_baby(request: Request):
    body = await request.json()
    name = (body.get("name") or "").strip() or "Baby"
    birthday = (body.get("birthday") or "").strip() or None
    # Counts only babies this account owns — being invited to someone
    # else's log should never use up your own allowance.
    async with Session() as session:
        owned = await session.scalar(
            select(func.count())
            .select_from(BabyAccess)
            .where(
                BabyAccess.user_id == request.state.user.id,
                BabyAccess.role == ROLE_OWNER,
            )
        )
    if (owned or 0) >= MAX_BABIES_PER_USER:
        return JSONResponse({"error": "too many babies"}, status_code=429)
    async with Session.begin() as session:
        baby = Baby(name=name, birthday=birthday)
        session.add(baby)
        await session.flush()
        session.add(
            BabyAccess(user_id=request.state.user.id, baby_id=baby.id, role=ROLE_OWNER)
        )
        result = baby_to_dict(baby)
    await broadcast_event("entries_changed")
    return result


@app.put("/api/babies/{baby_id}", tags=["Babies"])
async def update_baby(baby_id: int, request: Request):
    if (denied := await require_access(request, baby_id, ROLE_EDITOR)) is not None:
        return denied
    body = await request.json()
    async with Session.begin() as session:
        baby = await session.get(Baby, baby_id)
        if baby is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        if "name" in body:
            baby.name = (body.get("name") or "").strip() or baby.name
        if "birthday" in body:
            baby.birthday = (body.get("birthday") or "").strip() or None
    await broadcast_event("entries_changed")
    return {"ok": True}


@app.delete("/api/babies/{baby_id}", tags=["Babies"])
async def delete_baby(baby_id: int, request: Request):
    if (denied := await require_access(request, baby_id, ROLE_OWNER)) is not None:
        return denied
    async with Session.begin() as session:
        await session.execute(delete(Entry).where(Entry.baby_id == baby_id))
        await session.execute(delete(BabyAccess).where(BabyAccess.baby_id == baby_id))
        await session.execute(delete(Baby).where(Baby.id == baby_id))
    await broadcast_event("entries_changed")
    return {"ok": True}


@app.get("/api/babies/{baby_id}/access", tags=["Baby access"])
async def list_baby_access(baby_id: int, request: Request):
    if (denied := await require_access(request, baby_id, ROLE_OWNER)) is not None:
        return denied
    async with Session() as session:
        rows = (
            await session.execute(
                select(BabyAccess.user_id, BabyAccess.role, User.username)
                .join(User, User.id == BabyAccess.user_id)
                .where(BabyAccess.baby_id == baby_id)
                .order_by(User.username)
            )
        ).all()
    return [{"user_id": r[0], "role": r[1], "email": r[2]} for r in rows]


@app.post("/api/babies/{baby_id}/access", tags=["Baby access"])
async def grant_baby_access(baby_id: int, request: Request):
    if (denied := await require_access(request, baby_id, ROLE_OWNER)) is not None:
        return denied
    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    role = body.get("role") or ROLE_VIEWER
    if role not in ROLE_RANK:
        return JSONResponse({"error": "invalid role"}, status_code=400)
    async with Session.begin() as session:
        user = await session.scalar(select(User).where(User.username == email))
        if user is None:
            return JSONResponse({"error": "no such user"}, status_code=404)
        existing = await session.get(BabyAccess, (user.id, baby_id))
        if existing is not None:
            existing.role = role
        else:
            session.add(BabyAccess(user_id=user.id, baby_id=baby_id, role=role))
    return {"ok": True}


@app.delete("/api/babies/{baby_id}/access/{user_id}", tags=["Baby access"])
async def revoke_baby_access(baby_id: int, user_id: int, request: Request):
    if (denied := await require_access(request, baby_id, ROLE_OWNER)) is not None:
        return denied
    async with Session.begin() as session:
        owners = (
            await session.scalars(
                select(BabyAccess).where(
                    BabyAccess.baby_id == baby_id, BabyAccess.role == ROLE_OWNER
                )
            )
        ).all()
        if len(owners) <= 1 and any(o.user_id == user_id for o in owners):
            return JSONResponse(
                {"error": "a baby needs at least one owner"}, status_code=400
            )
        await session.execute(
            delete(BabyAccess).where(
                BabyAccess.baby_id == baby_id, BabyAccess.user_id == user_id
            )
        )
    return {"ok": True}


async def _open_entry(entry_type: str, baby_id: int):
    """Most recent entry of this type without an end time, if any."""
    async with Session() as session:
        entry = await session.scalar(
            entries_of(baby_id)
            .where(Entry.type == entry_type, Entry.ts_end.is_(None))
            .order_by(Entry.ts_start.desc())
            .limit(1)
        )
    return row_to_dict(entry) if entry else None


@app.get("/api/sleep/open", tags=["Entries"])
async def get_open_sleep(request: Request, baby_id: int = DEFAULT_BABY_ID):
    if (denied := await require_access(request, baby_id, ROLE_VIEWER)) is not None:
        return denied
    return await _open_entry("sleep", baby_id)


@app.get("/api/walk/open", tags=["Entries"])
async def get_open_walk(request: Request, baby_id: int = DEFAULT_BABY_ID):
    if (denied := await require_access(request, baby_id, ROLE_VIEWER)) is not None:
        return denied
    return await _open_entry("walk", baby_id)


@app.delete("/api/entries/{entry_id}", tags=["Entries"])
async def delete_entry(entry_id: int, request: Request):
    async with Session() as session:
        existing = await session.get(Entry, entry_id)
    if existing is None:
        return {"ok": True}
    if (
        denied := await require_access(request, existing.baby_id, ROLE_EDITOR)
    ) is not None:
        return denied
    async with Session.begin() as session:
        await session.execute(delete(Entry).where(Entry.id == entry_id))
    await broadcast_event("entries_changed")
    return {"ok": True}


@app.get("/api/stats", tags=["Stats"])
async def get_stats(
    request: Request, date: str | None = None, baby_id: int = DEFAULT_BABY_ID
):
    if (denied := await require_access(request, baby_id, ROLE_VIEWER)) is not None:
        return denied
    day = date or utc_now().astimezone(HOUSEHOLD_TZ).strftime("%Y-%m-%d")
    async with Session() as session:
        rows = (
            await session.scalars(
                entries_of(baby_id).order_by(Entry.ts_start.desc()).limit(500)
            )
        ).all()
        day_rows = (
            await session.scalars(
                entries_of(baby_id)
                .where(on_local_day(Entry.ts_start, day))
                .order_by(Entry.ts_start.asc())
            )
        ).all()
        growth_rows = (
            await session.scalars(
                entries_of(baby_id)
                .where(Entry.type == "weight")
                .order_by(Entry.ts_start.asc())
            )
        ).all()
    entries = [row_to_dict(r) for r in rows]
    day_entries = [row_to_dict(r) for r in day_rows]
    growth = [
        {"time": e["ts_start"], "weight": m.get("weight"), "height": m.get("height")}
        for e in (row_to_dict(r) for r in growth_rows)
        if (m := e["meta"] or {}) and (m.get("weight") or m.get("height"))
    ]

    last = {}
    for e in entries:
        t = e["type"]
        if t not in last:
            last[t] = e
        if t in ("nursing", "bottle") and "feeding" not in last:
            last["feeding"] = e

    sleep_entries = [e for e in entries if e["type"] == "sleep" and e["ts_end"]][:10]
    sleep_durations = []
    for e in sleep_entries:
        start = parse_entry_ts(e["ts_start"])
        end = parse_entry_ts(e["ts_end"])
        assert start is not None and end is not None
        dur = (end - start).total_seconds() / 60
        sleep_durations.append(
            {"start": e["ts_start"], "end": e["ts_end"], "minutes": round(dur)}
        )

    # Night sleep runs for hours and would dominate a nap average; keep
    # the two separate rather than let one long stretch skew the other.
    naps = [s for s in sleep_durations if s["minutes"] < NIGHT_SLEEP_MIN_MINUTES]
    avg_sleep_min = (
        round(sum(s["minutes"] for s in naps) / len(naps)) if naps else None
    )
    # Awake time between two of those same sleeps, chronologically adjacent —
    # sleep_entries is newest-first, so sort before taking consecutive gaps.
    chrono = sorted(sleep_entries, key=lambda e: e["ts_start"])
    awake_gaps = []
    for prev, nxt in zip(chrono, chrono[1:]):
        prev_end = parse_entry_ts(prev["ts_end"])
        next_start = parse_entry_ts(nxt["ts_start"])
        assert prev_end is not None and next_start is not None
        gap = (next_start - prev_end).total_seconds() / 60
        if gap > 0:
            awake_gaps.append(gap)
    avg_awake_min = round(sum(awake_gaps) / len(awake_gaps)) if awake_gaps else None

    intervals = {}
    for typ in ["diaper", "feeding"]:
        if typ == "feeding":
            typed = [e for e in day_entries if e["type"] in ("nursing", "bottle")]
        else:
            typed = [e for e in day_entries if e["type"] == typ]
        if len(typed) >= 2:
            diffs = []
            for i in range(len(typed) - 1):
                a = parse_entry_ts(typed[i]["ts_start"])
                b = parse_entry_ts(typed[i + 1]["ts_start"])
                assert a is not None and b is not None
                diffs.append(round((b - a).total_seconds() / 60))
            intervals[typ] = {
                "last": diffs[-1],
                "avg": round(sum(diffs) / len(diffs)),
            }

    return {
        "last": last,
        "sleep_durations": sleep_durations,
        "avg_sleep_min": avg_sleep_min,
        "avg_awake_min": avg_awake_min,
        "intervals": intervals,
        "growth": growth,
    }


# ── Export report ──
async def fetch_entries_range(start: str, end: str, baby_id: int = DEFAULT_BABY_ID):
    if start > end:
        start, end = end, start
    # Inclusive range of local days: from the first day's opening instant
    # to the last day's closing one.
    lo_bounds = local_day_bounds(start)
    hi_bounds = local_day_bounds(end)
    if lo_bounds is None or hi_bounds is None:
        return [], start, end
    async with Session() as session:
        rows = (
            await session.scalars(
                entries_of(baby_id)
                .where(Entry.ts_start >= lo_bounds[0], Entry.ts_start < hi_bounds[1])
                .order_by(Entry.ts_start.asc())
            )
        ).all()
    return [row_to_dict(r) for r in rows], start, end


def build_report(entries: list[dict], start: str, end: str) -> dict:
    days: dict[str, dict] = {}
    totals = {
        "diaper": 0, "diaper_wet": 0, "diaper_dirty": 0,
        "feeding": 0, "feeding_ml": 0,
        "sleep_count": 0, "sleep_min": 0,
        "walk_count": 0, "walk_min": 0,
        "notes": 0,
    }
    weights = []

    def day_bucket(d):
        return days.setdefault(d, {
            "date": d, "diaper": 0, "diaper_wet": 0, "diaper_dirty": 0,
            "feeding": 0, "feeding_ml": 0, "sleep_min": 0, "walk_min": 0,
            "walk_count": 0,
        })

    for e in entries:
        d = local_day_of(e["ts_start"])
        bucket = day_bucket(d)
        t = e["type"]
        m = e["meta"] or {}
        if t == "diaper":
            bucket["diaper"] += 1
            totals["diaper"] += 1
            dt = m.get("diaper_type", "")
            if dt in ("nass", "wet", "beides", "both"):
                bucket["diaper_wet"] += 1
                totals["diaper_wet"] += 1
            if dt in ("schmutzig", "dirty", "beides", "both"):
                bucket["diaper_dirty"] += 1
                totals["diaper_dirty"] += 1
        elif t in ("nursing", "bottle"):
            bucket["feeding"] += 1
            totals["feeding"] += 1
            if t == "bottle" and m.get("amount"):
                ml = int(m["amount"])
                bucket["feeding_ml"] += ml
                totals["feeding_ml"] += ml
        elif t == "sleep" and e["ts_end"]:
            e_end = parse_entry_ts(e["ts_end"])
            e_start = parse_entry_ts(e["ts_start"])
            assert e_end is not None and e_start is not None
            mins = round((e_end - e_start).total_seconds() / 60)
            bucket["sleep_min"] += mins
            totals["sleep_min"] += mins
            totals["sleep_count"] += 1
        elif t == "walk" and e["ts_end"]:
            e_end = parse_entry_ts(e["ts_end"])
            e_start = parse_entry_ts(e["ts_start"])
            assert e_end is not None and e_start is not None
            mins = round((e_end - e_start).total_seconds() / 60)
            bucket["walk_min"] += mins
            bucket["walk_count"] += 1
            totals["walk_min"] += mins
            totals["walk_count"] += 1
        elif t == "weight" and m.get("weight"):
            try:
                weight = float(m["weight"])
            except (TypeError, ValueError):
                pass
            else:
                weights.append(
                    {
                        "time": e["ts_start"],
                        "shown": (
                            f'{local_day_of(e["ts_start"])} '
                            f'{local_time_of(e["ts_start"])}'
                        ),
                        "weight": weight,
                    }
                )
        elif t == "note" and e.get("note"):
            totals["notes"] += 1

    weight_change = None
    if len(weights) >= 2:
        weight_change = float(weights[-1]["weight"]) - float(weights[0]["weight"])

    for e in entries:
        e["shown_start"] = local_time_of(e["ts_start"])
        e["shown_end"] = local_time_of(e["ts_end"]) if e["ts_end"] else ""

    entries_by_day = [
        {"date": d, "day_entries": list(items)}
        for d, items in groupby(entries, key=lambda e: local_day_of(e["ts_start"]))
    ]

    return {
        "start": start,
        "end": end,
        "days": sorted(days.values(), key=lambda d: d["date"]),
        "totals": totals,
        "weights": weights,
        "weight_change": weight_change,
        "entries_by_day": entries_by_day,
        "has_entries": bool(entries),
    }


@app.get("/report", response_class=HTMLResponse)
async def report(
    request: Request, start: str, end: str, baby_id: int = DEFAULT_BABY_ID
):
    if await require_access(request, baby_id, ROLE_VIEWER) is not None:
        return HTMLResponse("Forbidden", status_code=403)
    entries, start, end = await fetch_entries_range(start, end, baby_id)
    data = build_report(entries, start, end)
    return templates.TemplateResponse(
        "report.html", {"request": request, "v": ASSET_VERSION, **data}
    )


@app.get("/api/export.csv", tags=["Export"])
async def export_csv(
    request: Request, start: str, end: str, baby_id: int = DEFAULT_BABY_ID
):
    if (denied := await require_access(request, baby_id, ROLE_VIEWER)) is not None:
        return denied
    entries, start, end = await fetch_entries_range(start, end, baby_id)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "type", "start", "end", "note", "meta", "ip"])
    for e in entries:
        w.writerow(
            [
                e["id"],
                e["type"],
                e["ts_start"],
                e["ts_end"] or "",
                e["note"] or "",
                json.dumps(e["meta"]),
                e["ip"] or "",
            ]
        )
    filename = f"infabula-{start}_{end}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
