"""rhythm_alerts: which wake / bottle reminders are due right now, and
the push subscribe / opt-in endpoints."""

from sqlalchemy import select

import main
from db import PushSubscription, Session
from main import rhythm_alerts

RHYTHM = {
    "sleep": [
        {"start": "09:00", "end": "11:00", "prob": 0.5, "days": 10},
        {"start": "19:30", "end": "07:00", "prob": 0.9, "days": 14},
    ],
    "feeds": [
        {"time": "07:00", "ml": 120, "days": 12},
        {"time": "13:00", "ml": 110, "days": 11},
        {"time": "18:00", "ml": 130, "days": 12},
    ],
}


def kinds(alerts):
    return {a["kind"] for a in alerts}


class TestWakeReminder:
    def test_fires_shortly_before_the_typical_wake(self):
        a = rhythm_alerts(RHYTHM, now_min=10 * 60 + 50, open_sleep=True,
                          last_bottle_min_ago=200)
        assert any(x["kind"] == "wake" and x["at"] == "11:00" for x in a)

    def test_quiet_when_the_wake_time_is_still_far_off(self):
        a = rhythm_alerts(RHYTHM, now_min=9 * 60 + 30, open_sleep=True,
                          last_bottle_min_ago=200)
        assert "wake" not in kinds(a)

    def test_only_while_actually_asleep(self):
        a = rhythm_alerts(RHYTHM, now_min=10 * 60 + 50, open_sleep=False,
                          last_bottle_min_ago=200)
        assert "wake" not in kinds(a)

    def test_ignores_a_sleep_outside_any_typical_window(self):
        # asleep at noon — no window covers it
        a = rhythm_alerts(RHYTHM, now_min=12 * 60, open_sleep=True,
                          last_bottle_min_ago=200)
        assert "wake" not in kinds(a)

    def test_works_for_the_night_window_across_midnight(self):
        a = rhythm_alerts(RHYTHM, now_min=6 * 60 + 50, open_sleep=True,
                          last_bottle_min_ago=400)
        assert any(x["kind"] == "wake" and x["at"] == "07:00" for x in a)


class TestBottleReminder:
    def test_fires_shortly_before_a_typical_bottle(self):
        a = rhythm_alerts(RHYTHM, now_min=12 * 60 + 45, open_sleep=False,
                          last_bottle_min_ago=240)
        assert any(x["kind"] == "bottle" and x["at"] == "13:00"
                   and x["ml"] == 110 for x in a)

    def test_suppressed_right_after_a_bottle(self):
        a = rhythm_alerts(RHYTHM, now_min=12 * 60 + 45, open_sleep=False,
                          last_bottle_min_ago=30)
        assert "bottle" not in kinds(a)

    def test_fires_when_there_is_no_bottle_history(self):
        a = rhythm_alerts(RHYTHM, now_min=12 * 60 + 45, open_sleep=False,
                          last_bottle_min_ago=None)
        assert "bottle" in kinds(a)

    def test_quiet_between_typical_bottle_times(self):
        a = rhythm_alerts(RHYTHM, now_min=15 * 60, open_sleep=False,
                          last_bottle_min_ago=200)
        assert "bottle" not in kinds(a)


class TestNotifyEndpoints:
    async def test_me_reports_the_opt_in(self, client, logged_in):
        await logged_in()
        me = (await client.get("/api/auth/me")).json()
        assert me["notify_rhythm"] is False

    async def test_toggle_opt_in(self, client, logged_in):
        await logged_in()
        assert (
            await client.put("/api/auth/notify", json={"notify_rhythm": True})
        ).status_code == 200
        assert (await client.get("/api/auth/me")).json()["notify_rhythm"] is True

    async def test_push_config_shape(self, client, logged_in):
        await logged_in()
        cfg = (await client.get("/api/push/config")).json()
        assert set(cfg) == {"enabled", "vapid_key"}

    async def test_subscribe_needs_push_configured(self, client, logged_in):
        await logged_in()
        res = await client.post(
            "/api/push/subscribe",
            json={"endpoint": "https://x/y", "keys": {"p256dh": "a", "auth": "b"}},
        )
        assert res.status_code == 503  # no VAPID in the test env

    async def test_subscribe_and_unsubscribe_when_enabled(
        self, client, logged_in, monkeypatch
    ):
        monkeypatch.setattr(main, "PUSH_ENABLED", True)
        await logged_in()
        sub = {
            "endpoint": "https://push.example/abc",
            "keys": {"p256dh": "key-p", "auth": "key-a"},
            "lang": "de",
        }
        assert (await client.post("/api/push/subscribe", json=sub)).status_code == 200
        # idempotent
        assert (await client.post("/api/push/subscribe", json=sub)).status_code == 200
        assert (
            await client.post(
                "/api/push/unsubscribe", json={"endpoint": sub["endpoint"]}
            )
        ).status_code == 200


class TestNotifyTick:
    """Wires an alert through to the right subscribers. The time maths is
    covered by rhythm_alerts above; here that is stubbed."""

    @staticmethod
    def _stub(monkeypatch, alerts):
        monkeypatch.setattr(main, "PUSH_ENABLED", True)
        monkeypatch.setattr(main, "rhythm_alerts", lambda *a, **k: list(alerts))

        async def fake_rhythm(_baby_id):
            return {"days_analyzed": 20, "sleep": [], "feeds": []}

        monkeypatch.setattr(main, "_rhythm_cached", fake_rhythm)
        main._alert_sent_at.clear()

    async def _opt_in(self, client, logged_in, baby_factory):
        owner = await logged_in()
        baby_id = await baby_factory(owner)
        await client.put("/api/auth/notify", json={"notify_rhythm": True})
        await client.post(
            "/api/push/subscribe",
            json={
                "endpoint": "https://push.example/x",
                "keys": {"p256dh": "a", "auth": "b"},
                "lang": "en",
            },
        )
        return baby_id

    async def test_sends_once_then_respects_the_cooldown(
        self, client, logged_in, baby_factory, monkeypatch
    ):
        sent = []

        async def fake_send(_sub, payload):
            sent.append(payload)
            return True

        self._stub(monkeypatch, [{"kind": "wake", "key": "10:00", "at": "10:00"}])
        monkeypatch.setattr(main, "push_send", fake_send)
        await self._opt_in(client, logged_in, baby_factory)

        await main._notify_tick()
        assert len(sent) == 1
        assert sent[0]["tag"].startswith("rhythm-wake")

        sent.clear()
        await main._notify_tick()
        assert sent == []

    async def test_a_dead_endpoint_is_pruned(
        self, client, logged_in, baby_factory, monkeypatch
    ):
        async def fake_send(_sub, _payload):
            return False  # 404/410 from the push service

        self._stub(
            monkeypatch,
            [{"kind": "bottle", "key": "13:00", "at": "13:00", "ml": 120}],
        )
        monkeypatch.setattr(main, "push_send", fake_send)
        await self._opt_in(client, logged_in, baby_factory)

        await main._notify_tick()
        async with Session() as session:
            left = (await session.scalars(select(PushSubscription))).all()
        assert left == []

    async def test_opted_out_users_get_nothing(
        self, client, logged_in, baby_factory, monkeypatch
    ):
        sent = []

        async def fake_send(_sub, payload):
            sent.append(payload)
            return True

        self._stub(monkeypatch, [{"kind": "wake", "key": "10:00", "at": "10:00"}])
        monkeypatch.setattr(main, "push_send", fake_send)
        await self._opt_in(client, logged_in, baby_factory)
        await client.put("/api/auth/notify", json={"notify_rhythm": False})

        await main._notify_tick()
        assert sent == []
