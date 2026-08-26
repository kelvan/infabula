"""The 0006 -> 0007 UTC conversion.

This migration rewrote every timestamp in a live database, so it is
worth pinning: the conversion must preserve which local day each entry
belongs to, leave calendar dates alone, and be reversible.
"""

import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# (id, ts_start, ts_end) in the pre-migration naive local form.
LEGACY_ROWS = [
    (1, "2026-08-25T21:00", "2026-08-26T06:30"),  # overnight sleep
    (2, "2026-08-25T00:15", None),  # just after local midnight
    (3, "2026-08-25T23:59", None),  # just before local midnight
    (4, "2026-01-15T12:00", None),  # winter, CET (+1)
    (5, "2026-08-15T12:00", None),  # summer, CEST (+2)
]


def alembic(db_path, *args):
    env = {
        **os.environ,
        "TZ": "Europe/Vienna",
        "DB_URL": f"sqlite:///{db_path}",
    }
    return subprocess.run(
        ["uv", "run", "alembic", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.fixture
def legacy_db(tmp_path):
    """A database at revision 0006 holding naive local timestamps."""
    db_path = tmp_path / "legacy.db"
    result = alembic(db_path, "upgrade", "0006")
    assert result.returncode == 0, result.stderr

    # Revision 0002 already seeds user 1 and baby 1; reuse them.
    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE babies SET name = 'Samuel', birthday = '2026-05-05' WHERE id = 1"
    )
    for row_id, start, end in LEGACY_ROWS:
        conn.execute(
            "INSERT INTO entries (id, baby_id, type, ts_start, ts_end, meta)"
            " VALUES (?, 1, 'note', ?, ?, '{}')",
            (row_id, start, end),
        )
    conn.commit()
    conn.close()
    return db_path


def read_entries(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT id, ts_start, ts_end FROM entries ORDER BY id"
    ).fetchall()
    conn.close()
    return rows


def test_converts_local_to_utc(legacy_db):
    assert alembic(legacy_db, "upgrade", "0007").returncode == 0
    rows = dict((r[0], (r[1], r[2])) for r in read_entries(legacy_db))
    # CEST is +2, so local 21:00 is 19:00Z.
    assert rows[1] == ("2026-08-25T19:00Z", "2026-08-26T04:30Z")
    # CET is +1 in January.
    assert rows[4][0] == "2026-01-15T11:00Z"
    assert rows[5][0] == "2026-08-15T10:00Z"


def test_every_value_carries_the_utc_marker(legacy_db):
    alembic(legacy_db, "upgrade", "0007")
    for _, start, end in read_entries(legacy_db):
        assert start.endswith("Z")
        assert end is None or end.endswith("Z")


def test_local_day_is_preserved(legacy_db):
    """The strongest invariant: no entry may change which day it is on."""
    before = {r[0]: r[1][:10] for r in read_entries(legacy_db)}
    alembic(legacy_db, "upgrade", "0007")

    import sys

    sys.path.insert(0, str(ROOT))
    os.environ["TZ"] = "Europe/Vienna"
    from main import local_day_of

    after = {r[0]: local_day_of(r[1]) for r in read_entries(legacy_db)}
    assert before == after


def test_birthday_is_left_alone(legacy_db):
    """A birthday is a calendar date, not an instant."""
    alembic(legacy_db, "upgrade", "0007")
    conn = sqlite3.connect(legacy_db)
    birthday = conn.execute("SELECT birthday FROM babies").fetchone()[0]
    conn.close()
    assert birthday == "2026-05-05"


def test_downgrade_restores_the_original_values(legacy_db):
    original = read_entries(legacy_db)
    assert alembic(legacy_db, "upgrade", "0007").returncode == 0
    assert read_entries(legacy_db) != original
    assert alembic(legacy_db, "downgrade", "0006").returncode == 0
    assert read_entries(legacy_db) == original


def test_entry_conversion_is_idempotent(legacy_db):
    """Entry times must not shift twice if the conversion is re-applied.

    Alembic's version table normally prevents a second run; this guards
    the case where it doesn't (a restored database, a manual re-run),
    where a silent double shift would be hard to notice.
    """
    alembic(legacy_db, "upgrade", "0007")
    once = read_entries(legacy_db)

    conn = sqlite3.connect(legacy_db)
    conn.execute("UPDATE alembic_version SET version_num = '0006'")
    conn.commit()
    conn.close()

    alembic(legacy_db, "upgrade", "0007")
    assert read_entries(legacy_db) == once
