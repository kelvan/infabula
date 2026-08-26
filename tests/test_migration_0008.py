"""The 0007 -> 0008 admin/verification/disabled migration.

The one subtle part: which account becomes admin. A database that
predates real accounts seeds a placeholder user at id 1 with no
password (see db.py's DEFAULT_USER_ID) — that row must not become the
admin just because it has the lowest id, or the actual household
account ends up with no admin at all and the placeholder becomes an
unusable "admin" nobody can log in as.
"""

import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def alembic(db_path, *args):
    env = {**os.environ, "TZ": "Europe/Vienna", "DB_URL": f"sqlite:///{db_path}"}
    return subprocess.run(
        ["uv", "run", "alembic", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.fixture
def db_at_0007(tmp_path):
    db_path = tmp_path / "pre0008.db"
    result = alembic(db_path, "upgrade", "0007")
    assert result.returncode == 0, result.stderr
    return db_path


def read_users(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT id, email_verified, disabled, is_admin FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return rows


def test_placeholder_seed_row_does_not_become_admin(db_at_0007):
    """Mirrors the shape of the real production database: a passwordless
    row at id 1 from before accounts existed, and the actual household
    account at id 2."""
    conn = sqlite3.connect(db_at_0007)
    conn.execute("UPDATE users SET username = NULL WHERE id = 1")
    conn.execute(
        "INSERT INTO users (id, name, username, email, password_hash)"
        " VALUES (2, 'a', 'a@x.com', 'a@x.com', 'h')"
    )
    conn.commit()
    conn.close()

    assert alembic(db_at_0007, "upgrade", "0008").returncode == 0
    rows = {r[0]: r for r in read_users(db_at_0007)}
    assert rows[1][3] == 0, "the passwordless placeholder must not be admin"
    assert rows[2][3] == 1, "the real account should be admin"


def test_first_real_account_is_admin_when_id_1_has_a_password(db_at_0007):
    """The common case: id 1 is a real account too."""
    conn = sqlite3.connect(db_at_0007)
    conn.execute(
        "UPDATE users SET username = 'a@x.com', email = 'a@x.com',"
        " password_hash = 'h' WHERE id = 1"
    )
    conn.commit()
    conn.close()

    assert alembic(db_at_0007, "upgrade", "0008").returncode == 0
    rows = {r[0]: r for r in read_users(db_at_0007)}
    assert rows[1][3] == 1


def test_existing_accounts_are_grandfathered_as_verified(db_at_0007):
    assert alembic(db_at_0007, "upgrade", "0008").returncode == 0
    rows = read_users(db_at_0007)
    assert all(r[1] == 1 for r in rows), "every pre-existing row must be verified"
    assert all(r[2] == 0 for r in rows), "nobody starts out disabled"


def test_downgrade_drops_the_new_columns(db_at_0007):
    alembic(db_at_0007, "upgrade", "0008")
    assert alembic(db_at_0007, "downgrade", "0007").returncode == 0
    conn = sqlite3.connect(db_at_0007)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    conn.close()
    assert not columns & {"email_verified", "disabled", "is_admin"}
