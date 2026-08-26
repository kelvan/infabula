"""Per-baby access control.

Every baby-scoped route is gated on a role. These tests pin the matrix
so a viewer can never write and an editor can never take ownership.
"""

import main


async def _post_entry(client, baby_id, note="x"):
    return await client.post(
        f"/api/entries?baby_id={baby_id}",
        json={
            "type": "note",
            "ts_start": main.to_entry_ts(main.utc_now()),
            "note": note,
            "meta": {},
        },
    )


class TestUnauthenticated:
    async def test_api_returns_401(self, client):
        res = await client.get("/api/babies")
        assert res.status_code == 401

    async def test_html_redirects_to_login(self, client):
        res = await client.get("/")
        assert res.status_code == 307
        assert res.headers["location"] == "/login"

    async def test_login_page_is_public(self, client):
        assert (await client.get("/login")).status_code == 200


class TestStrangersBaby:
    """A baby you hold no access row for is invisible and untouchable."""

    async def test_not_listed(self, client, logged_in, user_factory, baby_factory):
        other = await user_factory(email="other@example.com")
        await baby_factory(other)
        await logged_in()
        assert (await client.get("/api/babies")).json() == []

    async def test_cannot_read_entries(
        self, client, logged_in, user_factory, baby_factory
    ):
        other = await user_factory(email="other@example.com")
        baby_id = await baby_factory(other)
        await logged_in()
        res = await client.get(f"/api/entries?baby_id={baby_id}")
        assert res.status_code == 403

    async def test_cannot_write_entries(
        self, client, logged_in, user_factory, baby_factory
    ):
        other = await user_factory(email="other@example.com")
        baby_id = await baby_factory(other)
        await logged_in()
        assert (await _post_entry(client, baby_id)).status_code == 403

    async def test_cannot_read_stats(
        self, client, logged_in, user_factory, baby_factory
    ):
        other = await user_factory(email="other@example.com")
        baby_id = await baby_factory(other)
        await logged_in()
        res = await client.get(f"/api/stats?baby_id={baby_id}")
        assert res.status_code == 403

    async def test_cannot_export(self, client, logged_in, user_factory, baby_factory):
        other = await user_factory(email="other@example.com")
        baby_id = await baby_factory(other)
        await logged_in()
        res = await client.get(
            f"/api/export.csv?start=2026-08-01&end=2026-08-31&baby_id={baby_id}"
        )
        assert res.status_code == 403


class TestViewer:
    async def test_can_read(self, client, logged_in, user_factory, baby_factory):
        owner = await user_factory(email="owner@example.com")
        baby_id = await baby_factory(owner)
        me = await logged_in()
        await baby_factory(me, name="ignored")  # unrelated own baby
        from db import BabyAccess, Session

        async with Session.begin() as session:
            session.add(BabyAccess(user_id=me, baby_id=baby_id, role="viewer"))
        assert (await client.get(f"/api/entries?baby_id={baby_id}")).status_code == 200

    async def test_cannot_write(self, client, logged_in, user_factory, baby_factory):
        owner = await user_factory(email="owner@example.com")
        baby_id = await baby_factory(owner)
        me = await logged_in()
        from db import BabyAccess, Session

        async with Session.begin() as session:
            session.add(BabyAccess(user_id=me, baby_id=baby_id, role="viewer"))
        assert (await _post_entry(client, baby_id)).status_code == 403


