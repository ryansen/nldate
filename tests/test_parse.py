"""Test suite for nldate.parse()."""

from datetime import date

import pytest

from nldate import parse

# Fixed reference date for all relative tests
TODAY = date(2025, 6, 11)  # Wednesday, June 11 2025


# ---------------------------------------------------------------------------
# Absolute dates
# ---------------------------------------------------------------------------


def test_iso_format() -> None:
    assert parse("2025-12-01", today=TODAY) == date(2025, 12, 1)


def test_us_slash_format() -> None:
    assert parse("12/1/2025", today=TODAY) == date(2025, 12, 1)


def test_month_name_day_year() -> None:
    assert parse("December 1st, 2025", today=TODAY) == date(2025, 12, 1)


def test_month_name_day_year_no_comma() -> None:
    assert parse("March 15 2026", today=TODAY) == date(2026, 3, 15)


def test_abbreviated_month() -> None:
    assert parse("Jan 5, 2026", today=TODAY) == date(2026, 1, 5)


def test_day_month_name_year() -> None:
    assert parse("1 December 2025", today=TODAY) == date(2025, 12, 1)


def test_month_day_no_year_future() -> None:
    # August 20 is still in the future relative to TODAY (June 11)
    assert parse("August 20", today=TODAY) == date(2025, 8, 20)


def test_month_day_no_year_wraps_to_next_year() -> None:
    # January 1 is already past (TODAY is June 11) → next year
    assert parse("January 1", today=TODAY) == date(2026, 1, 1)


# ---------------------------------------------------------------------------
# Anchor words
# ---------------------------------------------------------------------------


def test_today() -> None:
    assert parse("today", today=TODAY) == TODAY


def test_tomorrow() -> None:
    assert parse("tomorrow", today=TODAY) == date(2025, 6, 12)


def test_yesterday() -> None:
    assert parse("yesterday", today=TODAY) == date(2025, 6, 10)


# ---------------------------------------------------------------------------
# next / last / this + weekday
# ---------------------------------------------------------------------------


def test_next_tuesday() -> None:
    # TODAY is Wednesday June 11 → next Tuesday is June 17
    assert parse("next Tuesday", today=TODAY) == date(2025, 6, 17)


def test_next_monday() -> None:
    # TODAY is Wednesday → next Monday is June 16
    assert parse("next Monday", today=TODAY) == date(2025, 6, 16)


def test_last_monday() -> None:
    # TODAY is Wednesday June 11 → last Monday is June 9
    assert parse("last Monday", today=TODAY) == date(2025, 6, 9)


def test_last_friday() -> None:
    # TODAY is Wednesday June 11 → last Friday is June 6
    assert parse("last Friday", today=TODAY) == date(2025, 6, 6)


def test_this_friday() -> None:
    # TODAY is Wednesday → this Friday is June 13
    assert parse("this Friday", today=TODAY) == date(2025, 6, 13)


def test_this_wednesday() -> None:
    # TODAY is Wednesday → this Wednesday is same day
    assert parse("this Wednesday", today=TODAY) == date(2025, 6, 11)


# ---------------------------------------------------------------------------
# next/last month, week, year
# ---------------------------------------------------------------------------


def test_next_month() -> None:
    assert parse("next month", today=TODAY) == date(2025, 7, 11)


def test_last_month() -> None:
    assert parse("last month", today=TODAY) == date(2025, 5, 11)


def test_next_year() -> None:
    assert parse("next year", today=TODAY) == date(2026, 6, 11)


def test_last_year() -> None:
    assert parse("last year", today=TODAY) == date(2024, 6, 11)


def test_next_week() -> None:
    assert parse("next week", today=TODAY) == date(2025, 6, 18)


def test_last_week() -> None:
    assert parse("last week", today=TODAY) == date(2025, 6, 4)


# ---------------------------------------------------------------------------
# "in N units" / "N units from now"
# ---------------------------------------------------------------------------


def test_in_3_days() -> None:
    assert parse("in 3 days", today=TODAY) == date(2025, 6, 14)


