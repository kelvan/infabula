"""Entry writing, the anti-flooding ceilings, and day scoping."""

from datetime import timedelta

import main


def ts(**delta):
    return main.to_entry_ts(main.utc_now() + timedelta(**delta))


async def post(client, baby_id, **body):
    payload = {"type": "note", "ts_start": ts(), "note": "x", "meta": {}}
    payload.update(body)
    return await client.post(f"/api/entries?baby_id={baby_id}", json=payload)


class TestValidation:
    async def test_missing_type_is_a_400_not_a_crash(
        self, client, logged_in, baby_factory
    ):
        baby_id = await baby_factory(await logged_in())
        res = await client.post(
            f"/api/entries?baby_id={baby_id}",
            json={"ts_start": ts(), "meta": {}},
        )
        assert res.status_code == 400

    async def test_missing_entry_on_patch_is_404(self, client, logged_in):
        await logged_in()
        res = await client.patch("/api/entries/999999", json={"note": "x"})
        assert res.status_code == 404

    async def test_missing_baby_on_update_is_404(self, client, logged_in):
        """An access row pointing at a since-deleted baby — the only way
        require_access can pass with no matching Baby row.

        SQLite only: it leaves foreign keys unenforced by default, so
        that orphaned row can exist there. PostgreSQL rejects the insert
        outright, which makes the state — and this branch — unreachable.
        """
        import pytest

        from db import BabyAccess, Session, is_sqlite

        if not is_sqlite():
            pytest.skip("PostgreSQL enforces the FK, so the row can't exist")

        me = await logged_in()
        async with Session.begin() as session:
            session.add(BabyAccess(user_id=me, baby_id=999999, role="owner"))
        res = await client.put("/api/babies/999999", json={"name": "x"})
        assert res.status_code == 404

    async def test_duplicate_registration_is_409_not_500(self, client):
        body = {"email": "dup@example.com", "password": "password123"}
        first = await client.post("/api/auth/register", json=body)
        assert first.status_code == 200
        second = await client.post("/api/auth/register", json=body)
        assert second.status_code == 409

    async def test_unknown_entry_type_is_rejected(
        self, client, logged_in, baby_factory
    ):
        baby_id = await baby_factory(await logged_in())
        res = await post(client, baby_id, type="banana")
        assert res.status_code == 400

    async def test_every_real_entry_type_is_accepted(
        self, client, logged_in, baby_factory
    ):
        baby_id = await baby_factory(await logged_in())
        for entry_type in (
            "diaper", "nursing", "bottle", "sleep", "walk",
            "clothing", "note", "mood", "weight",
        ):
            res = await post(client, baby_id, type=entry_type)
            assert res.status_code == 200, entry_type

    async def test_ts_end_before_ts_start_is_rejected_on_create(
        self, client, logged_in, baby_factory
    ):
        baby_id = await baby_factory(await logged_in())
        res = await post(
            client, baby_id, type="sleep", ts_start=ts(), ts_end=ts(minutes=-5)
        )
        assert res.status_code == 400

    async def test_open_sleep_entry_has_no_ts_end_requirement(
        self, client, logged_in, baby_factory
    ):
        baby_id = await baby_factory(await logged_in())
        res = await post(client, baby_id, type="sleep", ts_end=None)
        assert res.status_code == 200

    async def test_ts_end_before_ts_start_is_rejected_on_patch(
        self, client, logged_in, baby_factory
    ):
        baby_id = await baby_factory(await logged_in())
        created = await post(client, baby_id, type="sleep", ts_end=None)
        entry_id = created.json()["id"]
        res = await client.patch(
            f"/api/entries/{entry_id}", json={"ts_end": ts(minutes=-5)}
        )
        assert res.status_code == 400

    async def test_patch_can_still_close_an_open_sleep(
        self, client, logged_in, baby_factory
    ):
        baby_id = await baby_factory(await logged_in())
        created = await post(client, baby_id, type="sleep", ts_end=None)
        entry_id = created.json()["id"]
        res = await client.patch(f"/api/entries/{entry_id}", json={"ts_end": ts()})
        assert res.status_code == 200


