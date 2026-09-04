import asyncio
import csv
import io
import json
import logging
import math
import os
import re
import sqlite3
import statistics
import time
from datetime import date, datetime, timedelta, timezone
from datetime import time as dtime
from itertools import groupby
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import jinja2
from fastapi import FastAPI, Request, UploadFile
from fastapi.openapi.utils import get_openapi
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image, ImageOps
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
    Invite,
    Session,
    User,
    WebauthnCredential,
    sqlite_file,
)
from migrate import run_migrations

logger = logging.getLogger(__name__)

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

# Backed by the same volume the SQLite-era DB file used to live on — kept
# around after the Postgres migration specifically for uploads like this.
DATA_DIR = os.getenv("DATA_DIR", "data")
AVATAR_DIR = os.path.join(DATA_DIR, "avatars")
AVATAR_SIZE = 256
AVATAR_MAX_UPLOAD_BYTES = 8 * 1024 * 1024
os.makedirs(AVATAR_DIR, exist_ok=True)


def avatar_path(user_id: int) -> str:
    return os.path.join(AVATAR_DIR, f"{user_id}.webp")


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


def resolve_tz(name: str | None) -> ZoneInfo:
    """A caller-supplied IANA zone name, or the household zone as fallback."""
    if not name:
        return HOUSEHOLD_TZ
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return HOUSEHOLD_TZ


def local_day_bounds(day: str, tz: ZoneInfo = HOUSEHOLD_TZ) -> tuple[str, str] | None:
    """The [start, end) UTC instants covering a local calendar date.

    Built from both local midnights rather than start + 24h, so the short
    and long days either side of a DST switch come out right.
    """
    try:
        parsed = date.fromisoformat(day)
    except (TypeError, ValueError):
        return None
    lo = datetime.combine(parsed, dtime.min, tzinfo=tz)
    hi = datetime.combine(parsed + timedelta(days=1), dtime.min, tzinfo=tz)
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


def on_local_day(column, day: str, tz: ZoneInfo = HOUSEHOLD_TZ):
    """SQL predicate: this timestamp column falls on the given local date."""
    bounds = local_day_bounds(day, tz)
    if bounds is None:
        return sa_false()
    lo, hi = bounds
    return (column >= lo) & (column < hi)


ROLE_RANK = {ROLE_VIEWER: 0, ROLE_EDITOR: 1, ROLE_OWNER: 2}

# Mirrors QUICK_TYPE_KEYS in static/app.js.
QUICK_ACTION_TYPES = frozenset(
    {"diaper", "nursing", "bottle", "sleep", "walk", "clothing", "note", "mood"}
)

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

# Per-baby now (Baby.nap_threshold_min) — this is only the fallback for a
# baby row that somehow has none.
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
    """None if the current user is an admin with TOTP enabled, else a 403.

    An admin session grants far more than a normal account (every other
    household member's data, the ability to lock accounts out) — a bare
    password shouldn't be enough to reach it. Regular account use is
    unaffected; this only gates the admin endpoints.
    """
    user = request.state.user
    if not user.is_admin:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    if not user.totp_enabled:
        return JSONResponse(
            {"error": "admin access requires two-factor authentication"},
            status_code=403,
        )
    return None


async def shares_a_baby_with(viewer_id: int, target_id: int) -> bool:
    """Whether two accounts have overlapping access to at least one baby.

    Gates avatar viewing: a household member's photo shouldn't be fetchable
    by user id alone from an unrelated account on the same server.
    """
    if viewer_id == target_id:
        return True
    async with Session() as session:
        mine = set(
            (
                await session.scalars(
                    select(BabyAccess.baby_id).where(BabyAccess.user_id == viewer_id)
                )
            ).all()
        )
        if not mine:
            return False
        theirs = await session.scalar(
            select(func.count())
            .select_from(BabyAccess)
            .where(BabyAccess.user_id == target_id, BabyAccess.baby_id.in_(mine))
        )
    return bool(theirs)

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


