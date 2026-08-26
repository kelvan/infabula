"""Local-day and write-window logic.

This is where the production bug lived: entry times are UTC instants but
users think in local days, and getting the conversion wrong silently
refuses every save or files entries under the wrong date.
"""

from datetime import timedelta

import main


def test_stored_form_is_utc_with_z():
    assert main.to_entry_ts(main.utc_now()).endswith("Z")
    assert len(main.to_entry_ts(main.utc_now())) == len("2026-08-26T05:23Z")


def test_parse_rejects_naive_timestamps():
    """A naive wall-clock string is ambiguous; the API must not accept it."""
    assert main.parse_entry_ts("2026-08-26T07:23") is None
    assert main.parse_entry_ts("garbage") is None
    assert main.parse_entry_ts("") is None
    assert main.parse_entry_ts(None) is None


def test_parse_roundtrips():
    moment = main.parse_entry_ts("2026-08-26T05:23Z")
    assert main.to_entry_ts(moment) == "2026-08-26T05:23Z"


class TestLocalDay:
    def test_summer_instant_maps_to_local_day(self):
        # 05:23Z is 07:23 in Vienna (CEST, +2) — same date.
        assert main.local_day_of("2026-08-26T05:23Z") == "2026-08-26"

    def test_late_evening_local_is_previous_utc_day(self):
        # 21:00 local on the 25th is 19:00Z the same day.
        assert main.local_day_of("2026-08-25T19:00Z") == "2026-08-25"

    def test_after_local_midnight_rolls_over(self):
        # 22:00Z is exactly local midnight -> belongs to the next day.
        assert main.local_day_of("2026-08-25T21:59Z") == "2026-08-25"
        assert main.local_day_of("2026-08-25T22:00Z") == "2026-08-26"

    def test_early_morning_local_is_previous_utc_day(self):
        # 04:30Z is 06:30 local — the far end of an overnight sleep.
        assert main.local_day_of("2026-08-26T04:30Z") == "2026-08-26"

    def test_winter_offset_differs_from_summer(self):
        # CET (+1) in January, CEST (+2) in August.
        assert main.local_day_of("2026-01-15T23:30Z") == "2026-01-16"
        assert main.local_day_of("2026-08-15T23:30Z") == "2026-08-16"

    def test_local_time_rendering(self):
        assert main.local_time_of("2026-08-25T19:00Z") == "21:00"
        assert main.local_time_of("2026-01-15T19:00Z") == "20:00"


class TestDayBounds:
    def _hours(self, day):
        lo, hi = main.local_day_bounds(day)
        return (
            main.parse_entry_ts(hi) - main.parse_entry_ts(lo)
        ).total_seconds() / 3600

    def test_normal_day_is_24h(self):
        assert self._hours("2026-08-26") == 24

    def test_spring_forward_day_is_23h(self):
        """Built from both local midnights, not start + 24h."""
        assert self._hours("2026-03-29") == 23

    def test_fall_back_day_is_25h(self):
        assert self._hours("2026-10-25") == 25

    def test_bounds_are_half_open_and_meet(self):
        _, first_end = main.local_day_bounds("2026-08-25")
        second_start, _ = main.local_day_bounds("2026-08-26")
        assert first_end == second_start

    def test_invalid_date_returns_none(self):
        assert main.local_day_bounds("not-a-date") is None
        assert main.local_day_bounds("") is None

    def test_every_instant_lands_in_exactly_one_day(self):
        """No gaps or overlaps across a DST switch."""
        for day in ("2026-03-28", "2026-03-29", "2026-03-30"):
            lo, hi = main.local_day_bounds(day)
            assert main.local_day_of(lo) == day
            # The closing bound belongs to the *next* day, not this one.
            assert main.local_day_of(hi) != day


class TestWriteWindow:
    def _ts(self, **delta):
        return main.to_entry_ts(main.utc_now() + timedelta(**delta))

    def test_now_is_allowed(self):
        assert main.check_entry_window(self._ts()) is None

    def test_slightly_ahead_is_allowed(self):
        assert main.check_entry_window(self._ts(minutes=30)) is None

    def test_too_far_ahead_is_refused(self):
        assert main.check_entry_window(self._ts(hours=2)) is not None

    def test_within_the_last_week_is_allowed(self):
        assert main.check_entry_window(self._ts(days=-3)) is None

    def test_older_than_a_week_is_refused(self):
        assert main.check_entry_window(self._ts(days=-10)) is not None

    def test_naive_timestamp_is_refused(self):
        assert main.check_entry_window("2026-08-26T07:23") is not None

    def test_editing_may_reach_further_back(self):
        """A PATCH adds no rows, so an old entry stays fixable."""
        assert main.check_entry_window(self._ts(days=-30), allow_old=True) is None

    def test_editing_still_refuses_the_far_future(self):
        assert (
            main.check_entry_window(self._ts(hours=5), allow_old=True) is not None
        )
