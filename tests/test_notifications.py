"""Emails sent for security-relevant account changes and baby access
grants — the app never sends these silently, so a change one household
member didn't make is visible to them."""

import pyotp

import mailer
import main
from db import BabyAccess, Session


def _capture(monkeypatch, fn_name):
    calls = []
    monkeypatch.setattr(mailer, fn_name, lambda *a, **kw: calls.append((a, kw)))
    return calls


class TestTotpEmails:
    async def test_enabling_sends_an_email(self, client, logged_in, monkeypatch):
        calls = _capture(monkeypatch, "send_totp_enabled_email")
        await logged_in()
        secret = (await client.post("/api/auth/totp/setup")).json()["secret"]
        code = pyotp.TOTP(secret).now()
        res = await client.post("/api/auth/totp/confirm", json={"code": code})
        assert res.status_code == 200
        assert calls == [(("a@example.com",), {})]

    async def test_disabling_sends_an_email(self, client, logged_in, monkeypatch):
        await logged_in()
        secret = (await client.post("/api/auth/totp/setup")).json()["secret"]
        await client.post(
            "/api/auth/totp/confirm", json={"code": pyotp.TOTP(secret).now()}
        )
        calls = _capture(monkeypatch, "send_totp_disabled_email")
        res = await client.post(
            "/api/auth/totp/disable", json={"password": "password123"}
        )
        assert res.status_code == 200
        assert calls == [(("a@example.com",), {})]

    async def test_a_failed_confirm_sends_no_email(
        self, client, logged_in, monkeypatch
    ):
        calls = _capture(monkeypatch, "send_totp_enabled_email")
        await logged_in()
        await client.post("/api/auth/totp/setup")
        res = await client.post("/api/auth/totp/confirm", json={"code": "000000"})
        assert res.status_code == 400
        assert calls == []


class TestPasskeyEmail:
    async def test_adding_a_passkey_sends_an_email(
        self, client, logged_in, monkeypatch
    ):
        await logged_in()
        options = (await client.post("/api/auth/passkey/register/options")).json()
        calls = _capture(monkeypatch, "send_passkey_added_email")

        class FakeVerification:
            credential_id = b"fake-id"
            credential_public_key = b"fake-key"
            sign_count = 0

        monkeypatch.setattr(
            main, "verify_registration_response", lambda **kw: FakeVerification()
        )
        res = await client.post(
            "/api/auth/passkey/register/verify",
            json={
                "challenge_token": options["challenge_token"],
                "name": "My Phone",
                "credential": {"id": "x", "rawId": "x", "type": "public-key"},
            },
        )
        assert res.status_code == 200
        assert calls == [(("a@example.com", "My Phone"), {})]


class TestAccessGrantEmails:
    async def test_new_grant_emails_both_parties(
        self, client, logged_in, user_factory, baby_factory, monkeypatch
    ):
        owner = await logged_in()
        baby_id = await baby_factory(owner)
        await user_factory(email="friend@example.com")
        granted_calls = _capture(monkeypatch, "send_access_granted_email")
        owner_calls = _capture(monkeypatch, "send_access_granted_owner_notice_email")

        res = await client.post(
            f"/api/babies/{baby_id}/access",
            json={"email": "friend@example.com", "role": "viewer"},
        )
        assert res.status_code == 200
        assert granted_calls == [(("friend@example.com", "Samuel", "viewer"), {})]
        assert owner_calls == [
            (("a@example.com", "Samuel", "friend@example.com", "viewer"), {})
        ]

    async def test_role_change_sends_no_grant_email(
        self, client, logged_in, user_factory, baby_factory, monkeypatch
    ):
        owner = await logged_in()
        baby_id = await baby_factory(owner)
        await user_factory(email="friend@example.com")
        await client.post(
            f"/api/babies/{baby_id}/access",
            json={"email": "friend@example.com", "role": "viewer"},
        )
        granted_calls = _capture(monkeypatch, "send_access_granted_email")
        owner_calls = _capture(monkeypatch, "send_access_granted_owner_notice_email")

        res = await client.post(
            f"/api/babies/{baby_id}/access",
            json={"email": "friend@example.com", "role": "editor"},
        )
        assert res.status_code == 200
        assert granted_calls == []
        assert owner_calls == []


class TestBabyCreatorProtection:
    async def test_creator_access_cannot_be_revoked(
        self, client, logged_in, baby_factory
    ):
        owner = await logged_in()
        baby_id = await baby_factory(owner)
        res = await client.delete(f"/api/babies/{baby_id}/access/{owner}")
        assert res.status_code == 400
        assert "creator" in res.json()["error"]

    async def test_creator_role_cannot_be_changed(
        self, client, logged_in, baby_factory
    ):
        owner = await logged_in()
        baby_id = await baby_factory(owner)
        res = await client.post(
            f"/api/babies/{baby_id}/access",
            json={"email": "a@example.com", "role": "editor"},
        )
        assert res.status_code == 400
        assert "creator" in res.json()["error"]

    async def test_another_owner_can_still_be_revoked(
        self, client, logged_in, user_factory, baby_factory
    ):
        owner = await logged_in()
        baby_id = await baby_factory(owner)
        co_owner = await user_factory(email="co@example.com")
        async with Session.begin() as session:
            session.add(BabyAccess(user_id=co_owner, baby_id=baby_id, role="owner"))
        res = await client.delete(f"/api/babies/{baby_id}/access/{co_owner}")
        assert res.status_code == 200