@app.get("/sw.js", tags=["PWA"], include_in_schema=False)
async def service_worker():
    """Served from the root, not /static/: a service worker's default
    scope is the directory it's fetched from, and it has to cover the
    whole app to satisfy Chrome's install-eligibility check — /static/
    would only ever let it control static assets. Also deliberately
    uncached, unlike everything under /static/, so a future change to
    this file isn't stuck behind a year-long immutable cache.
    """
    return FileResponse(
        "sw.js",
        media_type="text/javascript",
        headers={"Cache-Control": "no-cache"},
    )


ICON_DIR = "static/icons"


@app.get("/manifest.json", tags=["PWA"], include_in_schema=False)
async def manifest():
    """Not served from /static/, and neither are the icons it points at.

    Everything under /static/ carries a year-long immutable cache, so
    once a browser (or Chrome's WebAPK minting server) has fetched the
    manifest or an icon, a redesign never reaches it. Here the manifest
    is uncached and every icon URL gets the asset version as a *path*
    segment — a genuinely new URL each deploy, which nothing anywhere
    can answer from a stale cache.
    """
    with open("manifest.json") as fh:
        data = json.load(fh)
    for entry in data.get("icons", []):
        name = entry["src"].rsplit("/", 1)[-1]
        entry["src"] = f"/app-icon/{ASSET_VERSION}/{name}"
    return JSONResponse(data, headers={"Cache-Control": "no-cache"})


@app.get("/app-icon/{version}/{name}", tags=["PWA"], include_in_schema=False)
async def app_icon(version: str, name: str):
    """PWA icons, keyed by asset version in the path (see manifest())."""
    if not re.fullmatch(r"icon-\d+\.png", name):
        return JSONResponse({"error": "not found"}, status_code=404)
    path = os.path.join(ICON_DIR, name)
    if not os.path.exists(path):
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(
        path, media_type="image/png", headers={"Cache-Control": "no-cache"}
    )
# auto_reload only matters for local dev — templates are baked into the
# image in production, so nothing ever changes underneath the process.
# Starlette 1.0 dropped passing Environment options through
# Jinja2Templates directly; a real Environment is required instead.
_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader("templates"),
    # Matches what Jinja2Templates(directory=...) used to set up on its
    # own — extension-based, not a blanket True, so anything that isn't
    # .html/.xml wouldn't get escaped when it shouldn't be.
    autoescape=jinja2.select_autoescape(),
    auto_reload=True,
)
templates = Jinja2Templates(env=_jinja_env)
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
PUBLIC_PREFIXES = ("/static/", "/app-icon/")
PUBLIC_PATHS = (
    "/login",
    "/sw.js",
    "/manifest.json",
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
        request, "index.html", {"v": ASSET_VERSION}
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
        request,
        "login.html",
        {
            "v": ASSET_VERSION,
            # An invite link has to render the register form even when
            # open signup is otherwise closed — actual validity of the
            # token itself is only checked at submission time.
            "registration_enabled": registration_allowed(request)
            or bool(request.query_params.get("invite")),
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
        "quick_actions": user.quick_actions,
        "has_avatar": os.path.exists(avatar_path(user.id)),
    }


async def send_verification_email(email: str, user_id: int) -> None:
    token = await auth.create_email_verification(user_id)
    await asyncio.to_thread(mailer.send_verification_email, email, token)


@app.post("/api/auth/register", tags=["Auth"])
async def register(request: Request):
    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    invite_token = (body.get("invite_token") or "").strip()
    if not auth.is_valid_email(email) or len(password) < 8:
        return JSONResponse(
            {"error": "a valid email and an 8+ character password are required"},
            status_code=400,
        )
    # An invite works even when registration_allowed() would say no —
    # that's the whole point of one: it's the explicit exception an
    # admin granted, not a second way to walk in unannounced.
    used_invite = bool(invite_token)
    inviter_id = None
    if used_invite:
        inviter_id = await auth.find_valid_invite(invite_token, email)
        if inviter_id is None:
            return JSONResponse({"error": "invalid or expired invite"}, status_code=400)
    elif not registration_allowed(request):
        return JSONResponse({"error": "registration is closed"}, status_code=403)
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
                invited_by=inviter_id,
            )
            session.add(user)
            await session.flush()
            user_id = user.id
    except IntegrityError:
        # A second registration for the same email landed between our
        # check and the insert; the unique constraint is the real guard.
        return JSONResponse({"error": "email already registered"}, status_code=409)
    if used_invite:
        await auth.consume_invite(invite_token, user_id)
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


