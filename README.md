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
- **Note** – free text

Click any entry in the log to edit it. Multiple devices/tabs stay in sync live (SSE) — no reload needed.

## Stats

- Last event per type + "X ago", with combined Feeding (nursing + bottle)
- Awake/back-since duration while sleep or a walk is ongoing or just finished
- Intervals between diapers / feedings (last + average)
- Sleep duration bar chart (last 10 sleeps)
- IP colors: each device on the network gets its own color automatically; name them in Settings

## Settings

Assign a name to each device's IP address — the log legend and colors group by name instead of raw IP once set. Hover an entry's color dot to see which IP made it.

## Data

SQLite database, path configurable via env var `DB_PATH` (default: `infabula.db` in the current directory). A timestamped backup is written to a `backups/` folder next to the database on every startup.

## Podman/Docker (optional)

```bash
podman build -t infabula .
podman run -p 8080:8080 -v ./data:/app/data -e DB_PATH=/app/data/infabula.db infabula
```
