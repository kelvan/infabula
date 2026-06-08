# infabula 🍼

Simple baby journal as a local web application.

## Setup

```bash
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8080
```

Open in browser: http://localhost:8080
From other devices on LAN: http://<server-ip>:8080

## Features

- **Diaper** – time + type (wet/dirty/both)
- **Nursing** – start/end + side
- **Bottle** – time + amount (ml) + content
- **Sleep** – fell asleep/woke up → automatic duration
- **Weight** – time + grams
- **Note** – free text

## Stats

- Last event per type + "X minutes ago"
- Intervals between diapers / nursing / bottles (last + average)
- Sleep duration bar chart (last 10 sleeps)
- IP colors: each device on the network gets its own color automatically

## Data

SQLite database, path configurable via env var `DB_PATH` (default: `infabula.db` in the current directory).

## Podman/Docker (optional)

```bash
podman build -t infabula .
podman run -p 8080:8080 -v ./data:/app/data -e DB_PATH=/app/data/infabula.db infabula
```
