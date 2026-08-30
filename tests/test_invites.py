"""Invite-only registration: an admin-issued link lets someone register
even while open signup is closed or they're off-LAN — the exception
REGISTRATION_ENABLED=false was always meant to have."""

import main


async def register(client, email="new@example.com", password="password123", **extra):
    return await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, **extra},
    )


class TestAdminGate:
    async def test_non_admin_cannot_create_invites(self, client, logged_in):
        await logged_in()
        res = await client.post("/api/admin/invites", json={})
        assert res.status_code == 403

    async def test_non_admin_cannot_list_invites(self, client, logged_in):
        await logged_in()
        assert (await client.get("/api/admin/invites")).status_code == 403


class TestCreateAndRedeem:
    async def _admin(self, client, logged_in):
        from tests.test_admin import _logged_in_admin_with_totp

        return await _logged_in_admin_with_totp(logged_in)

    async def test_open_invite_lets_anyone_register_when_closed(
        self, client, logged_in, monkeypatch
    ):
        await self._admin(client, logged_in)
        created = (await client.post("/api/admin/invites", json={})).json()
        assert created["token"] in created["link"]

        monkeypatch.setattr(main, "REGISTRATION_ENABLED", False)
        anon = client  # same client is fine, invite doesn't need a session
        res = await register(
            anon,
            email="invited@example.com",
            headers={"X-Forwarded-For": "8.8.8.8"},
            invite_token=created["token"],
        )
        assert res.status_code == 200

    async def test_records_who_invited_the_new_account(
        self, client, logged_in, monkeypatch
    ):
        admin_id = await self._admin(client, logged_in)
        created = (await client.post("/api/admin/invites", json={})).json()
        monkeypatch.setattr(main, "REGISTRATION_ENABLED", False)
        await register(
            client,
            email="invited@example.com",
            headers={"X-Forwarded-For": "8.8.8.8"},
            invite_token=created["token"],
        )
        users = (await client.get("/api/admin/users")).json()
        invited = next(u for u in users if u["email"] == "invited@example.com")
        admin = next(u for u in users if u["id"] == admin_id)
        assert invited["invited_by"] == admin["email"]

    async def test_a_regular_registration_has_no_inviter(self, client, logged_in):
        await self._admin(client, logged_in)
        await register(client, email="walkup@example.com")
        users = (await client.get("/api/admin/users")).json()
        walkup = next(u for u in users if u["email"] == "walkup@example.com")
        assert walkup["invited_by"] is None

    async def test_email_bound_invite_rejects_a_different_email(
        self, client, logged_in, monkeypatch
    ):
        await self._admin(client, logged_in)
        created = (
            await client.post(
                "/api/admin/invites", json={"email": "only-this@example.com"}
            )
        ).json()

        monkeypatch.setattr(main, "REGISTRATION_ENABLED", False)
        res = await register(
            client,
            email="someone-else@example.com",
            headers={"X-Forwarded-For": "8.8.8.8"},
            invite_token=created["token"],
        )
        assert res.status_code == 400

    async def test_email_bound_invite_accepts_the_matching_email(
        self, client, logged_in, monkeypatch
    ):
        await self._admin(client, logged_in)
        created = (
            await client.post(
                "/api/admin/invites", json={"email": "only-this@example.com"}
            )
        ).json()

        monkeypatch.setattr(main, "REGISTRATION_ENABLED", False)
        res = await register(
            client,
            email="only-this@example.com",
            headers={"X-Forwarded-For": "8.8.8.8"},
            invite_token=created["token"],
        )
        assert res.status_code == 200

    async def test_invite_is_single_use(self, client, logged_in, monkeypatch):
        await self._admin(client, logged_in)
        created = (await client.post("/api/admin/invites", json={})).json()
        monkeypatch.setattr(main, "REGISTRATION_ENABLED", False)

        first = await register(
            client,
            email="first@example.com",
            headers={"X-Forwarded-For": "8.8.8.8"},
            invite_token=created["token"],
        )
        assert first.status_code == 200

        second = await register(
            client,
            email="second@example.com",
            headers={"X-Forwarded-For": "8.8.8.8"},
            invite_token=created["token"],
        )
        assert second.status_code == 400

    async def test_unknown_token_is_rejected(self, client, monkeypatch):
        monkeypatch.setattr(main, "REGISTRATION_ENABLED", False)
        res = await register(
            client,
            headers={"X-Forwarded-For": "8.8.8.8"},
            invite_token="inv_not-a-real-token",
        )
        assert res.status_code == 400

    async def test_a_failed_registration_does_not_burn_the_invite(
        self, client, logged_in, monkeypatch
    ):
        """Weak password rejected before the invite is ever touched —
        retrying with a stronger one still works."""
        await self._admin(client, logged_in)
        created = (await client.post("/api/admin/invites", json={})).json()
        monkeypatch.setattr(main, "REGISTRATION_ENABLED", False)

        weak = await register(
            client,
            email="retry@example.com",
            password="short",
            headers={"X-Forwarded-For": "8.8.8.8"},
            invite_token=created["token"],
        )
        assert weak.status_code == 400

        strong = await register(
            client,
            email="retry@example.com",
            headers={"X-Forwarded-For": "8.8.8.8"},
            invite_token=created["token"],
        )
        assert strong.status_code == 200


class TestRevoke:
    async def _admin(self, client, logged_in):
        from tests.test_admin import _logged_in_admin_with_totp

        return await _logged_in_admin_with_totp(logged_in)

    async def test_can_revoke_an_unused_invite(self, client, logged_in, monkeypatch):
        await self._admin(client, logged_in)
        created = (await client.post("/api/admin/invites", json={})).json()
        invite_id = (await client.get("/api/admin/invites")).json()[0]["id"]

        res = await client.delete(f"/api/admin/invites/{invite_id}")
        assert res.status_code == 200

        monkeypatch.setattr(main, "REGISTRATION_ENABLED", False)
        register_res = await register(
            client,
            headers={"X-Forwarded-For": "8.8.8.8"},
            invite_token=created["token"],
        )
        assert register_res.status_code == 400

    async def test_cannot_revoke_an_already_used_invite(
        self, client, logged_in, monkeypatch
    ):
        await self._admin(client, logged_in)
        created = (await client.post("/api/admin/invites", json={})).json()
        invite_id = (await client.get("/api/admin/invites")).json()[0]["id"]

        monkeypatch.setattr(main, "REGISTRATION_ENABLED", False)
        await register(
            client,
            headers={"X-Forwarded-For": "8.8.8.8"},
            invite_token=created["token"],
        )
        res = await client.delete(f"/api/admin/invites/{invite_id}")
        assert res.status_code == 400
