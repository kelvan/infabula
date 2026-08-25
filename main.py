import asyncio
import csv
import io
import json
import os
import sqlite3
import time
from datetime import datetime
from itertools import groupby

from fastapi import FastAPI, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, distinct, func, select
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
from db import (
    DEFAULT_BABY_ID,
    ROLE_EDITOR,
    ROLE_OWNER,
    ROLE_VIEWER,
    Baby,
    BabyAccess,
    Entry,
    IpName,
    Session,
    Setting,
    User,
    WebauthnCredential,
    sqlite_file,
)
from migrate import run_migrations

app = FastAPI()
ASSET_VERSION = str(int(time.time()))

# ts_start/ts_end hold 'YYYY-MM-DDTHH:MM'; substr is the portable way to get
# the date part across SQLite, PostgreSQL and MariaDB.
DAY_START = func.substr(Entry.ts_start, 1, 10)
DAY_END = func.substr(Entry.ts_end, 1, 10)

ROLE_RANK = {ROLE_VIEWER: 0, ROLE_EDITOR: 1, ROLE_OWNER: 2}


def entries_of(baby_id: int = DEFAULT_BABY_ID):
    """Base query scoped to one baby's log."""
    return select(Entry).where(Entry.baby_id == baby_id)


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

# ── SSE pub-sub ──
subscribers: set[asyncio.Queue] = set()


async def broadcast_event(event_type: str):
    for q in list(subscribers):
        q.put_nowait(event_type)


@app.get("/api/events")
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
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
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


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if await auth.get_session_user(request) is not None:
        return RedirectResponse("/")
    return templates.TemplateResponse(
        "login.html", {"request": request, "v": ASSET_VERSION}
    )


def user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.username,
        "name": user.name,
        "totp_enabled": user.totp_enabled,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
    }


@app.post("/api/auth/register")
async def register(request: Request, response: Response):
    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    if not auth.is_valid_email(email) or len(password) < 8:
        return JSONResponse(
            {"error": "a valid email and an 8+ character password are required"},
            status_code=400,
        )
    async with Session.begin() as session:
        existing = await session.scalar(select(User).where(User.username == email))
        if existing is not None:
            return JSONResponse({"error": "email already registered"}, status_code=409)
        user = User(
            name=email,
            username=email,
            email=email,
            password_hash=auth.hash_password(password),
            last_login_at=auth.now_str(),
        )
        session.add(user)
        await session.flush()
        user_id = user.id
    token = await auth.create_session(user_id)
    auth.set_session_cookie(response, token)
    return {"ok": True}


@app.post("/api/auth/login")
async def login(request: Request, response: Response):
    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    async with Session() as session:
        user = await session.scalar(select(User).where(User.username == email))
    password_ok = auth.verify_password(password, user.password_hash if user else None)
    if user is None or not password_ok:
        return JSONResponse({"error": "invalid credentials"}, status_code=401)
    if user.totp_enabled:
        pending_token = auth.store_pending("totp_login", {"user_id": user.id})
        return {"totp_required": True, "pending_token": pending_token}
    await auth.touch_last_login(user.id)
    token = await auth.create_session(user.id)
    auth.set_session_cookie(response, token)
    return {"ok": True}


@app.post("/api/auth/totp/verify")
async def totp_verify_login(request: Request, response: Response):
    body = await request.json()
    pending_token = body.get("pending_token") or ""
    pending = auth.peek_pending(pending_token, "totp_login")
    if pending is None:
        return JSONResponse({"error": "expired, log in again"}, status_code=400)
    async with Session() as session:
        user = await session.get(User, pending["user_id"])
    if user is None or not auth.verify_totp(user.totp_secret, body.get("code") or ""):
        return JSONResponse({"error": "invalid code"}, status_code=401)
    auth.pop_pending(pending_token, "totp_login")
    await auth.touch_last_login(user.id)
    token = await auth.create_session(user.id)
    auth.set_session_cookie(response, token)
    return {"ok": True}