class TestWriteWindow:
    async def test_accepts_now(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        assert (await post(client, baby_id)).status_code == 200

    async def test_refuses_the_far_future(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        res = await post(client, baby_id, ts_start=ts(hours=2))
        assert res.status_code == 400
        assert "future" in res.json()["error"]

    async def test_refuses_the_distant_past(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        res = await post(client, baby_id, ts_start=ts(days=-10))
        assert res.status_code == 400
        assert "past" in res.json()["error"]

    async def test_refuses_a_naive_timestamp(self, client, logged_in, baby_factory):
        """The store is UTC; an ambiguous wall-clock string is not accepted."""
        baby_id = await baby_factory(await logged_in())
        res = await post(client, baby_id, ts_start="2026-08-26T07:23")
        assert res.status_code == 400

    async def test_editing_reaches_further_back_than_creating(
        self, client, logged_in, baby_factory
    ):
        baby_id = await baby_factory(await logged_in())
        entry_id = (await post(client, baby_id)).json()["id"]
        res = await client.patch(
            f"/api/entries/{entry_id}", json={"ts_start": ts(days=-30)}
        )
        assert res.status_code == 200

    async def test_editing_still_refuses_the_far_future(
        self, client, logged_in, baby_factory
    ):
        baby_id = await baby_factory(await logged_in())
        entry_id = (await post(client, baby_id)).json()["id"]
        res = await client.patch(
            f"/api/entries/{entry_id}", json={"ts_start": ts(hours=5)}
        )
        assert res.status_code == 400


class TestCeilings:
    async def test_entries_per_day_are_capped(
        self, client, logged_in, baby_factory, monkeypatch
    ):
        monkeypatch.setattr(main, "MAX_ENTRIES_PER_DAY", 3)
        baby_id = await baby_factory(await logged_in())
        for _ in range(3):
            assert (await post(client, baby_id)).status_code == 200
        res = await post(client, baby_id)
        assert res.status_code == 429

    async def test_the_cap_is_per_day_not_total(
        self, client, logged_in, baby_factory, monkeypatch
    ):
        monkeypatch.setattr(main, "MAX_ENTRIES_PER_DAY", 2)
        baby_id = await baby_factory(await logged_in())
        for _ in range(2):
            await post(client, baby_id)
        assert (await post(client, baby_id)).status_code == 429
        # Yesterday still has room.
        assert (
            await post(client, baby_id, ts_start=ts(days=-1))
        ).status_code == 200

    async def test_babies_are_capped(self, client, logged_in, monkeypatch):
        monkeypatch.setattr(main, "MAX_BABIES_PER_USER", 2)
        await logged_in()
        for i in range(2):
            assert (
                await client.post("/api/babies", json={"name": f"B{i}"})
            ).status_code == 200
        assert (
            await client.post("/api/babies", json={"name": "over"})
        ).status_code == 429

    async def test_shared_babies_do_not_use_your_allowance(
        self, client, logged_in, user_factory, baby_factory, monkeypatch
    ):
        monkeypatch.setattr(main, "MAX_BABIES_PER_USER", 1)
        other = await user_factory(email="other@example.com")
        shared = await baby_factory(other, name="Theirs")
        me = await logged_in()
        from db import BabyAccess, Session

        async with Session.begin() as session:
            session.add(BabyAccess(user_id=me, baby_id=shared, role="editor"))
        # Being an editor elsewhere must not consume an owned-baby slot.
        assert (
            await client.post("/api/babies", json={"name": "Mine"})
        ).status_code == 200

    async def test_read_limit_is_clamped(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        res = await client.get(f"/api/entries?baby_id={baby_id}&limit=999999999")
        assert res.status_code == 200


class TestDayScoping:
    async def test_entry_lands_on_its_local_day(
        self, client, logged_in, baby_factory
    ):
        """22:00Z in summer is local midnight — the next day."""
        baby_id = await baby_factory(await logged_in())
        from db import Entry, Session

        async with Session.begin() as session:
            session.add(
                Entry(
                    baby_id=baby_id,
                    type="note",
                    ts_start="2026-08-25T22:00Z",
                    meta={},
                )
            )
        on_25 = (
            await client.get(f"/api/entries?baby_id={baby_id}&date=2026-08-25")
        ).json()
        on_26 = (
            await client.get(f"/api/entries?baby_id={baby_id}&date=2026-08-26")
        ).json()
        assert len(on_25) == 0
        assert len(on_26) == 1

    async def test_overnight_span_shows_on_both_days(
        self, client, logged_in, baby_factory
    ):
        """A sleep from 21:00 to 06:30 local belongs to both dates."""
        baby_id = await baby_factory(await logged_in())
        from db import Entry, Session

        async with Session.begin() as session:
            session.add(
                Entry(
                    baby_id=baby_id,
                    type="sleep",
                    ts_start="2026-08-25T19:00Z",
                    ts_end="2026-08-26T04:30Z",
                    meta={},
                )
            )
        for day in ("2026-08-25", "2026-08-26"):
            found = (
                await client.get(f"/api/entries?baby_id={baby_id}&date={day}")
            ).json()
            assert len(found) == 1, day

    async def test_open_entry_started_yesterday_still_shows_today(
        self, client, logged_in, baby_factory
    ):
        """A sleep that started yesterday and hasn't ended yet is still
        ongoing today — it should show in today's list too, not only on
        the day it started (ts_end is None, so it can't match "today"
        the way a closed entry's end time would)."""
        baby_id = await baby_factory(await logged_in())
        from db import Entry, Session

        async with Session.begin() as session:
            session.add(
                Entry(
                    baby_id=baby_id,
                    type="sleep",
                    ts_start="2026-08-25T19:00Z",
                    ts_end=None,
                    meta={},
                )
            )
        yesterday = (
            await client.get(f"/api/entries?baby_id={baby_id}&date=2026-08-25")
        ).json()
        today = (
            await client.get(f"/api/entries?baby_id={baby_id}&date=2026-08-26")
        ).json()
        assert len(yesterday) == 1
        assert len(today) == 1

    async def test_open_entry_does_not_leak_into_days_before_it_started(
        self, client, logged_in, baby_factory
    ):
        baby_id = await baby_factory(await logged_in())
        from db import Entry, Session

        async with Session.begin() as session:
            session.add(
                Entry(
                    baby_id=baby_id,
                    type="sleep",
                    ts_start="2026-08-25T19:00Z",
                    ts_end=None,
                    meta={},
                )
            )
        before = (
            await client.get(f"/api/entries?baby_id={baby_id}&date=2026-08-24")
        ).json()
        assert len(before) == 0

    async def test_instant_entries_from_other_days_do_not_leak_in(
        self, client, logged_in, baby_factory
    ):
        """Diaper/bottle/note/mood/weight entries never set ts_end at
        all — they're instant, not an open/close pair like sleep or
        walk. A day filter that treats "ts_end is null" as "still open"
        without also checking the type would match nearly every entry
        ever logged for the baby, not just genuinely ongoing ones."""
        baby_id = await baby_factory(await logged_in())
        from db import Entry, Session

        async with Session.begin() as session:
            for day_offset, entry_type in enumerate(
                ["diaper", "bottle", "note", "mood", "weight"]
            ):
                session.add(
                    Entry(
                        baby_id=baby_id,
                        type=entry_type,
                        ts_start=f"2026-08-{20 + day_offset}T10:00Z",
                        ts_end=None,
                        meta={},
                    )
                )
        today = (
            await client.get(f"/api/entries?baby_id={baby_id}&date=2026-08-26")
        ).json()
        assert today == []

    async def test_dates_list_uses_local_days(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        from db import Entry, Session

        async with Session.begin() as session:
            for value in ("2026-08-25T22:00Z", "2026-08-25T19:00Z"):
                session.add(
                    Entry(baby_id=baby_id, type="note", ts_start=value, meta={})
                )
        days = (await client.get(f"/api/entries/dates?baby_id={baby_id}")).json()
        assert days == ["2026-08-26", "2026-08-25"]


class TestOpenSpans:
    async def test_sleep_opens_and_closes(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        created = (
            await post(client, baby_id, type="sleep", ts_end=None)
        ).json()
        open_now = (await client.get(f"/api/sleep/open?baby_id={baby_id}")).json()
        assert open_now["id"] == created["id"]

        await client.patch(
            f"/api/entries/{created['id']}", json={"ts_end": ts(minutes=1)}
        )
        assert (await client.get(f"/api/sleep/open?baby_id={baby_id}")).json() is None
