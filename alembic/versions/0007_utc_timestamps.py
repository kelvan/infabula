"""store timestamps in UTC

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-26

Timestamps were naive local wall-clock strings, which only worked while
the server happened to share the household's timezone — when it didn't,
every entry read hours off. Entry times now carry an explicit UTC
instant ('YYYY-MM-DDTHH:MMZ'); the household timezone becomes purely a
presentation concern, applied when grouping a day or rendering a time.

Existing rows were written by browsers in the household's local zone, so
they are localized with that zone and converted. `babies.birthday` is a
calendar date, not an instant, and is deliberately left alone.
"""

import os
from datetime import datetime, timezone
from typing import Sequence, Union
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The zone the existing naive strings were written in. Same env var the
# app reads, so a deployment that already set TZ migrates correctly.
LEGACY_TZ = ZoneInfo(os.getenv("TZ", "UTC"))

ENTRY_FMT = "%Y-%m-%dT%H:%M"
STAMP_FMT = "%Y-%m-%d %H:%M:%S"

# table -> (primary key columns, timestamp columns)
STAMP_TABLES = {
    "entries": (("id",), ("created_at",)),
    "users": (("id",), ("created_at", "last_login_at")),
    "babies": (("id",), ("created_at",)),
    "baby_access": (("user_id", "baby_id"), ("created_at",)),
    "sessions": (("token",), ("created_at", "expires_at")),
    "webauthn_credentials": (("id",), ("created_at",)),
    "api_tokens": (("id",), ("created_at", "last_used_at")),
}


def _shift(value: str, fmt: str, suffix: str, to_utc: bool) -> str | None:
    """Reinterpret a naive string between local and UTC.

    Entry timestamps carry a 'Z' once converted, so a value that is
    already in the target form is left alone — re-running the conversion
    over converted data would otherwise shift it a second time.
    """
    if not value:
        return None
    # Only entry timestamps are self-describing (they gain a 'Z'), so
    # only they can be checked for having been converted already. The
    # bookkeeping stamps carry no marker and rely on Alembic's version
    # table not to be applied twice.
    marked = fmt is ENTRY_FMT
    if marked and value.endswith("Z") == to_utc:
        return None
    try:
        naive = datetime.strptime(value.rstrip("Z"), fmt)
    except ValueError:
        return None  # not a timestamp we recognise — leave it be
    if to_utc:
        moved = naive.replace(tzinfo=LEGACY_TZ).astimezone(timezone.utc)
    else:
        moved = naive.replace(tzinfo=timezone.utc).astimezone(LEGACY_TZ)
    return moved.strftime(fmt) + suffix


def _convert(to_utc: bool) -> None:
    conn = op.get_bind()

    entries = sa.table(
        "entries",
        sa.column("id"),
        sa.column("ts_start"),
        sa.column("ts_end"),
    )
    suffix = "Z" if to_utc else ""
    rows = conn.execute(
        sa.select(entries.c.id, entries.c.ts_start, entries.c.ts_end)
    ).fetchall()
    for row_id, ts_start, ts_end in rows:
        values = {}
        moved_start = _shift(ts_start or "", ENTRY_FMT, suffix, to_utc)
        if moved_start:
            values["ts_start"] = moved_start
        moved_end = _shift(ts_end or "", ENTRY_FMT, suffix, to_utc)
        if moved_end:
            values["ts_end"] = moved_end
        if values:
            conn.execute(
                entries.update().where(entries.c.id == row_id).values(**values)
            )

    # The bookkeeping stamps keep their format; only the zone they mean
    # changes, so they stay comparable with each other as before.
    for table_name, (pk_columns, columns) in STAMP_TABLES.items():
        all_columns = [*pk_columns, *columns]
        table = sa.table(table_name, *[sa.column(c) for c in all_columns])
        selected = conn.execute(
            sa.select(*[table.c[c] for c in all_columns])
        ).fetchall()
        for record in selected:
            keys = record[: len(pk_columns)]
            stamps = record[len(pk_columns) :]
            values = {}
            for column, stamp in zip(columns, stamps):
                moved = _shift(stamp or "", STAMP_FMT, "", to_utc)
                if moved:
                    values[column] = moved
            if not values:
                continue
            where = sa.and_(
                *[table.c[c] == k for c, k in zip(pk_columns, keys)]
            )
            conn.execute(table.update().where(where).values(**values))


def upgrade() -> None:
    _convert(to_utc=True)


def downgrade() -> None:
    _convert(to_utc=False)
