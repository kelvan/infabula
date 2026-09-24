"""Login, throttling, TOTP and API tokens."""

import time

import pyotp
import pytest

import auth


class TestRegistration:
    async def test_does_not_log_in_before_verification(self, client):
        """Registering creates the account but not a session — the
        address has to be confirmed first."""
        res = await client.post(
            "/api/auth/register",
            json={"email": "new@example.com", "password": "password123"},
        )
        assert res.status_code == 200
        assert (await client.get("/api/auth/me")).status_code == 401

    @pytest.mark.parametrize(
        "email", ["notanemail", "@example.com", "a@b", "", "a b@example.com"]
    )
    async def test_rejects_bad_email(self, client, email):
        res = await client.post(
            "/api/auth/register", json={"email": email, "password": "password123"}
        )
        assert res.status_code == 400

    async def test_rejects_short_password(self, client):
        res = await client.post(
            "/api/auth/register", json={"email": "a@example.com", "password": "short"}
        )
        assert res.status_code == 400

    async def test_rejects_duplicate_email(self, client, user_factory):
        await user_factory(email="taken@example.com")
        res = await client.post(
            "/api/auth/register",
            json={"email": "taken@example.com", "password": "password123"},
        )
        assert res.status_code == 409

    async def test_password_is_not_stored_in_the_clear(self, client, user_factory):
        from sqlalchemy import select

        from db import Session, User

        await user_factory(email="p@example.com", password="password123")
        async with Session() as session:
            user = await session.scalar(
                select(User).where(User.username == "p@example.com")
            )
        assert user is not None and user.password_hash is not None
        assert "password123" not in user.password_hash
        assert user.password_hash.startswith("$2b$")


class TestSessionCookie:
    async def test_marked_secure_over_https(self, user_factory):
        """Over TLS the session cookie must carry Secure, or a browser
        will happily replay it over plain HTTP."""
        import httpx

        import main

        await user_factory()
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="https://test"
        ) as tls_client:
            res = await tls_client.post(
                "/api/auth/login",
                json={"email": "a@example.com", "password": "password123"},
            )
        assert res.status_code == 200
        assert "secure" in res.headers["set-cookie"].lower()

    async def test_not_secure_over_plain_http(self, client, user_factory):
        """...but local dev over http still has to work, so don't set it
        unconditionally — the browser would drop the cookie entirely."""
        await user_factory()
        res = await client.post(
            "/api/auth/login",
            json={"email": "a@example.com", "password": "password123"},
        )
        assert res.status_code == 200
        assert "secure" not in res.headers["set-cookie"].lower()

    async def test_always_httponly(self, client, user_factory):
        await user_factory()
        res = await client.post(
            "/api/auth/login",
            json={"email": "a@example.com", "password": "password123"},
        )
        assert "httponly" in res.headers["set-cookie"].lower()


