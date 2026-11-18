# Changelog

All notable changes to infabula are documented here, grouped by release.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

No git tags exist yet — the versions below are a **proposed** cut of the
project's history into releases, grouped by theme and date. Nothing here
is final until tagged; adjust freely before doing so.

## [Unreleased] — Admin & invites

Security-hardening pass around the new web admin area, plus a real
invite flow.

### Added
- Web admin area: list every user and baby, disable/enable accounts.
- Owners can change a baby-access member's role or revoke it, not just
  grant new access. Whoever created a baby keeps permanent owner access
  to it — no other owner can lock them out.
- Email notifications for security-relevant changes: TOTP toggled, a
  passkey added, baby access granted (to both the new member and the
  granting owner).
- Invite-only registration: an admin-issued, optionally email-bound,
  single-use link that works even while open signup is closed or the
  visitor is off the LAN.
- Tracks who invited whom, kept on the account itself so it survives
  the invite record being revoked or expiring.

### Security
- Admin endpoints now require TOTP on the admin's own account — a bare
  password is no longer enough to reach every household member's data.

---

## [0.5.0] — 2026-08-30 — Installable app & personalization

### Added
- Installable PWA: manifest, icons, service worker.
- Per-account quick-action choices (previously stored per-browser).
- Per-baby nap/night-sleep threshold, replacing a fixed global constant.
- Profile avatar upload with a client-side crop step before saving;
  uploads restricted to a real image-format allowlist.
- `manage.py` — CLI to create, list, disable/enable, delete accounts,
  and reset passwords.

### Fixed
- Startup and error logs never reaching podman/journald (Alembic's
  logging setup was silently disabling them).
- The Baby settings Save button doing nothing (a broken CSS selector).

### Changed
- Project description updated to reflect the app's actual scope.

---

## [0.4.0] — 2026-08-28 to 2026-08-29 — Ready for the internet

### Added
- `REGISTRATION_ENABLED` switch to close signup (still allowed from the
  LAN even when closed to the internet).
- IP-based brute-force ban after repeated failed logins.
- SQLite → PostgreSQL migration script; the database password can be
  supplied separately from `DB_URL`.
- Implicit-TLS SMTP (port 465) support, not just STARTTLS.

### Security
- Session cookie marked `Secure` over TLS.
- Trust Caddy's `X-Forwarded-Proto` so WebAuthn's origin check works
  correctly behind a reverse proxy.

### Changed
- Upgraded dependencies, including Starlette's 1.0 major release.
- Renamed "Invite" to "Add" for granting baby access — it grants
  immediately, with no confirmation step, so "invite" was misleading.

### Fixed
- Registration-closed message alignment.

---

## [0.3.0] — 2026-08-26 to 2026-08-27 — Hardening & test infrastructure

### Added
- Personal API tokens, with OpenAPI/Swagger docs.
- Email verification required for new accounts; an admin can disable
  an account.
- Self-service account deletion.
- Full automated test suite; GitHub Actions CI running it, plus ruff
  and ty.
- Average sleep/awake duration in stats (night sleep excluded from the
  nap average).

### Security
- Fixed a stored XSS in entry editing.
- Throttled login and TOTP guess attempts.
- Capped babies per account, entries per day, and how far back or
  forward an entry may be dated.

### Changed
- Timestamps stored as UTC instants instead of naive local strings
  (migration written to be safe to re-run).
- Container runs in the household's configured timezone.

### Fixed
- `uv` re-syncing dev dependencies on every container start.
- Admin bootstrap picking an unusable placeholder account.
- Several unhandled crashes on missing or racing rows.
- Editing an entry no longer jumps the day view to the entry's date.

---

## [0.2.0] — 2026-08-23 to 2026-08-25 — Accounts & multi-baby

### Added
- Accounts: password login, with optional TOTP and passkey (WebAuthn)
  two-factor.
- Multi-baby support — switch between babies from the header.
- Per-baby access roles (owner/editor/viewer), with confirmation
  before revoking a share.
- Entries record who logged them.
- Display name per account.

### Changed
- Storage migrated from raw SQLite calls to SQLAlchemy ORM + Alembic
  migrations.
- Login identifier switched to email; last-login time tracked.
- Settings reorganized into three grouped tabs.

### Fixed
- German "still sleeping" label word order.

---

## [0.1.0] — 2026-06-08 to 2026-08-22 — Initial local journal

The original single-baby, local-network journal.

### Added
- Diaper, nursing, bottle, sleep, walk, clothing-change, mood, and
  weight/height entries — sleep and walk as open/close pairs.
- Day timeline view (list or visual timeline), remembered across
  reloads.
- Growth chart (weight/height over time).
- Quick actions: up to 5 configurable one-tap log buttons.
- Diaper/dirty-diaper day counters, combined feeding stat, daily
  bottle ml total.
- Stats: last-event summaries, awake/back-since durations, diaper and
  feeding intervals.
- CSV and printable report export for day/week/month/custom ranges.
- DE/EN language switcher.
- Multi-device live sync (SSE), with per-device IP naming and coloring.
- Baby name and birthday banner.
- Swipe gestures to switch tabs; tap any entry to edit it.
- Automatic SQLite backup on every startup.
- Redesigned visual style, with polished icons and mobile date/time
  pickers.
