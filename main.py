import asyncio
import json
import os
import sqlite3
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
DB_PATH = os.getenv("DB_PATH", "infabula.db")

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


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            ts_start TEXT NOT NULL,
            ts_end TEXT,
            note TEXT,
            meta TEXT,
            ip TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


init_db()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates", auto_reload=True)
templates.env.cache = None


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def row_to_dict(r):
    d = dict(r)
    d["meta"] = json.loads(d["meta"] or "{}")
    return d


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/entries")
async def create_entry(request: Request):
    body = await request.json()
    ip = get_client_ip(request)
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO entries (type, ts_start, ts_end, note, meta, ip) VALUES (?, ?, ?, ?, ?, ?)",
        (
            body["type"],
            body["ts_start"],
            body.get("ts_end"),
            body.get("note", ""),
            json.dumps(body.get("meta", {})),
            ip,
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    row = conn.execute("SELECT * FROM entries WHERE id=?", (new_id,)).fetchone()
    conn.close()
    await broadcast_event("entries_changed")
    return row_to_dict(row)


@app.patch("/api/entries/{entry_id}")
async def patch_entry(entry_id: int, request: Request):
    body = await request.json()
    conn = get_db()
    if "ts_start" in body:
        conn.execute(
            "UPDATE entries SET ts_start=? WHERE id=?", (body["ts_start"], entry_id)
        )
    if "ts_end" in body:
        conn.execute(
            "UPDATE entries SET ts_end=? WHERE id=?", (body["ts_end"], entry_id)
        )
    if "note" in body:
        conn.execute("UPDATE entries SET note=? WHERE id=?", (body["note"], entry_id))
    if "meta" in body:
        conn.execute(
            "UPDATE entries SET meta=? WHERE id=?",
            (json.dumps(body["meta"]), entry_id),
        )
    conn.commit()
    row = conn.execute("SELECT * FROM entries WHERE id=?", (entry_id,)).fetchone()
    conn.close()
    await broadcast_event("entries_changed")
    return row_to_dict(row)


@app.get("/api/entries")
async def get_entries(date: str = None, limit: int = 300):
    conn = get_db()
    if date:
        rows = conn.execute(
            "SELECT * FROM entries WHERE date(ts_start)=? ORDER BY ts_start DESC",
            (date,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM entries ORDER BY ts_start DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


@app.get("/api/entries/dates")
async def get_dates():
    """Return list of distinct dates that have entries."""
    conn = get_db()
    rows = conn.execute(
        "SELECT DISTINCT date(ts_start) as d FROM entries ORDER BY d DESC LIMIT 90"
    ).fetchall()
    conn.close()
    return [r["d"] for r in rows]


@app.get("/api/sleep/open")
async def get_open_sleep():
    """Return the most recent sleep entry without ts_end, if any."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM entries WHERE type='sleep' AND ts_end IS NULL ORDER BY ts_start DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row:
        return row_to_dict(row)
    return None


@app.delete("/api/entries/{entry_id}")
async def delete_entry(entry_id: int):
    conn = get_db()
    conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
    await broadcast_event("entries_changed")
    return {"ok": True}


@app.get("/api/stats")
async def get_stats():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM entries ORDER BY ts_start DESC LIMIT 500"
    ).fetchall()
    conn.close()
    entries = [row_to_dict(r) for r in rows]

    last = {}
    for e in entries:
        t = e["type"]
        if t not in last:
            last[t] = e

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
    for typ in ["diaper", "bottle", "nursing"]:
        typed = [e for e in entries if e["type"] == typ]
        if len(typed) >= 2:
            diffs = []
            for i in range(len(typed) - 1):
                a = datetime.fromisoformat(typed[i]["ts_start"])
                b = datetime.fromisoformat(typed[i + 1]["ts_start"])
                diff_min = abs((a - b).total_seconds() / 60)
                diffs.append(round(diff_min))
            if diffs:
                intervals[typ] = {
                    "last": diffs[0],
                    "avg": round(sum(diffs[:5]) / len(diffs[:5])),
                }

    return {
        "last": last,
        "sleep_durations": sleep_durations,
        "intervals": intervals,
    }
