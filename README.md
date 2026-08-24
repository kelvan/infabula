# infabula 🍼

Simple baby journal as a local web application.

## Setup

```bash
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8080
```

Open in browser: `http://localhost:8080`
From other devices on LAN: `http://<server-ip>:8080`

## Features

- **Diaper** – time + type (wet/dirty/both)
- **Nursing** – start/end + side
- **Bottle** – time + amount (ml) + content
- **Sleep** – fell asleep/woke up → automatic duration, blocked from starting twice
- **Walk** – started/back → automatic duration, blocked from starting twice
- **Clothing change** – time + note
- **Weight** – time + grams
- **Mood** – happy/neutral/fussy/crying, shown as an emoji marker
- **Note** – free text

Click any entry in the log to edit it. Multiple devices/tabs stay in sync live (SSE) — no reload needed. The log can be viewed as a list or as a day timeline (sleep/walk as bars, feeding/diaper as lines, mood as emoji), with the view choice remembered across reloads.

## Stats

- Last event per type + "X ago", with combined Feeding (nursing + bottle)
- Awake/back-since duration while sleep or a walk is ongoing or just finished
- Intervals between diapers / feedings (last + average)
- Sleep duration bar chart (last 10 sleeps)
- IP colors: each device on the network gets its own color automatically; name them in Settings
- Export a report or CSV for today / this week / this month / a custom range

## Settings

Assign a name to each device's IP address — the log legend and colors group by name instead of raw IP once set. Hover an entry's color dot to see which IP made it.

Set the baby's name and birthday; a banner marks the birthday and month-days once set.

## Data

Set the database with the `DB_URL` env var — SQLite, PostgreSQL and MariaDB/MySQL are supported:

```bash
DB_URL=sqlite:///infabula.db
DB_URL=postgresql://user:pass@host/infabula   # needs: uv sync --extra postgres
DB_URL=mysql://user:pass@host/infabula        # needs: uv sync --extra mysql
```

Defaults to SQLite; the older `DB_PATH` var still works and maps to a SQLite file. The schema is managed by Alembic and migrated automatically on startup — a database from before Alembic was introduced is adopted as-is, not re-created. On SQLite a timestamped backup is written to a `backups/` folder next to the database on every startup.

Entries belong to a baby and record who created them, and `baby_access` grants users an `owner`/`editor`/`viewer` role on a baby's log so several people can share one. None of that is exposed yet: there is no sign-in, and the app works against a single placeholder user and baby.

## Podman/Docker (optional)

```bash
podman build -t infabula .
podman run -p 8080:8080 -v ./data:/app/data -e DB_PATH=/app/data/infabula.db infabula
```