class TestEditor:
    async def _as_editor(self, logged_in, user_factory, baby_factory):
        owner = await user_factory(email="owner@example.com")
        baby_id = await baby_factory(owner)
        me = await logged_in()
        from db import BabyAccess, Session

        async with Session.begin() as session:
            session.add(BabyAccess(user_id=me, baby_id=baby_id, role="editor"))
        return baby_id

    async def test_can_write(self, client, logged_in, user_factory, baby_factory):
        baby_id = await self._as_editor(logged_in, user_factory, baby_factory)
        assert (await _post_entry(client, baby_id)).status_code == 200

    async def test_cannot_delete_the_baby(
        self, client, logged_in, user_factory, baby_factory
    ):
        baby_id = await self._as_editor(logged_in, user_factory, baby_factory)
        assert (await client.delete(f"/api/babies/{baby_id}")).status_code == 403

    async def test_cannot_manage_access(
        self, client, logged_in, user_factory, baby_factory
    ):
        baby_id = await self._as_editor(logged_in, user_factory, baby_factory)
        assert (await client.get(f"/api/babies/{baby_id}/access")).status_code == 403

    async def test_cannot_promote_self_to_owner(
        self, client, logged_in, user_factory, baby_factory
    ):
        baby_id = await self._as_editor(logged_in, user_factory, baby_factory)
        res = await client.post(
            f"/api/babies/{baby_id}/access",
            json={"email": "a@example.com", "role": "owner"},
        )
        assert res.status_code == 403


class TestOwner:
    async def test_can_invite_and_revoke(
        self, client, logged_in, user_factory, baby_factory
    ):
        me = await logged_in()
        baby_id = await baby_factory(me)
        guest = await user_factory(email="guest@example.com")

        granted = await client.post(
            f"/api/babies/{baby_id}/access",
            json={"email": "guest@example.com", "role": "editor"},
        )
        assert granted.status_code == 200
        members = (await client.get(f"/api/babies/{baby_id}/access")).json()
        assert {m["email"] for m in members} == {"a@example.com", "guest@example.com"}

        revoked = await client.delete(f"/api/babies/{baby_id}/access/{guest}")
        assert revoked.status_code == 200
        members = (await client.get(f"/api/babies/{baby_id}/access")).json()
        assert {m["email"] for m in members} == {"a@example.com"}

    async def test_cannot_invite_unknown_user(
        self, client, logged_in, baby_factory
    ):
        me = await logged_in()
        baby_id = await baby_factory(me)
        res = await client.post(
            f"/api/babies/{baby_id}/access",
            json={"email": "nobody@example.com", "role": "editor"},
        )
        assert res.status_code == 404

    async def test_rejects_an_invented_role(self, client, logged_in, baby_factory):
        me = await logged_in()
        baby_id = await baby_factory(me)
        await client.post("/api/auth/register", json={})  # noise
        res = await client.post(
            f"/api/babies/{baby_id}/access",
            json={"email": "a@example.com", "role": "superuser"},
        )
        assert res.status_code == 400

    async def test_last_owner_cannot_be_removed(
        self, client, logged_in, baby_factory
    ):
        """Otherwise the baby is orphaned and nobody can administer it."""
        me = await logged_in()
        baby_id = await baby_factory(me)
        res = await client.delete(f"/api/babies/{baby_id}/access/{me}")
        assert res.status_code == 400


class TestEntryOwnership:
    async def test_cannot_patch_another_babys_entry(
        self, client, logged_in, user_factory, baby_factory
    ):
        owner = await user_factory(email="owner@example.com")
        baby_id = await baby_factory(owner)
        from db import Entry, Session

        async with Session.begin() as session:
            entry = Entry(
                baby_id=baby_id,
                user_id=owner,
                type="note",
                ts_start=main.to_entry_ts(main.utc_now()),
                note="theirs",
                meta={},
            )
            session.add(entry)
            await session.flush()
            entry_id = entry.id

        await logged_in()
        res = await client.patch(f"/api/entries/{entry_id}", json={"note": "hacked"})
        assert res.status_code == 403

    async def test_cannot_delete_another_babys_entry(
        self, client, logged_in, user_factory, baby_factory
    ):
        owner = await user_factory(email="owner@example.com")
        baby_id = await baby_factory(owner)
        from db import Entry, Session

        async with Session.begin() as session:
            entry = Entry(
                baby_id=baby_id,
                user_id=owner,
                type="note",
                ts_start=main.to_entry_ts(main.utc_now()),
                meta={},
            )
            session.add(entry)
            await session.flush()
            entry_id = entry.id

        await logged_in()
        assert (await client.delete(f"/api/entries/{entry_id}")).status_code == 403