@app.post("/api/auth/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get(auth.SESSION_COOKIE)
    if token:
        await auth.delete_session(token)
    auth.clear_session_cookie(response)
    return {"ok": True}


@app.get("/api/auth/me")
async def me(request: Request):
    return user_to_dict(request.state.user)


@app.post("/api/auth/totp/setup")
async def totp_setup(request: Request):
    secret = auth.new_totp_secret()
    async with Session.begin() as session:
        user = await session.get(User, request.state.user.id)
        user.totp_secret = secret
        user.totp_enabled = False
        username = user.username
    uri = auth.totp_uri(secret, username)
    return {"secret": secret, "qr_svg": auth.totp_qr_svg(uri)}


@app.post("/api/auth/totp/confirm")
async def totp_confirm(request: Request):
    body = await request.json()
    async with Session.begin() as session:
        user = await session.get(User, request.state.user.id)
        if not user.totp_secret or not auth.verify_totp(
            user.totp_secret, body.get("code") or ""
        ):
            return JSONResponse({"error": "invalid code"}, status_code=400)
        user.totp_enabled = True
    return {"ok": True}


@app.post("/api/auth/totp/disable")
async def totp_disable(request: Request):
    body = await request.json()
    async with Session.begin() as session:
        user = await session.get(User, request.state.user.id)
        ok = auth.verify_password(body.get("password") or "", user.password_hash or "")
        if not ok:
            return JSONResponse({"error": "wrong password"}, status_code=401)
        user.totp_enabled = False
        user.totp_secret = None
    return {"ok": True}


@app.get("/api/auth/passkeys")
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


@app.delete("/api/auth/passkeys/{cred_id}")
async def delete_passkey(cred_id: int, request: Request):
    async with Session.begin() as session:
        cred = await session.get(WebauthnCredential, cred_id)
        if cred is not None and cred.user_id == request.state.user.id:
            await session.delete(cred)
    return {"ok": True}


@app.post("/api/auth/passkey/register/options")
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


@app.post("/api/auth/passkey/register/verify")
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


@app.post("/api/auth/passkey/login/options")
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


@app.post("/api/auth/passkey/login/verify")
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
    async with Session.begin() as session:
        row = await session.get(WebauthnCredential, stored.id)
        row.sign_count = verification.new_sign_count
    await auth.touch_last_login(stored.user_id)
    token = await auth.create_session(stored.user_id)
    auth.set_session_cookie(response, token)
    return {"ok": True}


@app.post("/api/entries")
async def create_entry(request: Request, baby_id: int = DEFAULT_BABY_ID):
    if (denied := await require_access(request, baby_id, ROLE_EDITOR)) is not None:
        return denied
    body = await request.json()
    entry = Entry(
        type=body["type"],
        ts_start=body["ts_start"],
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


@app.patch("/api/entries/{entry_id}")
async def patch_entry(entry_id: int, request: Request):
    async with Session() as session:
        existing = await session.get(Entry, entry_id)
    if existing is None:
        return None
    if (
        denied := await require_access(request, existing.baby_id, ROLE_EDITOR)
    ) is not None:
        return denied
    body = await request.json()
    async with Session.begin() as session:
        entry = await session.get(Entry, entry_id)
        for field in ("ts_start", "ts_end", "note", "meta"):
            if field in body:
                setattr(entry, field, body[field])
    await broadcast_event("entries_changed")
    return row_to_dict(entry)


@app.get("/api/entries")
async def get_entries(
    request: Request, date: str = None, limit: int = 300, baby_id: int = DEFAULT_BABY_ID
):
    if (denied := await require_access(request, baby_id, ROLE_VIEWER)) is not None:
        return denied
    async with Session() as session:
        stmt = entries_of(baby_id).order_by(Entry.ts_start.desc())
        if date:
            stmt = stmt.where((DAY_START == date) | (DAY_END == date))
        else:
            stmt = stmt.limit(limit)
        rows = (await session.scalars(stmt)).all()
    return [row_to_dict(r) for r in rows]


@app.get("/api/entries/dates")
async def get_dates(request: Request, baby_id: int = DEFAULT_BABY_ID):
    """Return list of distinct dates that have entries."""
    if (denied := await require_access(request, baby_id, ROLE_VIEWER)) is not None:
        return denied
    async with Session() as session:
        rows = (
            await session.scalars(
                select(distinct(DAY_START))
                .where(Entry.baby_id == baby_id)
                .order_by(DAY_START.desc())
                .limit(90)
            )
        ).all()
    return list(rows)


@app.get("/api/ip-names")
async def get_ip_names():
    async with Session() as session:
        rows = (await session.scalars(select(IpName))).all()
    return {r.ip: r.name for r in rows}


@app.put("/api/ip-names/{ip}")
async def set_ip_name(ip: str, request: Request):
    body = await request.json()
    name = (body.get("name") or "").strip()
    async with Session.begin() as session:
        row = await session.get(IpName, ip)
        if not name:
            if row is not None:
                await session.delete(row)
        elif row is None:
            session.add(IpName(ip=ip, name=name))
        else:
            row.name = name
    await broadcast_event("entries_changed")
    return {"ok": True}


@app.get("/api/settings")
async def get_settings():
    async with Session() as session:
        rows = (await session.scalars(select(Setting))).all()
    return {r.key: r.value for r in rows}


@app.put("/api/settings/{key}")
async def set_setting(key: str, request: Request):
    body = await request.json()
    value = (body.get("value") or "").strip()
    async with Session.begin() as session:
        row = await session.get(Setting, key)
        if not value:
            if row is not None:
                await session.delete(row)
        elif row is None:
            session.add(Setting(key=key, value=value))
        else:
            row.value = value
    await broadcast_event("entries_changed")
    return {"ok": True}


def baby_to_dict(baby: Baby) -> dict:
    return {"id": baby.id, "name": baby.name, "birthday": baby.birthday or ""}


@app.get("/api/babies")
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


@app.post("/api/babies")
async def create_baby(request: Request):
    body = await request.json()
    name = (body.get("name") or "").strip() or "Baby"
    birthday = (body.get("birthday") or "").strip() or None
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


@app.put("/api/babies/{baby_id}")
async def update_baby(baby_id: int, request: Request):
    if (denied := await require_access(request, baby_id, ROLE_EDITOR)) is not None:
        return denied
    body = await request.json()
    async with Session.begin() as session:
        baby = await session.get(Baby, baby_id)
        if baby is None:
            return {"ok": False}
        if "name" in body:
            baby.name = (body.get("name") or "").strip() or baby.name
        if "birthday" in body:
            baby.birthday = (body.get("birthday") or "").strip() or None
    await broadcast_event("entries_changed")
    return {"ok": True}


@app.delete("/api/babies/{baby_id}")
async def delete_baby(baby_id: int, request: Request):
    if (denied := await require_access(request, baby_id, ROLE_OWNER)) is not None:
        return denied
    async with Session.begin() as session:
        await session.execute(delete(Entry).where(Entry.baby_id == baby_id))
        await session.execute(delete(BabyAccess).where(BabyAccess.baby_id == baby_id))
        await session.execute(delete(Baby).where(Baby.id == baby_id))
    await broadcast_event("entries_changed")
    return {"ok": True}


@app.get("/api/babies/{baby_id}/access")
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


@app.post("/api/babies/{baby_id}/access")
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


@app.delete("/api/babies/{baby_id}/access/{user_id}")
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


@app.get("/api/ips")
async def get_known_ips(request: Request, baby_id: int = DEFAULT_BABY_ID):
    """Distinct IPs seen in entries, with their assigned name (if any)."""
    if (denied := await require_access(request, baby_id, ROLE_VIEWER)) is not None:
        return denied
    async with Session() as session:
        ips = (
            await session.scalars(
                select(distinct(Entry.ip))
                .where(Entry.ip.is_not(None), Entry.baby_id == baby_id)
                .order_by(Entry.ip)
            )
        ).all()
        name_rows = (await session.scalars(select(IpName))).all()
    names = {r.ip: r.name for r in name_rows}
    return [{"ip": ip, "name": names.get(ip, "")} for ip in ips]


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


@app.get("/api/sleep/open")
async def get_open_sleep(request: Request, baby_id: int = DEFAULT_BABY_ID):
    if (denied := await require_access(request, baby_id, ROLE_VIEWER)) is not None:
        return denied
    return await _open_entry("sleep", baby_id)


@app.get("/api/walk/open")
async def get_open_walk(request: Request, baby_id: int = DEFAULT_BABY_ID):
    if (denied := await require_access(request, baby_id, ROLE_VIEWER)) is not None:
        return denied
    return await _open_entry("walk", baby_id)


@app.delete("/api/entries/{entry_id}")
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


@app.get("/api/stats")
async def get_stats(request: Request, date: str = None, baby_id: int = DEFAULT_BABY_ID):
    if (denied := await require_access(request, baby_id, ROLE_VIEWER)) is not None:
        return denied
    day = date or datetime.now().strftime("%Y-%m-%d")
    async with Session() as session:
        rows = (
            await session.scalars(
                entries_of(baby_id).order_by(Entry.ts_start.desc()).limit(500)
            )
        ).all()
        day_rows = (
            await session.scalars(
                entries_of(baby_id)
                .where(DAY_START == day)
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
        start = datetime.fromisoformat(e["ts_start"])
        end = datetime.fromisoformat(e["ts_end"])
        dur = (end - start).total_seconds() / 60
        sleep_durations.append(
            {"start": e["ts_start"], "end": e["ts_end"], "minutes": round(dur)}
        )

    intervals = {}
    for typ in ["diaper", "feeding"]:
        if typ == "feeding":
            typed = [e for e in day_entries if e["type"] in ("nursing", "bottle")]
        else:
            typed = [e for e in day_entries if e["type"] == typ]
        if len(typed) >= 2:
            diffs = []
            for i in range(len(typed) - 1):
                a = datetime.fromisoformat(typed[i]["ts_start"])
                b = datetime.fromisoformat(typed[i + 1]["ts_start"])
                diffs.append(round((b - a).total_seconds() / 60))
            intervals[typ] = {
                "last": diffs[-1],
                "avg": round(sum(diffs) / len(diffs)),
            }

    return {
        "last": last,
        "sleep_durations": sleep_durations,
        "intervals": intervals,
        "growth": growth,
    }


# ── Export report ──
async def fetch_entries_range(start: str, end: str, baby_id: int = DEFAULT_BABY_ID):
    if start > end:
        start, end = end, start
    async with Session() as session:
        rows = (
            await session.scalars(
                entries_of(baby_id)
                .where(DAY_START.between(start, end))
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
        d = e["ts_start"][:10]
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
            mins = round(
                (datetime.fromisoformat(e["ts_end"]) - datetime.fromisoformat(e["ts_start"])).total_seconds() / 60
            )
            bucket["sleep_min"] += mins
            totals["sleep_min"] += mins
            totals["sleep_count"] += 1
        elif t == "walk" and e["ts_end"]:
            mins = round(
                (datetime.fromisoformat(e["ts_end"]) - datetime.fromisoformat(e["ts_start"])).total_seconds() / 60
            )
            bucket["walk_min"] += mins
            bucket["walk_count"] += 1
            totals["walk_min"] += mins
            totals["walk_count"] += 1
        elif t == "weight" and m.get("weight"):
            weights.append({"time": e["ts_start"], "weight": m["weight"]})
        elif t == "note" and e.get("note"):
            totals["notes"] += 1

    weight_change = weights[-1]["weight"] - weights[0]["weight"] if len(weights) >= 2 else None

    entries_by_day = [
        {"date": d, "day_entries": list(items)}
        for d, items in groupby(entries, key=lambda e: e["ts_start"][:10])
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


@app.get("/api/export.csv")
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
