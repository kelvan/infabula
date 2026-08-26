"""Admin: only an admin can list/disable/enable users, an admin can't
disable themselves, and enable/disable actually take effect."""


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


class TestAdmin:
    async def test_can_list_users(self, client, logged_in, user_factory):
        await logged_in(is_admin=True)
        await user_factory(email="other@example.com")
        rows = (await client.get("/api/admin/users")).json()
        assert {r["email"] for r in rows} == {"a@example.com", "other@example.com"}

    async def test_can_disable_and_enable_a_user(
        self, client, logged_in, user_factory
    ):
        await logged_in(is_admin=True)
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
        me = await logged_in(is_admin=True)
        res = await client.post(f"/api/admin/users/{me}/disable")
        assert res.status_code == 400

    async def test_disabling_unknown_user_is_404(self, client, logged_in):
        await logged_in(is_admin=True)
        res = await client.post("/api/admin/users/999999/disable")
        assert res.status_code == 404
