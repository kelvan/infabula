"""Shared fixtures.

`main` reads TZ and opens the database at import time, so both are set
here before it is ever imported — every test runs against a throwaway
SQLite file with the migrations applied, in a fixed timezone so the
day-boundary tests mean the same thing on any machine.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Must happen before `import main` — it binds the zone and the engine at
# module scope.
os.environ["TZ"] = "Europe/Vienna"
_TMP_DB = Path(tempfile.mkdtemp(prefix="infabula-tests-")) / "test.db"
os.environ["DB_URL"] = f"sqlite:///{_TMP_DB}"

import bcrypt  # noqa: E402

import auth  # noqa: E402
import main  # noqa: E402
from db import Base, Session  # noqa: E402

# bcrypt's cost is the point in production and pure overhead here — the
# tests care that hashing round-trips and that wrong passwords fail, not
# how many rounds it took. Lowest legal cost keeps the suite quick enough
# to run on every change.
_real_gensalt = bcrypt.gensalt
bcrypt.gensalt = lambda rounds=4, prefix=b"2b": _real_gensalt(  # ty: ignore[invalid-assignment]
    4, prefix
)


@pytest.fixture(autouse=True)
async def clean_db():
    """Empty every table between tests, so order never matters."""
    async with Session.begin() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
    auth._fails.clear()
    auth._pending.clear()
    yield


@pytest.fixture
async def user_factory():
    """Create a user directly, skipping the registration endpoint."""
    from db import User

    async def make(email="a@example.com", password="password123", **kwargs):
        async with Session.begin() as session:
            user = User(
                name=email,
                username=email,
                email=email,
                password_hash=auth.hash_password(password),
                **kwargs,
            )
            session.add(user)
            await session.flush()
            return user.id

    return make


@pytest.fixture
async def baby_factory():
    from db import Baby, BabyAccess

    async def make(user_id, name="Samuel", role="owner", birthday=None):
        async with Session.begin() as session:
            baby = Baby(name=name, birthday=birthday)
            session.add(baby)
            await session.flush()
            session.add(
                BabyAccess(user_id=user_id, baby_id=baby.id, role=role)
            )
            return baby.id

    return make


@pytest.fixture
async def client():
    """An HTTP client speaking to the app in-process."""
    import httpx

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as http_client:
        yield http_client


@pytest.fixture
async def logged_in(client, user_factory):
    """A client carrying a session cookie, plus its user id."""

    async def login(email="a@example.com", password="password123", **kwargs):
        user_id = await user_factory(email=email, password=password, **kwargs)
        res = await client.post(
            "/api/auth/login", json={"email": email, "password": password}
        )
        assert res.status_code == 200, res.text
        return user_id

    return login
