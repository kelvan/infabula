"""Quick-log button choices live on the account, not the browser, so they
follow the user across devices instead of resetting on a new one."""


class TestQuickActions:
    async def test_defaults_to_none(self, client, logged_in):
        await logged_in()
        me = (await client.get("/api/auth/me")).json()
        assert me["quick_actions"] is None

    async def test_save_and_read_back(self, client, logged_in):
        await logged_in()
        res = await client.put(
            "/api/auth/quick-actions", json={"quick_actions": ["diaper", "walk"]}
        )
        assert res.status_code == 200
        me = (await client.get("/api/auth/me")).json()
        assert me["quick_actions"] == ["diaper", "walk"]

    async def test_rejects_unknown_type(self, client, logged_in):
        await logged_in()
        res = await client.put(
            "/api/auth/quick-actions", json={"quick_actions": ["not_a_real_type"]}
        )
        assert res.status_code == 400

    async def test_caps_at_five(self, client, logged_in):
        await logged_in()
        types = ["diaper", "nursing", "bottle", "sleep", "walk", "clothing", "note"]
        await client.put("/api/auth/quick-actions", json={"quick_actions": types})
        me = (await client.get("/api/auth/me")).json()
        assert len(me["quick_actions"]) == 5

    async def test_requires_a_session(self, client):
        res = await client.put(
            "/api/auth/quick-actions", json={"quick_actions": ["diaper"]}
        )
        assert res.status_code == 401
