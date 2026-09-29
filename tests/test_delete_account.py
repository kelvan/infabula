"""Self-service account deletion: blocked while it solely owns a baby,
requires the password, and actually clears credentials on success."""

import os

from sqlalchemy import select

import main
from db import ApiToken, BabyAccess, Entry, Session


class TestDeleteAccount:
    async def test_wrong_password_is_refused(self, client, logged_in):
        await logged_in()
        res = await client.request(
            "DELETE", "/api/auth/me", json={"password": "wrong"}
        )
        assert res.status_code == 401
        assert (await client.get("/api/auth/me")).status_code == 200

    async def test_blocked_while_sole_owner_of_a_baby(
        self, client, logged_in, baby_factory
    ):
        me = await logged_in()
        await baby_factory(me, name="Samuel")
        res = await client.request(
            "DELETE", "/api/auth/me", json={"password": "password123"}
        )
        assert res.status_code == 400
        assert "Samuel" in res.json()["error"]
        assert (await client.get("/api/auth/me")).status_code == 200

    async def test_allowed_once_ownership_is_shared(
        self, client, logged_in, user_factory, baby_factory
    ):
        me = await logged_in()
        baby_id = await baby_factory(me, name="Samuel")
        co_owner = await user_factory(email="co@example.com")
        async with Session.begin() as session:
            session.add(
                BabyAccess(user_id=co_owner, baby_id=baby_id, role="owner")
            )
        res = await client.request(
            "DELETE", "/api/auth/me", json={"password": "password123"}
        )
        assert res.status_code == 200
        assert (await client.get("/api/auth/me")).status_code == 401

    async def test_allowed_when_only_editor_or_viewer(
        self, client, logged_in, user_factory, baby_factory
    ):
        owner = await user_factory(email="owner@example.com")
        baby_id = await baby_factory(owner)
        me = await logged_in()
        async with Session.begin() as session:
            session.add(BabyAccess(user_id=me, baby_id=baby_id, role="editor"))
        res = await client.request(
            "DELETE", "/api/auth/me", json={"password": "password123"}
        )
        assert res.status_code == 200

    async def test_entries_survive_with_no_author(
        self, client, logged_in, baby_factory
    ):
        me = await logged_in()
        owner_baby = await baby_factory(me, name="Samuel")
        co_owner_baby = await baby_factory(me, name="shared")
        from db import User

        async with Session.begin() as session:
            entry = Entry(
                baby_id=owner_baby, user_id=me, type="note", ts_start="x", meta={}
            )
            session.add(entry)
            # a second owner on `owner_baby` so deletion isn't blocked
            other = User(name="x", username="x@example.com", email="x@example.com")
            session.add(other)
            await session.flush()
            session.add(
                BabyAccess(user_id=other.id, baby_id=owner_baby, role="owner")
            )
            session.add(
                BabyAccess(user_id=other.id, baby_id=co_owner_baby, role="owner")
            )
            entry_id = entry.id

        res = await client.request(
            "DELETE", "/api/auth/me", json={"password": "password123"}
        )
        assert res.status_code == 200

        async with Session() as session:
            kept = await session.get(Entry, entry_id)
        assert kept is not None
        assert kept.user_id is None

    async def test_removes_the_avatar_file(self, client, logged_in):
        me = await logged_in()
        path = main.avatar_path(me)
        with open(path, "wb") as fh:
            fh.write(b"not a real webp, just needs to exist")
        res = await client.request(
            "DELETE", "/api/auth/me", json={"password": "password123"}
        )
        assert res.status_code == 200
        assert not os.path.exists(path)

    async def test_no_avatar_is_not_an_error(self, client, logged_in):
        me = await logged_in()
        assert not os.path.exists(main.avatar_path(me))
        res = await client.request(
            "DELETE", "/api/auth/me", json={"password": "password123"}
        )
        assert res.status_code == 200

    async def test_removes_api_tokens_in_the_same_deletion(
        self, client, logged_in
    ):
        me = await logged_in()
        async with Session.begin() as session:
            session.add(
                ApiToken(
                    user_id=me, name="t", token_hash="x", prefix="ib_x"
                )
            )
        res = await client.request(
            "DELETE", "/api/auth/me", json={"password": "password123"}
        )
        assert res.status_code == 200
        async with Session() as session:
            rows = (
                await session.scalars(
                    select(ApiToken).where(ApiToken.user_id == me)
                )
            ).all()
        assert rows == []

    async def test_clears_baby_access_rows(self, client, logged_in, baby_factory):
        me = await logged_in()
        b1 = await baby_factory(me, name="a")
        b2 = await baby_factory(me, name="b")
        async with Session.begin() as session:
            from db import User

            other = User(name="x", username="x@example.com", email="x@example.com")
            session.add(other)
            await session.flush()
            session.add(BabyAccess(user_id=other.id, baby_id=b1, role="owner"))
            session.add(BabyAccess(user_id=other.id, baby_id=b2, role="owner"))

        await client.request(
            "DELETE", "/api/auth/me", json={"password": "password123"}
        )
        async with Session() as session:
            rows = (
                await session.scalars(
                    select(BabyAccess).where(BabyAccess.user_id == me)
                )
            ).all()
        assert rows == []
