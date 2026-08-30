"""Admin: only an admin with TOTP enabled can list/disable/enable users,
an admin can't disable themselves, and enable/disable actually take
effect."""

from db import Session, User


async def _enable_totp(user_id: int) -> None:
    """Flips totp_enabled directly, after login.

    Creating the user with totp_enabled=True from the start would make
    `logged_in()` hit the real login-time TOTP challenge (it returns 200
    without ever setting a session cookie) — that flow is covered in
    test_auth.py; here only the *result* (an admin with 2FA on) matters.
    """
    async with Session.begin() as session:
        row = await session.get(User, user_id)
        assert row is not None
        row.totp_enabled = True


async def _logged_in_admin_with_totp(logged_in, **kwargs) -> int:
    user_id = await logged_in(is_admin=True, **kwargs)
    await _enable_totp(user_id)
    return user_id


class TestGate:
    async def test_non_admin_cannot_list_users(self, client, logged_in):
        await logged_in()
        assert (await client.get("/api/admin/users")).status_code == 403

    async def test_non_admin_cannot_disable_anyone(
        self, client, logged_in, user_factory
    ):
        await logged_in()
        other = await user_factory(email="other@example.com")
        res = await client.post(f"/api/admin/users/{other}/disable")
        assert res.status_code == 403

    async def test_non_admin_cannot_list_babies(self, client, logged_in):
        await logged_in()
        assert (await client.get("/api/admin/babies")).status_code == 403

    async def test_admin_without_totp_is_blocked(self, client, logged_in):
        """Being an admin isn't enough on its own — a password-only
        session shouldn't reach every household member's data."""
        await logged_in(is_admin=True)
        res = await client.get("/api/admin/users")
        assert res.status_code == 403
        assert "two-factor" in res.json()["error"]

    async def test_normal_account_use_is_unaffected_without_totp(
        self, client, logged_in
    ):
        """The TOTP requirement gates admin endpoints only — a non-admin
        (or an admin just using the app normally) is never forced into it."""
        await logged_in(is_admin=True)
        assert (await client.get("/api/auth/me")).status_code == 200
        assert (await client.get("/api/babies")).status_code == 200


class TestAdmin:
    async def test_can_list_users(self, client, logged_in, user_factory):
        await _logged_in_admin_with_totp(logged_in)
        await user_factory(email="other@example.com")
        rows = (await client.get("/api/admin/users")).json()
        assert {r["email"] for r in rows} == {"a@example.com", "other@example.com"}

    async def test_can_disable_and_enable_a_user(
        self, client, logged_in, user_factory
    ):
        await _logged_in_admin_with_totp(logged_in)
        target = await user_factory(email="target@example.com")

        disable = await client.post(f"/api/admin/users/{target}/disable")
        assert disable.status_code == 200
        login = await client.post(
            "/api/auth/login",
            json={"email": "target@example.com", "password": "password123"},
        )
        assert login.status_code == 403

        enable = await client.post(f"/api/admin/users/{target}/enable")
        assert enable.status_code == 200
        login2 = await client.post(
            "/api/auth/login",
            json={"email": "target@example.com", "password": "password123"},
        )
        assert login2.status_code == 200

    async def test_cannot_disable_self(self, client, logged_in):
        me = await _logged_in_admin_with_totp(logged_in)
        res = await client.post(f"/api/admin/users/{me}/disable")
        assert res.status_code == 400

    async def test_disabling_unknown_user_is_404(self, client, logged_in):
        await _logged_in_admin_with_totp(logged_in)
        res = await client.post("/api/admin/users/999999/disable")
        assert res.status_code == 404

    async def test_can_list_babies_with_owners_across_all_accounts(
        self, client, logged_in, user_factory, baby_factory
    ):
        admin = await _logged_in_admin_with_totp(logged_in)
        other = await user_factory(email="other@example.com")
        await baby_factory(admin, name="Admin's baby")
        await baby_factory(other, name="Other's baby")
        rows = (await client.get("/api/admin/babies")).json()
        by_name = {r["name"]: r for r in rows}
        assert by_name["Admin's baby"]["owners"] == ["a@example.com"]
        assert by_name["Other's baby"]["owners"] == ["other@example.com"]