class TestIpBan:
    """The per-account limit alone lets one address spray a password
    across account after account; these cover the per-IP ban that stops
    it, and the LAN exemption that keeps it from locking out the house."""

    HEADERS = {"X-Forwarded-For": "8.8.8.8"}

    async def _fail_login(self, client, email="a@example.com", headers=None):
        return await client.post(
            "/api/auth/login",
            json={"email": email, "password": "wrong"},
            headers=self.HEADERS if headers is None else headers,
        )

    async def test_spraying_many_accounts_gets_the_ip_banned(
        self, client, user_factory
    ):
        """Each account stays under its own limit, but the address
        doesn't."""
        for i in range(auth.MAX_IP_FAILS):
            await user_factory(email=f"user{i}@example.com")
            res = await self._fail_login(client, f"user{i}@example.com")
            assert res.status_code == 401, f"attempt {i} should be a plain refusal"

        await user_factory(email="next@example.com")
        res = await self._fail_login(client, "next@example.com")
        assert res.status_code == 429

    async def test_ban_blocks_even_the_correct_password(self, client, user_factory):
        await user_factory()
        for i in range(auth.MAX_IP_FAILS):
            await self._fail_login(client, f"ghost{i}@example.com")
        res = await client.post(
            "/api/auth/login",
            json={"email": "a@example.com", "password": "password123"},
            headers=self.HEADERS,
        )
        assert res.status_code == 429

    async def test_ban_is_scoped_to_the_offending_address(self, client, user_factory):
        await user_factory()
        for i in range(auth.MAX_IP_FAILS):
            await self._fail_login(client, f"ghost{i}@example.com")
        res = await client.post(
            "/api/auth/login",
            json={"email": "a@example.com", "password": "password123"},
            headers={"X-Forwarded-For": "9.9.9.9"},
        )
        assert res.status_code == 200

    async def test_lan_addresses_are_never_banned(self, client, user_factory):
        """One family member fat-fingering their password must not lock
        out everyone else — the router NATs them all to one address."""
        await user_factory()
        lan = {"X-Forwarded-For": "10.0.1.1"}
        for i in range(auth.MAX_IP_FAILS + 5):
            await self._fail_login(client, f"ghost{i}@example.com", headers=lan)
        res = await client.post(
            "/api/auth/login",
            json={"email": "a@example.com", "password": "password123"},
            headers=lan,
        )
        assert res.status_code == 200

    def test_ban_duration_escalates_and_is_capped(self):
        key = "ip:93.184.216.34"
        auth._bans.clear()
        durations = []
        for _ in range(8):
            for _ in range(auth.MAX_IP_FAILS):
                auth.record_ip_fail("93.184.216.34")
            expires_at, offences = auth._bans[key]
            durations.append(round(expires_at - time.time()))
            # Serve out the ban so the next round earns a fresh one.
            auth._bans[key] = (0.0, offences)

        assert durations[1] > durations[0], "a repeat offender should wait longer"
        assert max(durations) <= auth.BAN_MAX_SECONDS
        assert durations[-1] == auth.BAN_MAX_SECONDS, "should settle at the cap"

    async def test_forged_lan_header_does_not_dodge_the_ban(
        self, client, user_factory
    ):
        """A client can send its own X-Forwarded-For and a proxy appends
        to it, so the leftmost entry is attacker-controlled. Claiming to
        be on the LAN must not buy an exemption."""
        await user_factory()
        forged = {"X-Forwarded-For": "10.0.1.1, 8.8.8.8"}
        for i in range(auth.MAX_IP_FAILS):
            await self._fail_login(client, f"ghost{i}@example.com", headers=forged)
        res = await client.post(
            "/api/auth/login",
            json={"email": "a@example.com", "password": "password123"},
            headers=forged,
        )
        assert res.status_code == 429, "should be banned as 8.8.8.8, not exempt"

    def test_unparseable_address_is_not_treated_as_lan(self):
        assert auth.is_lan_address("not-an-ip") is False
        assert auth.is_lan_address("") is False
        assert auth.is_lan_address("10.0.1.1") is True
        assert auth.is_lan_address("192.168.1.5") is True
        assert auth.is_lan_address("127.0.0.1") is True
        assert auth.is_lan_address("8.8.8.8") is False


class TestLogin:
    async def test_correct_password(self, client, user_factory):
        await user_factory()
        res = await client.post(
            "/api/auth/login",
            json={"email": "a@example.com", "password": "password123"},
        )
        assert res.status_code == 200

    async def test_wrong_password(self, client, user_factory):
        await user_factory()
        res = await client.post(
            "/api/auth/login", json={"email": "a@example.com", "password": "nope"}
        )
        assert res.status_code == 401

    async def test_unknown_account_looks_the_same(self, client):
        res = await client.post(
            "/api/auth/login",
            json={"email": "ghost@example.com", "password": "whatever"},
        )
        assert res.status_code == 401
        assert res.json()["error"] == "invalid credentials"

    async def test_logout_invalidates_the_session(self, client, logged_in):
        await logged_in()
        assert (await client.get("/api/babies")).status_code == 200
        await client.post("/api/auth/logout")
        assert (await client.get("/api/babies")).status_code == 401


