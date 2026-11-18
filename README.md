# infabula 🍼

Self-hosted, multi-user baby journal PWA for the household.

Built with [Claude Code](https://claude.com/claude-code) — nearly every line, commit, and word in this README was AI-generated, reviewed and directed by a human in the loop. It has not had an independent security audit. Read the code before you trust it with your household's data or expose it past your LAN.

## Quick start

Build and start the app in a container, then create the first account. Registration alone never grants admin rights, so the first account comes from the command line:

```bash
podman build -t infabula .
podman run -d --name infabula -p 8080:8080 \
  -v infabula-data:/app/data -e DB_PATH=/app/data/infabula.db \
  -e TZ=Europe/Vienna infabula
podman exec -it infabula uv run --no-sync python manage.py create you@example.com --admin
```

Open `http://localhost:8080`, log in, and add your baby's name and birthday when the app asks. Then tap the **+** button for a full entry, or the round quick buttons for a diaper, a mood or "fell asleep" in one tap. Set `TZ` to your own timezone: it decides which local day an entry belongs to.

Everyone else can register themselves, or you can send an invite from Settings → Admin. See [Accounts](#accounts) for email confirmation and two-factor login, and [Setup](#setup) to run without a container.

<p align="center">
  <img src="docs/screenshots/log.png" width="23%" alt="Log">
  <img src="docs/screenshots/timeline.png" width="23%" alt="Timeline">
  <img src="docs/screenshots/stats.png" width="23%" alt="Stats">
  <img src="docs/screenshots/settings.png" width="23%" alt="Settings">
</p>

## Setup

```bash
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8080
```

Open in browser: `http://localhost:8080`
From other devices on the LAN: `http://<server-ip>:8080`

## Tests

```bash
uv run pytest
```

The suite runs against a throwaway SQLite database with the migrations applied. It pins `TZ=Europe/Vienna`, because a UTC instant's local day depends on the timezone. This kind of bug shows up only on someone else's machine.

## Features

- **Diaper** — time and type (wet, dirty, or both)
- **Nursing** — start time, end time, and side
- **Bottle** — time, amount in ml, and content
- **Sleep** — "fell asleep" and "woke up" times, with automatic duration
- **Walk** — "started" and "back" times, with automatic duration
- **Clothing change** — time and note
- **Weight** — time and weight in grams
- **Mood** — happy, neutral, fussy, or crying, as an emoji marker
- **Note** — free text

The app blocks a second open sleep or walk entry while one is already open. Tap any entry in the log to edit it. All open devices and tabs stay in sync through server-sent events (SSE), so you do not need to reload the page. You can view the log as a list or as a timeline for one day. The timeline shows sleep and walks as bars, feeding and diaper changes as lines, and mood as emoji. The app remembers your view choice after a reload.

## Offline

Once you have opened the app with a network, it opens again without one and shows the log as it was at that point. A bar across the top says so, because a saved copy otherwise looks exactly like the current one.

You can keep logging while offline. A new entry is kept on the device, marked "not synced" in the log, and synced as soon as there is a network again — when the app is reopened, or within half a minute if it is already open. Tap the × on a waiting entry to drop it before it is synced. An entry carries the time it happened, so it lands where it belongs however late it arrives, and two phones logging at once need no reconciliation.

Editing and deleting still need the server, and are refused with "Offline — not saved". An entry the server rejects on sync (one logged more than seven days ago, say) is dropped with a notice rather than blocking the ones behind it. Logging out clears both the saved copy and anything still waiting, so the next person to pick up the phone cannot read it back.

## Stats

- Last event of each type, with time since it (for example "2h ago")
- Combined feeding stat: nursing and bottle together
- Awake time, or time since back from a walk, while it is open or just finished
- Time between diaper changes and feedings: last interval and average
- Bar chart of the last 10 sleep durations
- One color per device on the network, with names you assign in Settings
- Report or CSV export for today, this week, this month, or a custom date range

## Settings

Assign a name to each device's IP address in Settings. After you assign a name, the log legend and the colors use it instead of the raw IP address. Hover over an entry's color dot to see which IP address made it.

Set the baby's name and birthday in Settings. After you set the birthday, a banner marks the birthday and the matching day of each month.

Settings → Account → Logging turns the free-text note field on the add/edit dialogs on or off, per account. On by default. An entry that already carries a note keeps showing that field regardless, so turning this off never hides existing text or risks it being cleared on the next edit.

## Data

Set the database with the `DB_URL` environment variable. The app supports SQLite, PostgreSQL, and MariaDB or MySQL:

```bash
DB_URL=sqlite:///infabula.db
DB_URL=postgresql://user:pass@host/infabula   # needs: uv sync --extra postgres
DB_URL=mysql://user:pass@host/infabula        # needs: uv sync --extra mysql
```

The app defaults to SQLite. The older `DB_PATH` variable still works and maps to a SQLite file. Alembic manages the schema and applies migrations automatically at startup. A database from before Alembic existed keeps its data as-is: the app does not re-create it. On SQLite, the app writes a timestamped backup to a `backups/` folder next to the database at every startup.

Each entry belongs to one baby and records who created it. You can manage multiple babies and switch between them from the header.

The `baby_access` table gives each user one role on a baby's log: `owner`, `editor`, or `viewer`. An owner manages access from Settings → Baby → Manage access. From there, an owner can grant access, change a member's role, or revoke access. The account that created the baby keeps owner access permanently. As a result, no other owner can remove that account's access.

## Accounts

By default, registration is open. Anyone who can reach the app can register with an email address and a password. A new account cannot log in until someone clicks the confirmation link sent to that address.

Set `REGISTRATION_ENABLED=false` to close registration. This does not affect existing accounts, and registration still works from the LAN. Close registration after the app becomes reachable from the internet.

An admin can still add a new household member from anywhere with an invite. Create an invite from Settings → Admin → Invites. You can bind an invite to one email address, or leave it open. Share the one-time link with the new member. The invite expires after 7 days, or after first use. You can revoke an unused invite at any time.

Set these environment variables to send the confirmation email:

```bash
SMTP_HOST=smtp.example.com
SMTP_PORT=587            # default
SMTP_USER=you@example.com
SMTP_PASSWORD=...
SMTP_FROM=infabula@example.com   # defaults to SMTP_USER
APP_BASE_URL=http://192.168.1.50:8080   # how the household reaches the app — used to build the link
```

If you do not set `SMTP_HOST`, the app writes the link to stdout instead of an email. This works for local development. Do not use it for a real deployment: nobody outside the server can click the link. The app treats accounts created before this feature as already verified.

The app uses the same SMTP settings to send a notice for other security changes. As a result, no change to an account happens silently. The app sends a notice when TOTP turns on or off, when someone adds a passkey, and when someone grants baby access. A baby-access grant sends a notice to both the new member and the owner who granted access.

Each account can turn on two-factor login from Settings → Account:

- **TOTP** — scan the QR code into an authenticator app, then confirm with a code
- **Passkeys (WebAuthn)** — add one or more passkeys from the same tab

Passkeys need a secure context. They work on `localhost`. Over plain HTTP on a LAN IP address, most browsers refuse the passkey ceremony. Put a reverse proxy with TLS, for example Caddy, in front of the app for passkeys to work outside `localhost`.

Sessions use httponly cookies. Each session stays valid for 30 days. The app stores sessions on the server, so you can revoke a session by logging out.

## Rhythm reminders

Settings → Account → Reminders lets each account turn on a Web Push notification shortly before the baby usually wakes, or before the next typical bottle is due. The app learns those times from the log (see the "Typical day" section in Stats) and a background loop checks every few minutes.

It needs a VAPID key pair. Generate one and set it in the environment:

```bash
uv run python manage.py vapid
```

```bash
VAPID_PRIVATE_KEY=...
VAPID_PUBLIC_KEY=...
VAPID_CLAIM_EMAIL=mailto:you@example.com
```

Without these three, the feature stays off and the Reminders card says so. Push also needs a secure context — the same TLS reverse proxy that passkeys need.

You can delete your account from Settings → Account → Danger zone. You must enter your password to confirm. The app refuses the deletion while your account is the sole owner of a baby. Transfer ownership, or delete the baby first. This prevents a journal from disappearing without warning. After deletion, existing entries from your account stay, with no author.

An admin account can disable another account through the API. The app makes the first account created an admin. Disabling an account ends its sessions and API tokens at once. Disabling an account does not touch its journal history.

```bash
GET  /api/admin/users
POST /api/admin/users/{id}/disable
POST /api/admin/users/{id}/enable
```

An admin can also do this from Settings → Admin in the app. Or an admin can call the API directly, with a session cookie or a bearer token, or from `/docs`.

### CLI

`manage.py` gives the same account management from the command line. Use it to create the first account, because registration alone never grants admin rights. Use it to fix a locked-out household member without the API:

```bash
uv run python manage.py create a@example.com --admin   # prompts for a password
uv run python manage.py list
uv run python manage.py disable a@example.com
uv run python manage.py enable a@example.com
uv run python manage.py set-admin a@example.com [--off]
uv run python manage.py set-password a@example.com
uv run python manage.py delete a@example.com           # refuses while sole owner of a baby
```

Run the command inside the deployed container, so it uses the real database: `podman exec -it <container> uv run --no-sync python manage.py ...`. The `--no-sync` flag skips a re-check of dependencies against the container's lockfile, which excludes dev packages.

## API

The app documents every route at `/docs` (Swagger UI) or `/redoc`. Both need login, like the rest of the app. Two ways to authenticate:

- **Session cookie** — the browser uses this. If a script keeps the cookie jar from a login request, the script can use it too.
- **API token** — create one from Settings → Account → API tokens. Send it as `Authorization: Bearer <token>`. A token grants the same access as the account that created it.

The app shows a raw token once, at creation. You can revoke a token at any time.

## Podman/Docker (optional)

```bash
podman build -t infabula .
podman run -p 8080:8080 -v ./data:/app/data -e DB_PATH=/app/data/infabula.db infabula
```
