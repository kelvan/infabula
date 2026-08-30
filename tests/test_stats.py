"""/api/stats: average sleep duration and average awake time between
sleeps, computed over the last 10 completed sleeps."""

from db import Entry, Session


async def add_sleep(baby_id, start, end):
    async with Session.begin() as session:
        session.add(
            Entry(baby_id=baby_id, type="sleep", ts_start=start, ts_end=end, meta={})
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