class TestLoginThrottle:
    async def _fail(self, client, email="a@example.com"):
        return await client.post(
            "/api/auth/login", json={"email": email, "password": "wrong"}
        )

    async def test_locks_out_after_the_limit(self, client, user_factory):
        await user_factory()
        for _ in range(auth.MAX_LOGIN_FAILS):
            assert (await self._fail(client)).status_code == 401
        assert (await self._fail(client)).status_code == 429

    async def test_lockout_blocks_even_the_right_password(self, client, user_factory):
        await user_factory()
        for _ in range(auth.MAX_LOGIN_FAILS):
            await self._fail(client)
        res = await client.post(
            "/api/auth/login",
            json={"email": "a@example.com", "password": "password123"},
        )
        assert res.status_code == 429

    async def test_is_scoped_per_account(self, client, user_factory):
        """One account being attacked must not lock everyone else out."""
        await user_factory(email="victim@example.com")
        await user_factory(email="bystander@example.com")
        for _ in range(auth.MAX_LOGIN_FAILS + 1):
            await self._fail(client, "victim@example.com")
        res = await client.post(
            "/api/auth/login",
            json={"email": "bystander@example.com", "password": "password123"},
        )
        assert res.status_code == 200

    async def test_success_clears_the_counter(self, client, user_factory):
        await user_factory()
        for _ in range(auth.MAX_LOGIN_FAILS - 1):
            await self._fail(client)
        ok = await client.post(
            "/api/auth/login",
            json={"email": "a@example.com", "password": "password123"},
        )
        assert ok.status_code == 200
        assert (await self._fail(client)).status_code == 401  # not 429


class TestTotp:
    async def _enrolled(self, client, logged_in):
        await logged_in()
        secret = (await client.post("/api/auth/totp/setup")).json()["secret"]
        code = pyotp.TOTP(secret).now()
        assert (
            await client.post("/api/auth/totp/confirm", json={"code": code})
        ).status_code == 200
        await client.post("/api/auth/logout")
        return secret

    async def test_login_requires_a_second_factor(self, client, logged_in):
        await self._enrolled(client, logged_in)
        res = await client.post(
            "/api/auth/login",
            json={"email": "a@example.com", "password": "password123"},
        )
        assert res.json().get("totp_required") is True
        # The password alone must not have granted a session.
        assert (await client.get("/api/babies")).status_code == 401

    async def test_correct_code_completes_login(self, client, logged_in):
        secret = await self._enrolled(client, logged_in)
        pending = (
            await client.post(
                "/api/auth/login",
                json={"email": "a@example.com", "password": "password123"},
            )
        ).json()["pending_token"]
        res = await client.post(
            "/api/auth/totp/verify",
            json={"pending_token": pending, "code": pyotp.TOTP(secret).now()},
        )
        assert res.status_code == 200
        assert (await client.get("/api/babies")).status_code == 200

    async def test_a_typo_can_be_retried(self, client, logged_in):
        secret = await self._enrolled(client, logged_in)
        pending = (
            await client.post(
                "/api/auth/login",
                json={"email": "a@example.com", "password": "password123"},
            )
        ).json()["pending_token"]
        bad = await client.post(
            "/api/auth/totp/verify",
            json={"pending_token": pending, "code": "000000"},
        )
        assert bad.status_code == 401
        good = await client.post(
            "/api/auth/totp/verify",
            json={"pending_token": pending, "code": pyotp.TOTP(secret).now()},
        )
        assert good.status_code == 200

    async def test_guessing_is_capped(self, client, logged_in):
        """Retries are allowed, so the attempt count is what stops a
        6-digit code being brute-forced within the token's lifetime."""
        secret = await self._enrolled(client, logged_in)
        pending = (
            await client.post(
                "/api/auth/login",
                json={"email": "a@example.com", "password": "password123"},
            )
        ).json()["pending_token"]
        for _ in range(auth.MAX_TOTP_FAILS):
            res = await client.post(
                "/api/auth/totp/verify",
                json={"pending_token": pending, "code": "000000"},
            )
            assert res.status_code == 401
        assert (
            await client.post(
                "/api/auth/totp/verify",
                json={"pending_token": pending, "code": "000000"},
            )
        ).status_code == 429
        # The burned token must not accept the real code either.
        after = await client.post(
            "/api/auth/totp/verify",
            json={"pending_token": pending, "code": pyotp.TOTP(secret).now()},
        )
        assert after.status_code == 400

    async def test_disable_requires_the_password(self, client, logged_in):
        secret = await self._enrolled(client, logged_in)
        pending = (
            await client.post(
                "/api/auth/login",
                json={"email": "a@example.com", "password": "password123"},
            )
        ).json()["pending_token"]
        await client.post(
            "/api/auth/totp/verify",
            json={"pending_token": pending, "code": pyotp.TOTP(secret).now()},
        )
        assert (
            await client.post("/api/auth/totp/disable", json={"password": "wrong"})
        ).status_code == 401
        assert (
            await client.post(
                "/api/auth/totp/disable", json={"password": "password123"}
            )
        ).status_code == 200


