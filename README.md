# infabula 🍼

Self-hosted, multi-user baby journal PWA for the household.

## Setup

```bash
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8080
```

Open in browser: `http://localhost:8080`
From other devices on LAN: `http://<server-ip>:8080`

## Tests

```bash
uv run pytest
```

Runs against a throwaway SQLite database with the migrations applied. The
suite pins `TZ=Europe/Vienna`, since which local day a UTC instant falls
on is exactly the sort of thing that only breaks on someone else's
machine.

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

Entries belong to a baby and record who created them, and multiple babies can be managed and switched between from the header. `baby_access` grants users an `owner`/`editor`/`viewer` role on a baby's log — an owner manages access from Settings → Baby → Manage access: grant, change a member's role, or revoke it. Whoever created the baby keeps permanent owner access there, so no other owner can lock them out.

## Accounts

Signing up is open by default — anyone who can reach the app can register with an email and password, but the account can't log in until it clicks a confirmation link sent to that address. Set `REGISTRATION_ENABLED=false` to close it entirely (existing accounts are unaffected, and it's still allowed from the LAN) — worth doing once the app is reachable from the internet. An admin can still bring in a new household member from anywhere with an invite, from Settings → Admin → Invites: optionally bind it to one email, share the one-time link, it expires after 7 days or first use, and can be revoked while still unused. Set these env vars to actually send the confirmation email:

```bash
SMTP_HOST=smtp.example.com
SMTP_PORT=587            # default
SMTP_USER=you@example.com
SMTP_PASSWORD=...
SMTP_FROM=infabula@example.com   # defaults to SMTP_USER
APP_BASE_URL=http://192.168.1.50:8080   # how the household reaches the app — used to build the link
```

Without `SMTP_HOST` set, the link is logged to stdout instead of emailed — fine for local dev, not for a real deployment, since nobody outside the server can ever verify. Accounts that existed before this was added are grandfathered in as already verified.

The same SMTP config sends a notice for other security-relevant changes, so one household member's account being touched is never silent to them: TOTP enabled/disabled, a passkey added, and baby access granted — the latter goes to both the new member and the owner who granted it.

Optional two-factor login is available per account, from Settings → Account:

- **TOTP** — scan the QR code into an authenticator app, confirm with a code.
- **Passkeys (WebAuthn)** — add one or more from the same tab. Passkeys need a secure context: they work on `localhost`, but over plain HTTP on a LAN IP most browsers will refuse the ceremony. Put a reverse proxy with TLS (e.g. Caddy) in front for passkeys to actually work outside of localhost.

Sessions are httponly cookies, valid 30 days, stored server-side so they can be revoked by logging out.

An account can delete itself from Settings → Account → Danger zone, with its password. Refused while it's the sole owner of a baby — transfer ownership or delete the baby first, so a journal is never silently lost. Its existing entries stay, with no author.

An admin account (the first account created is bootstrapped as one) can disable another account — instantly killing its sessions and API tokens, without touching its journal history — via the API:

```bash
GET  /api/admin/users
POST /api/admin/users/{id}/disable
POST /api/admin/users/{id}/enable
```

There's no admin page for this yet — authenticate as the admin account (cookie or bearer token) and call it directly, or from `/docs`.

### CLI

`manage.py` covers the same account management from the command line — useful for creating the first account (nobody can register their way to admin) or fixing a locked-out household member without going through the API:

```bash
uv run python manage.py create a@example.com --admin   # prompts for a password
uv run python manage.py list
uv run python manage.py disable a@example.com
uv run python manage.py enable a@example.com
uv run python manage.py set-admin a@example.com [--off]
uv run python manage.py set-password a@example.com
uv run python manage.py delete a@example.com           # refuses while sole owner of a baby
```

Run it against the deployed container so it shares the real database: `podman exec -it <container> uv run --no-sync python manage.py ...` (`--no-sync` skips re-resolving dependencies against the container's dev-less lockfile install).

## API

Every route documented at `/docs` (Swagger UI) or `/redoc`, both behind login like the rest of the app. Two ways to authenticate:

- **Session cookie** — what the browser uses; also works for scripting if you keep the cookie jar from a login request.
- **API tokens** — create one from Settings → Account → API tokens. Send it as `Authorization: Bearer <token>`; it grants the same access as the account that created it. The raw token is shown once, at creation, and can be revoked at any time.

## Podman/Docker (optional)

```bash
podman build -t infabula .
podman run -p 8080:8080 -v ./data:/app/data -e DB_PATH=/app/data/infabula.db infabula
```