def test_in_two_weeks() -> None:
    assert parse("in two weeks", today=TODAY) == date(2025, 6, 25)


def test_in_1_year_and_2_months() -> None:
    assert parse("in 1 year and 2 months", today=TODAY) == date(2026, 8, 11)


def test_in_6_months() -> None:
    assert parse("in 6 months", today=TODAY) == date(2025, 12, 11)


def test_3_days_from_now() -> None:
    assert parse("3 days from now", today=TODAY) == date(2025, 6, 14)


def test_two_weeks_from_today() -> None:
    assert parse("two weeks from today", today=TODAY) == date(2025, 6, 25)


def test_1_week_from_tomorrow() -> None:
    assert parse("1 week from tomorrow", today=TODAY) == date(2025, 6, 19)


# ---------------------------------------------------------------------------
# "N units ago"
# ---------------------------------------------------------------------------


def test_3_days_ago() -> None:
    assert parse("3 days ago", today=TODAY) == date(2025, 6, 8)


def test_two_weeks_ago() -> None:
    assert parse("two weeks ago", today=TODAY) == date(2025, 5, 28)


def test_1_month_ago() -> None:
    assert parse("1 month ago", today=TODAY) == date(2025, 5, 11)


def test_1_year_ago() -> None:
    assert parse("1 year ago", today=TODAY) == date(2024, 6, 11)


# ---------------------------------------------------------------------------
# "N units before/after <anchor>"
# ---------------------------------------------------------------------------


def test_5_days_before_date() -> None:
    assert parse("5 days before December 1st, 2025", today=TODAY) == date(2025, 11, 26)


def test_2_weeks_after_tomorrow() -> None:
    assert parse("2 weeks after tomorrow", today=TODAY) == date(2025, 6, 26)


def test_1_year_and_2_months_after_yesterday() -> None:
    assert parse("1 year and 2 months after yesterday", today=TODAY) == date(2026, 8, 10)


def test_3_days_before_next_monday() -> None:
    assert parse("3 days before next Monday", today=TODAY) == date(2025, 6, 13)


def test_10_days_after_january_1_2026() -> None:
    assert parse("10 days after January 1 2026", today=TODAY) == date(2026, 1, 11)


# ---------------------------------------------------------------------------
# "N units later/earlier/hence"
# ---------------------------------------------------------------------------


def test_3_days_later() -> None:
    assert parse("3 days later", today=TODAY) == date(2025, 6, 14)


def test_2_weeks_earlier() -> None:
    assert parse("2 weeks earlier", today=TODAY) == date(2025, 5, 28)


def test_1_month_hence() -> None:
    assert parse("1 month hence", today=TODAY) == date(2025, 7, 11)


# ---------------------------------------------------------------------------
# End/start of month
# ---------------------------------------------------------------------------


def test_end_of_month() -> None:
    assert parse("end of month", today=TODAY) == date(2025, 6, 30)


def test_end_of_the_month() -> None:
    assert parse("end of the month", today=TODAY) == date(2025, 6, 30)


def test_start_of_month() -> None:
    assert parse("start of month", today=TODAY) == date(2025, 6, 1)


def test_beginning_of_the_month() -> None:
    assert parse("beginning of the month", today=TODAY) == date(2025, 6, 1)


# ---------------------------------------------------------------------------
# Default today
# ---------------------------------------------------------------------------


def test_today_default() -> None:
    """parse('today') with no today param should return date.today()."""
    assert parse("today") == date.today()


# ---------------------------------------------------------------------------
# Word numbers
# ---------------------------------------------------------------------------


def test_word_number_five_days() -> None:
    assert parse("five days from now", today=TODAY) == date(2025, 6, 16)


def test_word_number_a_week() -> None:
    assert parse("a week from today", today=TODAY) == date(2025, 6, 18)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_invalid_string_raises() -> None:
    with pytest.raises(ValueError):
        parse("not a date at all zzz", today=TODAY)


def test_empty_string_raises() -> None:
    with pytest.raises(ValueError):
        parse("", today=TODAY)
