"""/api/stats: average sleep duration and average awake time between
sleeps, computed over the last 10 completed sleeps."""

from db import Entry, Session


async def add_sleep(baby_id, start, end):
    async with Session.begin() as session:
        session.add(
            Entry(baby_id=baby_id, type="sleep", ts_start=start, ts_end=end, meta={})
        )


async def add_entry(baby_id, entry_type, ts_start, meta=None):
    async with Session.begin() as session:
        session.add(
            Entry(
                baby_id=baby_id,
                type=entry_type,
                ts_start=ts_start,
                ts_end=None,
                meta=meta or {},
            )
        )


class TestSleepAverages:
    async def test_no_data_is_none_not_a_crash(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        res = await client.get(f"/api/stats?baby_id={baby_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["avg_sleep_min"] is None
        assert data["avg_awake_min"] is None

    async def test_single_sleep_has_no_awake_gap(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        await add_sleep(baby_id, "2026-08-20T10:00Z", "2026-08-20T11:00Z")
        data = (await client.get(f"/api/stats?baby_id={baby_id}")).json()
        assert data["avg_sleep_min"] == 60
        assert data["avg_awake_min"] is None

    async def test_averages_two_sleeps(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        # 60 min sleep, 120 min awake, 30 min sleep -> avg sleep 45, avg awake 120
        await add_sleep(baby_id, "2026-08-20T10:00Z", "2026-08-20T11:00Z")
        await add_sleep(baby_id, "2026-08-20T13:00Z", "2026-08-20T13:30Z")
        data = (await client.get(f"/api/stats?baby_id={baby_id}")).json()
        assert data["avg_sleep_min"] == 45
        assert data["avg_awake_min"] == 120

    async def test_open_sleep_is_excluded(self, client, logged_in, baby_factory):
        """An ongoing sleep (no ts_end) has no duration and must not be
        counted or crash the average."""
        baby_id = await baby_factory(await logged_in())
        await add_sleep(baby_id, "2026-08-20T10:00Z", "2026-08-20T11:00Z")
        await add_sleep(baby_id, "2026-08-20T13:00Z", None)
        data = (await client.get(f"/api/stats?baby_id={baby_id}")).json()
        assert data["avg_sleep_min"] == 60
        assert data["avg_awake_min"] is None

    async def test_only_last_ten_sleeps_count(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        # 11 sleeps of 10 minutes each, one 200-minute outlier furthest back
        await add_sleep(baby_id, "2026-08-10T00:00Z", "2026-08-10T03:20Z")
        for day in range(11, 22):
            await add_sleep(
                baby_id, f"2026-08-{day:02d}T10:00Z", f"2026-08-{day:02d}T10:10Z"
            )
        data = (await client.get(f"/api/stats?baby_id={baby_id}")).json()
        assert data["avg_sleep_min"] == 10

    async def test_night_sleep_is_excluded_from_the_nap_average(
        self, client, logged_in, baby_factory
    ):
        """An overnight sleep is hours long and would swamp a nap
        average that's meant to reflect actual naps."""
        baby_id = await baby_factory(await logged_in())
        await add_sleep(baby_id, "2026-08-19T21:00Z", "2026-08-20T06:00Z")  # 9h
        await add_sleep(baby_id, "2026-08-20T10:00Z", "2026-08-20T10:30Z")  # 30m nap
        await add_sleep(baby_id, "2026-08-20T13:00Z", "2026-08-20T13:30Z")  # 30m nap
        data = (await client.get(f"/api/stats?baby_id={baby_id}")).json()
        assert data["avg_sleep_min"] == 30

    async def test_night_sleep_still_bounds_an_awake_gap(
        self, client, logged_in, baby_factory
    ):
        """Excluded from the nap average, but still a real sleep event —
        the gap either side of it is a genuine awake window."""
        baby_id = await baby_factory(await logged_in())
        await add_sleep(baby_id, "2026-08-19T21:00Z", "2026-08-20T06:00Z")  # 9h
        await add_sleep(baby_id, "2026-08-20T08:00Z", "2026-08-20T08:30Z")  # 30m nap
        data = (await client.get(f"/api/stats?baby_id={baby_id}")).json()
        assert data["avg_awake_min"] == 120

    async def test_respects_a_custom_nap_threshold(
        self, client, logged_in, baby_factory
    ):
        """A baby whose threshold has been raised should count a longer
        sleep as still a nap, not night sleep."""
        baby_id = await baby_factory(await logged_in())
        await client.put(f"/api/babies/{baby_id}", json={"nap_threshold_min": 300})
        await add_sleep(baby_id, "2026-08-20T10:00Z", "2026-08-20T14:30Z")  # 4.5h
        data = (await client.get(f"/api/stats?baby_id={baby_id}")).json()
        assert data["avg_sleep_min"] == 270

    async def test_only_within_baby_scope(self, client, logged_in, baby_factory):
        me = await logged_in()
        baby_a = await baby_factory(me, name="a")
        baby_b = await baby_factory(me, name="b")
        await add_sleep(baby_a, "2026-08-20T10:00Z", "2026-08-20T20:00Z")
        await add_sleep(baby_b, "2026-08-20T10:00Z", "2026-08-20T10:05Z")
        data = (await client.get(f"/api/stats?baby_id={baby_b}")).json()
        assert data["avg_sleep_min"] == 5


class TestTotals:
    async def test_counts_every_entry_by_type(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        await add_entry(baby_id, "diaper", "2026-08-01T08:00Z")
        await add_entry(baby_id, "diaper", "2026-08-20T09:00Z")
        await add_entry(baby_id, "nursing", "2026-08-20T10:00Z")
        data = (await client.get(f"/api/stats?baby_id={baby_id}")).json()
        assert data["totals"] == {"diaper": 2, "nursing": 1}

    async def test_totals_are_baby_scoped(self, client, logged_in, baby_factory):
        me = await logged_in()
        baby_a = await baby_factory(me, name="a")
        baby_b = await baby_factory(me, name="b")
        await add_entry(baby_a, "diaper", "2026-08-20T09:00Z")
        await add_entry(baby_b, "walk", "2026-08-20T09:00Z")
        data = (await client.get(f"/api/stats?baby_id={baby_b}")).json()
        assert data["totals"] == {"walk": 1}


class TestGrowthChart:
    async def test_a_zero_height_with_no_weight_still_shows_up(
        self, client, logged_in, baby_factory
    ):
        """A truthiness check on weight/height used to drop a 0 value —
        indistinguishable from the field never having been logged."""
        baby_id = await baby_factory(await logged_in())
        await add_entry(baby_id, "weight", "2026-08-20T09:00Z", meta={"height": 0})
        data = (await client.get(f"/api/stats?baby_id={baby_id}")).json()
        assert len(data["growth"]) == 1
        assert data["growth"][0]["height"] == 0

    async def test_no_weight_and_no_height_is_excluded(
        self, client, logged_in, baby_factory
    ):
        baby_id = await baby_factory(await logged_in())
        await add_entry(baby_id, "weight", "2026-08-20T09:00Z", meta={})
        data = (await client.get(f"/api/stats?baby_id={baby_id}")).json()
        assert data["growth"] == []


class TestStatsTimezone:
    async def test_tz_param_shifts_the_day_window(
        self, client, logged_in, baby_factory
    ):
        """The household zone is Europe/Vienna (+02:00 in August): the two
        21:00/23:00 UTC diapers land on different local days, so no interval.
        Asking for UTC puts both on 2026-08-20, two hours apart."""
        baby_id = await baby_factory(await logged_in())
        await add_entry(baby_id, "diaper", "2026-08-20T21:00Z")
        await add_entry(baby_id, "diaper", "2026-08-20T23:00Z")

        household = (
            await client.get(f"/api/stats?baby_id={baby_id}&date=2026-08-20")
        ).json()
        assert "diaper" not in household["intervals"]

        utc = (
            await client.get(f"/api/stats?baby_id={baby_id}&date=2026-08-20&tz=UTC")
        ).json()
        assert utc["intervals"]["diaper"]["last"] == 120

    async def test_unknown_tz_falls_back_to_household(
        self, client, logged_in, baby_factory
    ):
        baby_id = await baby_factory(await logged_in())
        await add_entry(baby_id, "diaper", "2026-08-20T21:00Z")
        await add_entry(baby_id, "diaper", "2026-08-20T23:00Z")
        data = (
            await client.get(
                f"/api/stats?baby_id={baby_id}&date=2026-08-20&tz=Mars/Olympus"
            )
        ).json()
        assert "diaper" not in data["intervals"]