class TestApiTokens:
    async def test_token_authenticates_without_a_cookie(self, client, logged_in):
        await logged_in()
        token = (
            await client.post("/api/auth/tokens", json={"name": "script"})
        ).json()["token"]
        client.cookies.clear()
        assert (await client.get("/api/babies")).status_code == 401
        res = await client.get(
            "/api/babies", headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200

    async def test_raw_token_is_never_listed(self, client, logged_in):
        await logged_in()
        created = (
            await client.post("/api/auth/tokens", json={"name": "script"})
        ).json()
        listed = (await client.get("/api/auth/tokens")).json()
        assert created["token"] not in str(listed)
        assert listed[0]["prefix"] in created["token"]

    async def test_only_the_hash_is_stored(self, client, logged_in):
        await logged_in()
        token = (
            await client.post("/api/auth/tokens", json={"name": "script"})
        ).json()["token"]
        from sqlalchemy import select

        from db import ApiToken, Session

        async with Session() as session:
            row = await session.scalar(select(ApiToken))
        assert row is not None
        assert row.token_hash == auth.hash_token(token)
        assert token not in row.token_hash

    async def test_revoked_token_stops_working(self, client, logged_in):
        await logged_in()
        created = (
            await client.post("/api/auth/tokens", json={"name": "script"})
        ).json()
        await client.delete(f"/api/auth/tokens/{created['id']}")
        client.cookies.clear()
        res = await client.get(
            "/api/babies", headers={"Authorization": f"Bearer {created['token']}"}
        )
        assert res.status_code == 401

    async def test_garbage_bearer_is_rejected(self, client):
        res = await client.get(
            "/api/babies", headers={"Authorization": "Bearer ib_nonsense"}
        )
        assert res.status_code == 401

    async def test_cannot_revoke_someone_elses_token(
        self, client, logged_in, user_factory
    ):
        other = await user_factory(email="other@example.com")
        from db import ApiToken, Session

        raw, token_hash, prefix = auth.generate_api_token()
        async with Session.begin() as session:
            row = ApiToken(
                user_id=other, name="theirs", token_hash=token_hash, prefix=prefix
            )
            session.add(row)
            await session.flush()
            other_token_id = row.id

        await logged_in()
        await client.delete(f"/api/auth/tokens/{other_token_id}")
        client.cookies.clear()
        # Still valid: the delete must have been a no-op.
        res = await client.get(
            "/api/babies", headers={"Authorization": f"Bearer {raw}"}
        )
        assert res.status_code == 200


class TestShowNoteFields:
    async def test_on_by_default(self, client, logged_in):
        await logged_in()
        me = (await client.get("/api/auth/me")).json()
        assert me["show_note_fields"] is True

    async def test_can_turn_off_and_on(self, client, logged_in):
        await logged_in()
        assert (
            await client.put("/api/auth/show-notes", json={"show_note_fields": False})
        ).status_code == 200
        assert (
            await client.get("/api/auth/me")
        ).json()["show_note_fields"] is False

        assert (
            await client.put("/api/auth/show-notes", json={"show_note_fields": True})
        ).status_code == 200
        assert (
            await client.get("/api/auth/me")
        ).json()["show_note_fields"] is True

    async def test_needs_a_session(self, client):
        res = await client.put("/api/auth/show-notes", json={"show_note_fields": False})
        assert res.status_code == 401
