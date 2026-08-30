"""Registration hardening: an account can't log in until its email is
confirmed, disabled accounts can't log in at all, and the whole loop
(register -> resend -> click -> log in) works end to end."""

import auth


async def register(client, email="new@example.com", password="password123"):
    return await client.post(
        "/api/auth/register", json={"email": email, "password": password}
    )


class TestRegistration:
    async def test_closed_registration_is_refused_from_the_internet(
        self, client, monkeypatch
    ):
        import main

        monkeypatch.setattr(main, "REGISTRATION_ENABLED", False)
        res = await client.post(
            "/api/auth/register",
            json={"email": "new@example.com", "password": "password123"},
            headers={"X-Forwarded-For": "8.8.8.8"},
        )
        assert res.status_code == 403

    async def test_closed_registration_still_works_from_the_lan(
        self, client, monkeypatch
    ):
        """Closing registration to the internet shouldn't stop the
        household adding a member from their own wifi."""
        import main

        monkeypatch.setattr(main, "REGISTRATION_ENABLED", False)
        res = await client.post(
            "/api/auth/register",
            json={"email": "new@example.com", "password": "password123"},
            headers={"X-Forwarded-For": "10.0.1.55"},
        )
        assert res.status_code == 200

    async def test_account_starts_unverified(self, client):
        await register(client)
        from sqlalchemy import select

        from db import Session, User

        async with Session() as session:
            user = await session.scalar(
                select(User).where(User.username == "new@example.com")
            )
        assert user is not None and user.email_verified is False

    async def test_login_is_refused_before_verification(self, client):
        await register(client)
        res = await client.post(
            "/api/auth/login",
            json={"email": "new@example.com", "password": "password123"},
        )
        assert res.status_code == 403


class TestLoginPageRegistrationState:
    async def test_shows_the_form_for_lan_even_when_globally_closed(
        self, client, monkeypatch
    ):
        import main

        monkeypatch.setattr(main, "REGISTRATION_ENABLED", False)
        res = await client.get("/login", headers={"X-Forwarded-For": "10.0.1.55"})
        assert 'id="register-form"' in res.text

    async def test_hides_the_form_for_the_internet_when_closed(
        self, client, monkeypatch
    ):
        import main

        monkeypatch.setattr(main, "REGISTRATION_ENABLED", False)
        res = await client.get("/login", headers={"X-Forwarded-For": "8.8.8.8"})
        assert 'id="register-form"' not in res.text
        assert "Registration is currently closed" in res.text


class TestVerifyLink:
    async def _token_for(self, email="new@example.com"):
        from sqlalchemy import select

        from db import EmailVerification, Session

        async with Session() as session:
            row = await session.scalar(select(EmailVerification))
        assert row is not None
        return row.token

    async def test_valid_token_verifies_and_login_then_works(self, client):
        await register(client)
        token = await self._token_for()
        res = await client.get(
            f"/api/auth/verify-email?token={token}", follow_redirects=False
        )
        assert res.status_code in (302, 307)
        login = await client.post(
            "/api/auth/login",
            json={"email": "new@example.com", "password": "password123"},
        )
        assert login.status_code == 200

    async def test_token_is_single_use(self, client):
        await register(client)
        token = await self._token_for()
        await client.get(f"/api/auth/verify-email?token={token}")
        second = await client.get(
            f"/api/auth/verify-email?token={token}", follow_redirects=False
        )
        assert "expired" in second.headers["location"]

    async def test_garbage_token_does_not_verify_anything(self, client):
        await register(client)
        res = await client.get(
            "/api/auth/verify-email?token=not-a-real-token", follow_redirects=False
        )
        assert "expired" in res.headers["location"]
        login = await client.post(
            "/api/auth/login",
            json={"email": "new@example.com", "password": "password123"},
        )
        assert login.status_code == 403


class TestResend:
    async def test_replaces_the_old_link(self, client):
        """A stale, already-opened email can't be used once a resend
        was requested — only the newest token is valid."""
        await register(client)
        from sqlalchemy import select

        from db import EmailVerification, Session

        async with Session() as session:
            first_token = await session.scalar(select(EmailVerification.token))

        resend = await client.post(
            "/api/auth/resend-verification",
            json={"email": "new@example.com", "password": "password123"},
        )
        assert resend.status_code == 200

        stale = await client.get(
            f"/api/auth/verify-email?token={first_token}", follow_redirects=False
        )
        assert "expired" in stale.headers["location"]

        async with Session() as session:
            new_token = await session.scalar(select(EmailVerification.token))
        fresh = await client.get(
            f"/api/auth/verify-email?token={new_token}", follow_redirects=False
        )
        assert "ok" in fresh.headers["location"]

    async def test_wrong_password_is_refused(self, client):
        await register(client)
        res = await client.post(
            "/api/auth/resend-verification",
            json={"email": "new@example.com", "password": "wrong"},
        )
        assert res.status_code == 401

    async def test_is_throttled(self, client):
        await register(client)
        for _ in range(auth.MAX_RESEND_ATTEMPTS):
            await client.post(
                "/api/auth/resend-verification",
                json={"email": "new@example.com", "password": "wrong"},
            )
        res = await client.post(
            "/api/auth/resend-verification",
            json={"email": "new@example.com", "password": "password123"},
        )
        assert res.status_code == 429


class TestDisabled:
    async def test_disabled_account_cannot_log_in(
        self, client, logged_in, user_factory
    ):
        await user_factory(email="disabled@example.com", disabled=True)
        res = await client.post(
            "/api/auth/login",
            json={"email": "disabled@example.com", "password": "password123"},
        )
        assert res.status_code == 403

    async def test_disabling_kills_an_active_session(
        self, client, logged_in, user_factory
    ):
        target = await user_factory(email="target@example.com")
        target_client_login = await client.post(
            "/api/auth/login",
            json={"email": "target@example.com", "password": "password123"},
        )
        assert target_client_login.status_code == 200
        assert (await client.get("/api/auth/me")).status_code == 200

        admin_id = await user_factory(email="admin@example.com", is_admin=True)
        import httpx

        import main
        from db import Session, User

        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as admin_client:
            await admin_client.post(
                "/api/auth/login",
                json={"email": "admin@example.com", "password": "password123"},
            )
            # Flipped after login, not at User(...) time or before logging
            # in: either would make the login above hit the real
            # TOTP-challenge branch (200, but no session cookie) instead
            # of a normal completed login.
            async with Session.begin() as session:
                row = await session.get(User, admin_id)
                assert row is not None
                row.totp_enabled = True
            res = await admin_client.post(f"/api/admin/users/{target}/disable")
            assert res.status_code == 200

        assert (await client.get("/api/auth/me")).status_code == 401