@app.put("/api/auth/quick-actions", tags=["Auth"])
async def update_quick_actions(request: Request):
    body = await request.json()
    actions = body.get("quick_actions")
    if not isinstance(actions, list) or not all(
        isinstance(a, str) and a in QUICK_ACTION_TYPES for a in actions
    ):
        return JSONResponse({"error": "invalid quick actions"}, status_code=400)
    async with Session.begin() as session:
        user = await session.get(User, request.state.user.id)
        assert user is not None
        user.quick_actions = actions[:5]
    return {"ok": True}


@app.post("/api/auth/me/avatar", tags=["Auth"])
async def upload_avatar(request: Request, file: UploadFile):
    data = await file.read(AVATAR_MAX_UPLOAD_BYTES + 1)
    if len(data) > AVATAR_MAX_UPLOAD_BYTES:
        return JSONResponse({"error": "image too large"}, status_code=400)
    try:
        img = Image.open(io.BytesIO(data))
        # Format is read from the header alone; check it before the
        # decode below, which is where an exotic/rarely-fuzzed format's
        # decoder would actually run on attacker-controlled bytes.
        if img.format not in ("JPEG", "PNG", "WEBP", "GIF"):
            return JSONResponse({"error": "unsupported image format"}, status_code=400)
        img.load()
    except Exception:
        return JSONResponse({"error": "not a valid image"}, status_code=400)
    img = ImageOps.exif_transpose(img) or img
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "transparency" in img.info else "RGB")
    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.getchannel("A"))
        img = background
    img = ImageOps.fit(img, (AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)
    dest = avatar_path(request.state.user.id)
    tmp = dest + ".tmp"
    img.save(tmp, "WEBP", quality=85)
    os.replace(tmp, dest)
    return {"ok": True}


@app.delete("/api/auth/me/avatar", tags=["Auth"])
async def delete_avatar(request: Request):
    try:
        os.remove(avatar_path(request.state.user.id))
    except FileNotFoundError:
        pass
    return {"ok": True}


@app.get("/api/users/{user_id}/avatar", tags=["Auth"])
async def get_avatar(user_id: int, request: Request):
    if not await shares_a_baby_with(request.state.user.id, user_id):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    path = avatar_path(user_id)
    if not os.path.exists(path):
        return JSONResponse({"error": "no avatar"}, status_code=404)
    return FileResponse(
        path, media_type="image/webp", headers={"Cache-Control": "private, max-age=300"}
    )


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
        email = user.username
    if email:
        await asyncio.to_thread(mailer.send_totp_enabled_email, email)
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
        email = user.username
    if email:
        await asyncio.to_thread(mailer.send_totp_disabled_email, email)
    return {"ok": True}


# ── Admin ──
def admin_user_to_dict(user: User, email_by_id: dict[int, str]) -> dict:
    return {
        "id": user.id,
        "email": user.username,
        "name": user.name,
        "disabled": user.disabled,
        "is_admin": user.is_admin,
        "email_verified": user.email_verified,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
        "invited_by": email_by_id.get(user.invited_by) if user.invited_by else None,
    }


@app.get("/api/admin/users", tags=["Admin"])
async def admin_list_users(request: Request):
    if (denied := require_admin(request)) is not None:
        return denied
    async with Session() as session:
        rows = (
            await session.scalars(select(User).order_by(User.id))
        ).all()
        email_by_id = {u.id: u.username for u in rows if u.username}
    return [admin_user_to_dict(u, email_by_id) for u in rows]


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


@app.get("/api/admin/babies", tags=["Admin"])
async def admin_list_babies(request: Request):
    if (denied := require_admin(request)) is not None:
        return denied
    async with Session() as session:
        babies = (await session.scalars(select(Baby).order_by(Baby.id))).all()
        result = []
        for baby in babies:
            owners = (
                await session.scalars(
                    select(User.username)
                    .join(BabyAccess, BabyAccess.user_id == User.id)
                    .where(BabyAccess.baby_id == baby.id, BabyAccess.role == ROLE_OWNER)
                )
            ).all()
            result.append(
                {
                    "id": baby.id,
                    "name": baby.name,
                    "birthday": baby.birthday or "",
                    "created_at": baby.created_at,
                    "owners": list(owners),
                }
            )
    return result


def invite_to_dict(invite: Invite) -> dict:
    return {
        "id": invite.id,
        "prefix": invite.prefix,
        "email": invite.email,
        "created_at": invite.created_at,
        "expires_at": invite.expires_at,
        "used_at": invite.used_at,
    }


@app.get("/api/admin/invites", tags=["Admin"])
async def admin_list_invites(request: Request):
    if (denied := require_admin(request)) is not None:
        return denied
    async with Session() as session:
        rows = (
            await session.scalars(select(Invite).order_by(Invite.id.desc()))
        ).all()
    return [invite_to_dict(i) for i in rows]


@app.post("/api/admin/invites", tags=["Admin"])
async def admin_create_invite(request: Request):
    if (denied := require_admin(request)) is not None:
        return denied
    body = await request.json()
    email = (body.get("email") or "").strip().lower() or None
    if email and not auth.is_valid_email(email):
        return JSONResponse({"error": "invalid email"}, status_code=400)
    raw_token = await auth.create_invite(request.state.user.id, email)
    return {
        "token": raw_token,
        "link": f"{mailer.APP_BASE_URL}/login?invite={raw_token}",
    }


@app.delete("/api/admin/invites/{invite_id}", tags=["Admin"])
async def admin_revoke_invite(invite_id: int, request: Request):
    if (denied := require_admin(request)) is not None:
        return denied
    async with Session.begin() as session:
        invite = await session.get(Invite, invite_id)
        if invite is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        if invite.used_at is not None:
            return JSONResponse(
                {"error": "invite was already used"}, status_code=400
            )
        await session.delete(invite)
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
    passkey_name = (body.get("name") or "Passkey").strip()[:128]
    async with Session.begin() as session:
        session.add(
            WebauthnCredential(
                user_id=request.state.user.id,
                credential_id=bytes_to_base64url(verification.credential_id),
                public_key=bytes_to_base64url(verification.credential_public_key),
                sign_count=verification.sign_count,
                name=passkey_name,
            )
        )
    if request.state.user.username:
        await asyncio.to_thread(
            mailer.send_passkey_added_email, request.state.user.username, passkey_name
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
        logger.exception("passkey login verification failed")
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
            bounds = local_day_bounds(date)
            still_open_today = sa_false()
            if bounds is not None:
                # An open sleep/walk that started before today and hasn't
                # ended yet spans into today too — ts_start alone would
                # only ever place it on the day it started, never on the
                # days it's still ongoing through. Scoped to sleep/walk
                # specifically: every other type also leaves ts_end null
                # (it's simply unused for an instant entry), so without
                # this the clause below would match nearly every entry
                # ever logged, not just genuinely open ones.
                still_open_today = (
                    Entry.type.in_(("sleep", "walk"))
                    & Entry.ts_end.is_(None)
                    & (Entry.ts_start < bounds[1])
                )
            stmt = stmt.where(
                on_local_day(Entry.ts_start, date)
                | on_local_day(Entry.ts_end, date)
                | still_open_today
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
    return {
        "id": baby.id,
        "name": baby.name,
        "birthday": baby.birthday or "",
        "nap_threshold_min": baby.nap_threshold_min,
        "bottle_default_content": baby.bottle_default_content or "",
        "created_by": baby.created_by,
    }


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
        baby = Baby(name=name, birthday=birthday, created_by=request.state.user.id)
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
    if "nap_threshold_min" in body:
        threshold = body.get("nap_threshold_min")
        if not isinstance(threshold, int) or not (15 <= threshold <= 1440):
            return JSONResponse(
                {"error": "nap_threshold_min must be between 15 and 1440"},
                status_code=400,
            )
    if "bottle_default_content" in body:
        content = (body.get("bottle_default_content") or "").strip() or None
        if content not in (None, "abgepumpt", "formula"):
            return JSONResponse(
                {"error": "bottle_default_content must be abgepumpt, formula or empty"},
                status_code=400,
            )
    async with Session.begin() as session:
        baby = await session.get(Baby, baby_id)
        if baby is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        if "name" in body:
            baby.name = (body.get("name") or "").strip() or baby.name
        if "birthday" in body:
            baby.birthday = (body.get("birthday") or "").strip() or None
        if "nap_threshold_min" in body:
            baby.nap_threshold_min = body["nap_threshold_min"]
        if "bottle_default_content" in body:
            baby.bottle_default_content = (
                body.get("bottle_default_content") or ""
            ).strip() or None
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
    return [
        {
            "user_id": r[0],
            "role": r[1],
            "email": r[2],
            "has_avatar": os.path.exists(avatar_path(r[0])),
        }
        for r in rows
    ]


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
        baby = await session.get(Baby, baby_id)
        if baby is not None and baby.created_by == user.id and role != ROLE_OWNER:
            return JSONResponse(
                {"error": "cannot change the baby creator's role"}, status_code=400
            )
        existing = await session.get(BabyAccess, (user.id, baby_id))
        is_new_grant = existing is None
        if existing is not None:
            existing.role = role
        else:
            session.add(BabyAccess(user_id=user.id, baby_id=baby_id, role=role))
        baby_name = baby.name if baby is not None else ""
    if is_new_grant:
        if email:
            await asyncio.to_thread(
                mailer.send_access_granted_email, email, baby_name, role
            )
        actor_email = request.state.user.username
        if actor_email and actor_email != email:
            await asyncio.to_thread(
                mailer.send_access_granted_owner_notice_email,
                actor_email,
                baby_name,
                email,
                role,
            )
    return {"ok": True}


@app.delete("/api/babies/{baby_id}/access/{user_id}", tags=["Baby access"])
async def revoke_baby_access(baby_id: int, user_id: int, request: Request):
    if (denied := await require_access(request, baby_id, ROLE_OWNER)) is not None:
        return denied
    async with Session.begin() as session:
        baby = await session.get(Baby, baby_id)
        if baby is not None and baby.created_by == user_id:
            return JSONResponse(
                {"error": "cannot remove the baby creator's access"}, status_code=400
            )
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


# ── Typical-day rhythm ──
# Recurring sleep windows and bottle-feed slots, learned from history.
RHYTHM_WINDOW_DAYS = 28
RHYTHM_MIN_ENTRIES_PER_DAY = 3  # fewer and that day wasn't really tracked
RHYTHM_MIN_DAYS_OBSERVED = 3  # need this many looks at a minute to trust it
RHYTHM_SLEEP_PROB = 0.25  # asleep on >= this share of observed days
RHYTHM_SMOOTH_HALF_MIN = 40  # wide enough that scattered short naps add up
RHYTHM_MIN_WINDOW_MIN = 25  # drop typical-sleep runs shorter than this
RHYTHM_FEED_MERGE_GAP_MIN = 30  # bottles this close chain into one feed
RHYTHM_FEED_MIN_BOTTLES_PER_DAY = 2  # a 1-bottle day isn't a bottle-fed day
RHYTHM_FEED_PEAK_HALF_MIN = 45  # feeds within this add to a peak's height
RHYTHM_FEED_SLOT_HALF_MIN = 80  # min gap between slots; assignment radius
RHYTHM_FEED_MIN_DAYS = 3  # a feed slot must recur on >= this many days
RHYTHM_FEED_SLOT_SHARE = 0.5  # ...or this share of bottle-fed days, whichever more


def _local_dt(ts: str | None, tz: ZoneInfo) -> datetime | None:
    dt = parse_entry_ts(ts)
    return dt.astimezone(tz) if dt else None


def _hhmm(minute: float) -> str:
    m = int(round(minute)) % 1440
    return f"{m // 60:02d}:{m % 60:02d}"


def _local_midnight(day: str, tz: ZoneInfo) -> datetime:
    return datetime.fromisoformat(day).replace(tzinfo=tz)


def _days_touched(start: datetime, end: datetime) -> list[str]:
    days, d = [], start.date()
    while d <= end.date():
        days.append(d.isoformat())
        d += timedelta(days=1)
    return days


def _circ_dist(a: int, b: int, span: int = 1440) -> int:
    d = abs(a - b) % span
    return min(d, span - d)


def _circular_box_sum(vals: list[float], half: int) -> list[float]:
    n = len(vals)
    return [
        sum(vals[(i + k) % n] for k in range(-half, half + 1)) for i in range(n)
    ]


def _circular_smooth(vals: list[float | None], half: int) -> list[float | None]:
    n = len(vals)
    out: list[float | None] = [None] * n
    for i in range(n):
        got: list[float] = []
        for k in range(-half, half + 1):
            v = vals[(i + k) % n]
            if v is not None:
                got.append(v)
        if got:
            out[i] = sum(got) / len(got)
    return out


def _circular_runs(
    vals: list[float | None], threshold: float, min_len: int
) -> list[tuple[int, int, float]]:
    """Maximal circular runs where vals is defined and >= threshold.

    Returns (start_minute, end_minute_exclusive, mean_value); a run that
    wraps midnight comes back with end > 1440.
    """
    n = len(vals)
    hot = [v is not None and v >= threshold for v in vals]
    if all(hot):
        vv = [v for v in vals if v is not None]
        return [(0, n, sum(vv) / len(vv))]
    if not any(hot):
        return []
    start = next(i for i in range(n) if hot[i] and not hot[(i - 1) % n])
    runs: list[tuple[int, int, float]] = []
    i, seen = start, 0
    while seen < n:
        if hot[i % n]:
            j = i
            acc: list[float] = []
            while hot[j % n]:
                v = vals[j % n]
                assert v is not None
                acc.append(v)
                j += 1
                seen += 1
            if len(acc) >= min_len:
                runs.append((i % n, i % n + len(acc), sum(acc) / len(acc)))
            i = j
        else:
            i += 1
            seen += 1
    return runs


def compute_rhythm(
    entries: list[dict],
    tz: ZoneInfo,
    *,
    window_days: int = RHYTHM_WINDOW_DAYS,
    today: date | None = None,
) -> dict:
    """Typical sleep windows and bottle-feed slots across a day.

    Only days that look genuinely tracked are counted, and each minute is
    weighed only over the days that actually observed it — between that
    day's first and last entry, plus any span a sleep or walk brackets.
    A day with a couple of stray entries would otherwise read as "awake
    all afternoon" and drag every average toward nothing.
    """
    today = today or datetime.now(tz).date()
    window_start = today - timedelta(days=window_days - 1)

    by_day: dict[str, list[dict]] = {}
    for e in entries:
        start = _local_dt(e.get("ts_start"), tz)
        if start is None or not (window_start <= start.date() <= today):
            continue
        by_day.setdefault(start.date().isoformat(), []).append(e)

    usable = {
        day
        for day, items in by_day.items()
        if len(items) >= RHYTHM_MIN_ENTRIES_PER_DAY
    }
    result = {
        "window_days": window_days,
        "days_analyzed": len(usable),
        "days_skipped": len(by_day) - len(usable),
        "sleep": [],
        "feeds": [],
    }
    if not usable:
        return result

    observed = {d: [False] * 1440 for d in usable}
    asleep = {d: [False] * 1440 for d in usable}

    # base tracked window: first entry -> last entry (ts_end counted) each day
    for day in usable:
        ds = _local_midnight(day, tz)
        marks: list[float] = []
        for e in by_day[day]:
            s = _local_dt(e["ts_start"], tz)
            if s:
                marks.append((s - ds).total_seconds() / 60)
            en = _local_dt(e.get("ts_end"), tz)
            if en:
                marks.append(min((en - ds).total_seconds() / 60, 1440))
        lo = max(0, int(min(marks)))
        hi = min(1440, math.ceil(max(marks)) + 1)  # the last entry's minute counts
        for m in range(lo, hi):
            observed[day][m] = True

    # a sleep/walk that brackets a stretch means we observed it, even the
    # small hours before the first "fresh" entry of the day
    for e in entries:
        if e.get("type") not in ("sleep", "walk"):
            continue
        s = _local_dt(e["ts_start"], tz)
        en = _local_dt(e.get("ts_end"), tz)
        if s is None or en is None or en <= s:
            continue
        for day in _days_touched(s, en):
            if day not in usable:
                continue
            ds = _local_midnight(day, tz)
            m0 = max(0, int((s - ds).total_seconds() / 60))
            m1 = min(1440, math.ceil((en - ds).total_seconds() / 60))
            for m in range(m0, m1):
                observed[day][m] = True
                if e["type"] == "sleep":
                    asleep[day][m] = True

    obs_total = [0] * 1440
    asleep_total = [0] * 1440
    for day in usable:
        for m in range(1440):
            if observed[day][m]:
                obs_total[m] += 1
                if asleep[day][m]:
                    asleep_total[m] += 1

    prob: list[float | None] = [
        asleep_total[m] / obs_total[m]
        if obs_total[m] >= RHYTHM_MIN_DAYS_OBSERVED
        else None
        for m in range(1440)
    ]
    prob = _circular_smooth(prob, RHYTHM_SMOOTH_HALF_MIN)

    for lo, hi, avg in _circular_runs(
        prob, RHYTHM_SLEEP_PROB, RHYTHM_MIN_WINDOW_MIN
    ):
        run_min = [m % 1440 for m in range(lo, hi)]
        seen_on = sum(
            1 for day in usable if any(asleep[day][m] for m in run_min)
        )
        result["sleep"].append(
            {
                "start": _hhmm(lo),
                "end": _hhmm(hi),
                "prob": round(avg, 2),
                "days": seen_on,
            }
        )

    # ── bottle feeds ──
    # A day only counts here if it has at least a couple of bottles; a
    # single stray bottle on an otherwise breastfed day isn't a schedule.
    feed_days = {
        day
        for day in usable
        if sum(1 for e in by_day[day] if e.get("type") == "bottle")
        >= RHYTHM_FEED_MIN_BOTTLES_PER_DAY
    }
    events: list[tuple[int, float, str]] = []  # (minute_of_day, ml, day)
    for day in feed_days:
        ds = _local_midnight(day, tz)
        bottles: list[tuple[datetime, float]] = []
        for e in by_day[day]:
            if e.get("type") != "bottle":
                continue
            t = _local_dt(e["ts_start"], tz)
            if t is None:
                continue
            bottles.append((t, float((e.get("meta") or {}).get("amount") or 0)))
        bottles.sort()
        prev: datetime | None = None
        merged: list[list[float]] = []
        for t, ml in bottles:
            gap = (t - prev).total_seconds() / 60 if prev is not None else None
            if gap is not None and gap <= RHYTHM_FEED_MERGE_GAP_MIN:
                merged[-1][1] += ml
            else:
                merged.append([(t - ds).total_seconds() / 60, ml])
            prev = t
        for minute, ml in merged:
            events.append((int(minute) % 1440, ml, day))

    # cluster by peaks in the time-of-day histogram, not by chaining
    # neighbours — with a bottle every couple of hours, single-linkage
    # would swallow the whole day into one slot.
    counts = [0.0] * 1440
    for minute, _, _ in events:
        counts[minute] += 1.0
    density = _circular_box_sum(counts, RHYTHM_FEED_PEAK_HALF_MIN)
    slot_min_days = max(
        RHYTHM_FEED_MIN_DAYS, math.ceil(RHYTHM_FEED_SLOT_SHARE * len(feed_days))
    )
    floor = slot_min_days
    peaks: list[int] = []
    for m in sorted(range(1440), key=lambda i: -density[i]):
        if density[m] < floor:
            break
        if all(
            _circ_dist(m, p) > RHYTHM_FEED_SLOT_HALF_MIN for p in peaks
        ):
            peaks.append(m)

    slots: dict[int, dict] = {
        p: {"minutes": [], "mls": [], "days": set()} for p in peaks
    }
    for minute, ml, day in events:
        near = min(peaks, key=lambda p: _circ_dist(minute, p), default=None)
        if near is not None and _circ_dist(minute, near) <= RHYTHM_FEED_SLOT_HALF_MIN:
            s = slots[near]
            s["minutes"].append(minute)
            s["mls"].append(ml)
            s["days"].add(day)

    feeds = []
    for p in sorted(peaks):
        s = slots[p]
        if len(s["days"]) < slot_min_days:
            continue
        obs_days = sum(1 for day in feed_days if observed[day][p])
        feeds.append(
            {
                "time": _hhmm(statistics.median(s["minutes"])),
                "ml": round(statistics.mean(s["mls"])),
                "ml_low": round(min(s["mls"])),
                "ml_high": round(max(s["mls"])),
                "count": len(s["minutes"]),
                "days": len(s["days"]),
                "regularity": round(len(s["days"]) / obs_days, 2) if obs_days else None,
            }
        )
    result["feeds"] = sorted(feeds, key=lambda f: f["time"])
    return result


@app.get("/api/rhythm", tags=["Stats"])
async def get_rhythm(
    request: Request,
    days: int = RHYTHM_WINDOW_DAYS,
    tz: str | None = None,
    baby_id: int = DEFAULT_BABY_ID,
):
    """Typical sleep windows and bottle-feed times learned from history."""
    if (denied := await require_access(request, baby_id, ROLE_VIEWER)) is not None:
        return denied
    days = max(7, min(days, 90))
    zone = resolve_tz(tz)
    # reach a day past the window so a night sleep that started earlier
    # still contributes its small-hours coverage
    cutoff = datetime.now(zone).date() - timedelta(days=days + 1)
    cutoff_ts = to_entry_ts(datetime.combine(cutoff, dtime.min, tzinfo=zone))
    async with Session() as session:
        rows = (
            await session.scalars(
                entries_of(baby_id)
                .where(Entry.ts_start >= cutoff_ts)
                .order_by(Entry.ts_start.asc())
            )
        ).all()
    return compute_rhythm([row_to_dict(r) for r in rows], zone, window_days=days)


@app.get("/api/stats", tags=["Stats"])
async def get_stats(
    request: Request,
    date: str | None = None,
    tz: str | None = None,
    baby_id: int = DEFAULT_BABY_ID,
):
    if (denied := await require_access(request, baby_id, ROLE_VIEWER)) is not None:
        return denied
    # `tz` lets a non-browser client (e.g. Home Assistant) bucket "today" in
    # its own zone instead of the household one. Unknown names fall back.
    zone = resolve_tz(tz)
    day = date or utc_now().astimezone(zone).strftime("%Y-%m-%d")
    async with Session() as session:
        baby = await session.get(Baby, baby_id)
        nap_threshold_min = baby.nap_threshold_min if baby else NIGHT_SLEEP_MIN_MINUTES
        rows = (
            await session.scalars(
                entries_of(baby_id).order_by(Entry.ts_start.desc()).limit(500)
            )
        ).all()
        day_rows = (
            await session.scalars(
                entries_of(baby_id)
                .where(on_local_day(Entry.ts_start, day, zone))
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
        total_rows = (
            await session.execute(
                select(Entry.type, func.count())
                .where(Entry.baby_id == baby_id)
                .group_by(Entry.type)
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
    naps = [s for s in sleep_durations if s["minutes"] < nap_threshold_min]
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

    totals = {entry_type: count for entry_type, count in total_rows}

    return {
        "last": last,
        "sleep_durations": sleep_durations,
        "avg_sleep_min": avg_sleep_min,
        "avg_awake_min": avg_awake_min,
        "intervals": intervals,
        "growth": growth,
        "totals": totals,
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
        request, "report.html", {"v": ASSET_VERSION, **data}
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
