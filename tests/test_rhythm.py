"""compute_rhythm: typical sleep windows and bottle-feed slots learned
from history, with days that weren't really tracked left out of the
weighing."""

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from db import Entry, Session
from main import compute_rhythm

TZ = ZoneInfo("Europe/Vienna")  # UTC+2 in September
TODAY = date(2026, 9, 1)


def at(days_ago: int, hh: int, mm: int = 0) -> str:
    """A local wall-clock time N days before TODAY, as a stored UTC string."""
    d = TODAY - timedelta(days=days_ago)
    local = datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ)
    return local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def e(typ, start, end=None, **meta):
    return {"type": typ, "ts_start": start, "ts_end": end, "meta": meta}


def run(entries, **kw):
    return compute_rhythm(entries, TZ, today=TODAY, **kw)


def _hm(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


class TestUsableDays:
    def test_no_entries(self):
        r = run([])
        assert r["days_analyzed"] == 0
        assert r["sleep"] == [] and r["feeds"] == []

    def test_a_thin_day_is_skipped(self):
        entries = []
        for d in range(1, 6):  # 5 well-tracked days
            entries += [
                e("diaper", at(d, 7)),
                e("sleep", at(d, 9, 30), at(d, 11)),
                e("bottle", at(d, 12), amount=120),
                e("diaper", at(d, 18)),
            ]
        # one day with only two entries — not tracked
        entries += [e("diaper", at(6, 8)), e("diaper", at(6, 9))]
        r = run(entries)
        assert r["days_analyzed"] == 5
        assert r["days_skipped"] == 1


class TestSleepWindows:
    def _nap_days(self, n, start=(9, 30), end=(11, 0)):
        entries = []
        for d in range(1, n + 1):
            entries += [
                e("diaper", at(d, 7)),
                e("bottle", at(d, 8), amount=120),
                e("sleep", at(d, *start), at(d, *end)),
                e("bottle", at(d, 13), amount=120),
                e("diaper", at(d, 19)),
            ]
        return entries

    def test_a_recurring_nap_shows_up(self):
        r = run(self._nap_days(12))
        assert len(r["sleep"]) == 1
        w = r["sleep"][0]
        assert abs(_hm(w["start"]) - _hm("09:30")) <= 45
        assert abs(_hm(w["end"]) - _hm("11:00")) <= 45
        assert w["prob"] >= 0.6
        assert w["days"] == 12

    def test_night_sleep_wraps_midnight(self):
        entries = []
        for d in range(1, 15):
            entries += [
                e("bottle", at(d, 6, 45), amount=150),
                e("diaper", at(d, 12)),
                e("bottle", at(d, 18), amount=150),
                # asleep from 19:30 to 06:30 the next morning
                e("sleep", at(d + 1, 19, 30), at(d, 6, 30)),
            ]
        r = run(entries)
        night = max(r["sleep"], key=lambda w: _hm(w["end"]) - _hm(w["start"]) % 1440)
        assert _hm(night["start"]) >= 18 * 60  # evening
        # end runs past midnight into the small hours
        assert night["end"] < night["start"] or _hm(night["end"]) <= 8 * 60

    def test_an_untracked_afternoon_does_not_erase_the_morning_nap(self):
        """The key case: some days stop being logged before the nap.
        Those days must not count as 'awake' over the nap window."""
        entries = []
        for d in range(1, 9):  # 8 days with a clear morning nap
            entries += [
                e("diaper", at(d, 7)),
                e("bottle", at(d, 8), amount=120),
                e("sleep", at(d, 9, 30), at(d, 11)),
                e("bottle", at(d, 13), amount=120),
                e("diaper", at(d, 18)),
            ]
        for d in range(9, 13):  # 4 days logged only until ~08:30
            entries += [
                e("diaper", at(d, 7)),
                e("bottle", at(d, 8), amount=120),
                e("diaper", at(d, 8, 30)),
            ]
        r = run(entries)
        assert r["days_analyzed"] == 12
        assert any(
            abs(_hm(w["start"]) - _hm("09:30")) <= 25 for w in r["sleep"]
        ), r["sleep"]

    def test_irregular_naps_give_no_window(self):
        entries = []
        naps = [(8, 0), (10, 30), (13, 0), (15, 30), (9, 0), (12, 0), (14, 0)]
        for d in range(1, 8):
            h, m = naps[d - 1]
            entries += [
                e("diaper", at(d, 6, 30)),
                e("bottle", at(d, 7), amount=120),
                e("sleep", at(d, h, m), at(d, h + 1, m)),
                e("diaper", at(d, 20)),
            ]
        r = run(entries)
        assert r["sleep"] == []


class TestFeedSlots:
    def test_recurring_bottle_times_and_ml(self):
        entries = []
        for d in range(1, 15):
            entries += [
                e("bottle", at(d, 7, 0), amount=120),
                e("sleep", at(d, 9), at(d, 10)),
                e("bottle", at(d, 13, 0), amount=100),
                e("diaper", at(d, 18)),
            ]
        r = run(entries)
        assert len(r["feeds"]) == 2
        morning, midday = r["feeds"]
        assert abs(_hm(morning["time"]) - _hm("07:00")) <= 20
        assert morning["ml"] == 120
        assert abs(_hm(midday["time"]) - _hm("13:00")) <= 20
        assert midday["ml"] == 100

    def test_bottles_close_together_are_one_feed(self):
        entries = []
        for d in range(1, 15):
            entries += [
                e("bottle", at(d, 7, 0), amount=60),
                e("bottle", at(d, 7, 20), amount=60),  # top-up 20 min later
                e("diaper", at(d, 12)),
                e("diaper", at(d, 19)),
            ]
        r = run(entries)
        assert len(r["feeds"]) == 1
        assert abs(_hm(r["feeds"][0]["time"]) - _hm("07:00")) <= 15
        assert r["feeds"][0]["ml"] == 120  # summed, not averaged to 60

    def test_a_one_off_night_bottle_is_not_a_slot(self):
        entries = []
        for d in range(1, 15):
            entries += [
                e("bottle", at(d, 7), amount=120),
                e("diaper", at(d, 12)),
                e("bottle", at(d, 19), amount=120),
            ]
        entries += [e("bottle", at(3, 3, 0), amount=90)]  # once, at 3am
        r = run(entries)
        assert sorted(f["time"][:2] for f in r["feeds"]) == ["07", "19"]

    def test_single_bottle_days_are_ignored_for_feeds(self):
        entries = []
        for d in range(1, 13):  # one bottle a day, breastfed the rest
            entries += [
                e("bottle", at(d, 8), amount=120),
                e("diaper", at(d, 12)),
                e("diaper", at(d, 19)),
            ]
        r = run(entries)
        assert r["feeds"] == []
        assert r["days_analyzed"] == 12  # still counts toward sleep

    def test_regularity_reflects_how_often_the_slot_is_used(self):
        entries = []
        for d in range(1, 15):  # 14 bottle-fed days: 07:00 + 13:00 always
            entries += [
                e("bottle", at(d, 7), amount=120),
                e("bottle", at(d, 13), amount=110),
                e("diaper", at(d, 20)),
            ]
            entries.append(e("diaper", at(d, 22)))
            if d <= 8:  # a third feed at 20:00 on 8 of them
                entries.append(e("bottle", at(d, 20), amount=90))
        r = run(entries)
        evening = next(f for f in r["feeds"] if f["time"].startswith("20"))
        assert evening["days"] == 8
        assert 0.5 <= evening["regularity"] <= 0.65


class TestRhythmEndpoint:
    async def test_requires_access(self, client, baby_factory, logged_in):
        owner = await logged_in()
        baby_id = await baby_factory(owner)
        res = await client.get(f"/api/rhythm?baby_id={baby_id}")
        assert res.status_code == 200
        data = res.json()
        assert set(data) >= {"days_analyzed", "days_skipped", "sleep", "feeds"}

    async def test_reads_the_babys_recent_entries(
        self, client, baby_factory, logged_in
    ):
        baby_id = await baby_factory(await logged_in())
        rows = []
        for d in range(1, 13):
            day = (datetime.now(TZ) - timedelta(days=d)).strftime("%Y-%m-%d")
            for hh, typ, meta in [
                (6, "bottle", {"amount": 120}),
                (9, "sleep", {}),
                (13, "bottle", {"amount": 110}),
                (19, "diaper", {}),
            ]:
                s = f"{day}T{hh:02d}:00Z"
                end = f"{day}T{hh + 1:02d}:00Z" if typ == "sleep" else None
                rows.append(
                    Entry(
                        baby_id=baby_id,
                        type=typ,
                        ts_start=s,
                        ts_end=end,
                        meta=meta,
                    )
                )
        async with Session.begin() as session:
            session.add_all(rows)
        data = (await client.get(f"/api/rhythm?baby_id={baby_id}&tz=UTC")).json()
        assert data["days_analyzed"] >= 10
        assert len(data["feeds"]) == 2
