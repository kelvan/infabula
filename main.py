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
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, distinct, func, select

from db import Entry, IpName, Session, Setting, sqlite_file
from migrate import run_migrations

app = FastAPI()
ASSET_VERSION = str(int(time.time()))

# ts_start/ts_end hold 'YYYY-MM-DDTHH:MM'; substr is the portable way to get
# the date part across SQLite, PostgreSQL and MariaDB.
DAY_START = func.substr(Entry.ts_start, 1, 10)
DAY_END = func.substr(Entry.ts_end, 1, 10)

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


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "v": ASSET_VERSION}
    )


@app.post("/api/entries")
async def create_entry(request: Request):
    body = await request.json()
    entry = Entry(
        type=body["type"],
        ts_start=body["ts_start"],
        ts_end=body.get("ts_end"),
        note=body.get("note", ""),
        meta=body.get("meta", {}),
        ip=get_client_ip(request),
    )
    async with Session.begin() as session:
        session.add(entry)
    await broadcast_event("entries_changed")
    return row_to_dict(entry)


@app.patch("/api/entries/{entry_id}")
async def patch_entry(entry_id: int, request: Request):
    body = await request.json()
    async with Session.begin() as session:
        entry = await session.get(Entry, entry_id)
        if entry is None:
            return None
        for field in ("ts_start", "ts_end", "note", "meta"):
            if field in body:
                setattr(entry, field, body[field])
    await broadcast_event("entries_changed")
    return row_to_dict(entry)


@app.get("/api/entries")
async def get_entries(date: str = None, limit: int = 300):
    async with Session() as session:
        stmt = select(Entry).order_by(Entry.ts_start.desc())
        if date:
            stmt = stmt.where((DAY_START == date) | (DAY_END == date))
        else:
            stmt = stmt.limit(limit)
        rows = (await session.scalars(stmt)).all()
    return [row_to_dict(r) for r in rows]


@app.get("/api/entries/dates")
async def get_dates():
    """Return list of distinct dates that have entries."""
    async with Session() as session:
        rows = (
            await session.scalars(
                select(distinct(DAY_START)).order_by(DAY_START.desc()).limit(90)
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


@app.get("/api/ips")
async def get_known_ips():
    """Distinct IPs seen in entries, with their assigned name (if any)."""
    async with Session() as session:
        ips = (
            await session.scalars(
                select(distinct(Entry.ip))
                .where(Entry.ip.is_not(None))
                .order_by(Entry.ip)
            )
        ).all()
        name_rows = (await session.scalars(select(IpName))).all()
    names = {r.ip: r.name for r in name_rows}
    return [{"ip": ip, "name": names.get(ip, "")} for ip in ips]


async def _open_entry(entry_type: str):
    """Most recent entry of this type without an end time, if any."""
    async with Session() as session:
        entry = await session.scalar(
            select(Entry)
            .where(Entry.type == entry_type, Entry.ts_end.is_(None))
            .order_by(Entry.ts_start.desc())
            .limit(1)
        )
    return row_to_dict(entry) if entry else None


@app.get("/api/sleep/open")
async def get_open_sleep():
    return await _open_entry("sleep")


@app.get("/api/walk/open")
async def get_open_walk():
    return await _open_entry("walk")


@app.delete("/api/entries/{entry_id}")
async def delete_entry(entry_id: int):
    async with Session.begin() as session:
        await session.execute(delete(Entry).where(Entry.id == entry_id))
    await broadcast_event("entries_changed")
    return {"ok": True}


@app.get("/api/stats")
async def get_stats(date: str = None):
    day = date or datetime.now().strftime("%Y-%m-%d")
    async with Session() as session:
        rows = (
            await session.scalars(
                select(Entry).order_by(Entry.ts_start.desc()).limit(500)
            )
        ).all()
        day_rows = (
            await session.scalars(
                select(Entry).where(DAY_START == day).order_by(Entry.ts_start.asc())
            )
        ).all()
    entries = [row_to_dict(r) for r in rows]
    day_entries = [row_to_dict(r) for r in day_rows]

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
    }


# ── Export report ──
async def fetch_entries_range(start: str, end: str):
    if start > end:
        start, end = end, start
    async with Session() as session:
        rows = (
            await session.scalars(
                select(Entry)
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
async def report(request: Request, start: str, end: str):
    entries, start, end = await fetch_entries_range(start, end)
    data = build_report(entries, start, end)
    return templates.TemplateResponse(
        "report.html", {"request": request, "v": ASSET_VERSION, **data}
    )


@app.get("/api/export.csv")
async def export_csv(start: str, end: str):
    entries, start, end = await fetch_entries_range(start, end)
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
