"""Natural-language date parser implementation."""

from __future__ import annotations

import re
from datetime import date, timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WEEKDAYS: dict[str, int] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

MONTHS: dict[str, int] = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

WORD_NUMBERS: dict[str, int] = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50,
    "a": 1, "an": 1,
}

# Ordinal suffixes
_ORDINAL_RE = re.compile(r"\b(\d+)(?:st|nd|rd|th)\b")


def _normalise(s: str) -> str:
    """Lowercase, strip extra whitespace, expand ordinal digits."""
    s = s.lower().strip()
    # Replace ordinal numbers like "1st" -> "1"
    s = _ORDINAL_RE.sub(r"\1", s)
    return s


def _parse_number(token: str) -> int | None:
    """Convert a word or digit string to an integer, or return None."""
    token = token.strip()
    if token.isdigit():
        return int(token)
    # Handle compound word numbers like "twenty one"
    parts = token.split()
    total = 0
    for part in parts:
        val = WORD_NUMBERS.get(part)
        if val is None:
            return None
        total += val
    return total if total >= 0 else None


def _next_weekday(ref: date, weekday: int) -> date:
    """Return the next occurrence of *weekday* (0=Mon) strictly after *ref*."""
    days_ahead = weekday - ref.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return ref + timedelta(days=days_ahead)


def _last_weekday(ref: date, weekday: int) -> date:
    """Return the most recent occurrence of *weekday* strictly before *ref*."""
    days_behind = ref.weekday() - weekday
    if days_behind <= 0:
        days_behind += 7
    return ref - timedelta(days=days_behind)


def _this_weekday(ref: date, weekday: int) -> date:
    """Return the weekday in the current week (Mon-start), or next if already past."""
    days_ahead = weekday - ref.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return ref + timedelta(days=days_ahead)


# ---------------------------------------------------------------------------
# Sub-parsers – each returns a date or None
# ---------------------------------------------------------------------------

def _try_absolute(s: str, _today: date) -> date | None:
    """Parse fully-specified dates: 'December 1st, 2025', '2025-12-01', '12/1/2025'."""
    # ISO format: YYYY-MM-DD
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # US numeric: M/D/YYYY or M-D-YYYY
    m = re.fullmatch(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", s)
    if m:
        return date(int(m.group(3)), int(m.group(1)), int(m.group(2)))

    # Month name + day + year: "December 1 2025", "Dec 1, 2025"
    m = re.fullmatch(
        r"([a-z]+)\s+(\d{1,2})(?:,)?\s+(\d{4})",
        s,
    )
    if m:
        month_num = MONTHS.get(m.group(1))
        if month_num:
            return date(int(m.group(3)), month_num, int(m.group(2)))

    # Day + Month name + year: "1 December 2025"
    m = re.fullmatch(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", s)
    if m:
        month_num = MONTHS.get(m.group(2))
        if month_num:
            return date(int(m.group(3)), month_num, int(m.group(1)))

    # Month name + day (no year) – assume current or next occurrence
    m = re.fullmatch(r"([a-z]+)\s+(\d{1,2})", s)
    if m:
        month_num = MONTHS.get(m.group(1))
        if month_num:
            day = int(m.group(2))
            year = _today.year
            candidate = date(year, month_num, day)
            if candidate < _today:
                candidate = date(year + 1, month_num, day)
            return candidate

    return None


def _try_anchor(s: str, today: date) -> date | None:
    """Handle simple anchor words: today, tomorrow, yesterday."""
    if s in ("today",):
        return today
    if s in ("tomorrow",):
        return today + timedelta(days=1)
    if s in ("yesterday",):
        return today - timedelta(days=1)
    return None


def _try_next_last_this_weekday(s: str, today: date) -> date | None:
    """Handle 'next Tuesday', 'last Monday', 'this Friday'."""
    m = re.fullmatch(r"(next|last|this)\s+([a-z]+)", s)
    if not m:
        return None
    qualifier, day_name = m.group(1), m.group(2)
    weekday = WEEKDAYS.get(day_name)
    if weekday is None:
        return None
    if qualifier == "next":
        return _next_weekday(today, weekday)
    if qualifier == "last":
        return _last_weekday(today, weekday)
    # "this"
    return _this_weekday(today, weekday)


def _try_in_n_units(s: str, today: date) -> date | None:
    """Handle 'in 3 days', 'in two weeks', 'in 1 year and 2 months'."""
    # Strip leading "in " or trailing " from now / from today"
    s = re.sub(r"^in\s+", "", s)
    s = re.sub(r"\s+from\s+(?:now|today)$", "", s)
    return _parse_offset_expression(s, today)


def _try_n_units_ago(s: str, today: date) -> date | None:
    """Handle '3 days ago', 'two weeks ago'."""
    m = re.fullmatch(r"(.+?)\s+ago", s)
    if not m:
        return None
    delta = _parse_delta(m.group(1))
    if delta is None:
        return None
    return _apply_delta(today, delta, sign=-1)


def _try_n_units_from_anchor(s: str, today: date) -> date | None:
    """Handle '3 days from now', '2 weeks from today', '1 year from tomorrow'."""
    m = re.fullmatch(r"(.+?)\s+from\s+(now|today|tomorrow|yesterday)", s)
    if not m:
        return None
    delta = _parse_delta(m.group(1))
    if delta is None:
        return None
    anchor_word = m.group(2)
    anchor = _try_anchor(anchor_word, today)
    if anchor is None:
        return None
    return _apply_delta(anchor, delta, sign=1)


def _try_offset_before_after_date(s: str, today: date) -> date | None:
    """Handle '5 days before December 1st 2025', '2 weeks after tomorrow'."""
    m = re.fullmatch(r"(.+?)\s+(before|after)\s+(.+)", s)
    if not m:
        return None
    offset_str, direction, anchor_str = m.group(1), m.group(2), m.group(3)

    delta = _parse_delta(offset_str)
    if delta is None:
        return None

    anchor = _resolve(anchor_str, today)
    if anchor is None:
        return None

    sign = 1 if direction == "after" else -1
    return _apply_delta(anchor, delta, sign=sign)


def _try_n_units_later_earlier(s: str, today: date) -> date | None:
    """Handle '3 days later', '2 weeks earlier'."""
    m = re.fullmatch(r"(.+?)\s+(later|earlier|hence)", s)
    if not m:
        return None
    delta = _parse_delta(m.group(1))
    if delta is None:
        return None
    sign = -1 if m.group(2) == "earlier" else 1
    return _apply_delta(today, delta, sign=sign)


def _try_next_last_month_year(s: str, today: date) -> date | None:
    """Handle 'next month', 'last month', 'next year', 'last year'."""
    if s == "next month":
        month = today.month + 1
        year = today.year
        if month > 12:
            month = 1
            year += 1
        return date(year, month, today.day)
    if s == "last month":
        month = today.month - 1
        year = today.year
        if month < 1:
            month = 12
            year -= 1
        return date(year, month, today.day)
    if s == "next year":
        return date(today.year + 1, today.month, today.day)
    if s == "last year":
        return date(today.year - 1, today.month, today.day)
    if s == "next week":
        return today + timedelta(weeks=1)
    if s == "last week":
        return today - timedelta(weeks=1)
    return None


def _try_end_of_month(s: str, today: date) -> date | None:
    """Handle 'end of month', 'end of the month', 'end of December 2025'."""
    m = re.fullmatch(r"end of (?:the\s+)?(?:([a-z]+)\s+)?(\d{4})?", s)
    if not m:
        if s in ("end of month", "end of the month"):
            # Last day of current month
            if today.month == 12:
                return date(today.year + 1, 1, 1) - timedelta(days=1)
            return date(today.year, today.month + 1, 1) - timedelta(days=1)
        return None
    month_name = m.group(1)
    year_str = m.group(2)
    if month_name and month_name in MONTHS:
        month_num = MONTHS[month_name]
        year = int(year_str) if year_str else today.year
        if month_num == 12:
            return date(year + 1, 1, 1) - timedelta(days=1)
        return date(year, month_num + 1, 1) - timedelta(days=1)
    return None


def _try_start_of_month(s: str, today: date) -> date | None:
    """Handle 'start of month', 'beginning of the month', etc."""
    if s in ("start of month", "start of the month",
             "beginning of month", "beginning of the month",
             "first of the month", "first of month"):
        return date(today.year, today.month, 1)
    m = re.fullmatch(
        r"(?:start|beginning) of (?:the\s+)?([a-z]+)(?:\s+(\d{4}))?", s
    )
    if m:
        month_num = MONTHS.get(m.group(1))
        if month_num:
            year = int(m.group(2)) if m.group(2) else today.year
            return date(year, month_num, 1)
    return None


# ---------------------------------------------------------------------------
# Delta parsing helpers
# ---------------------------------------------------------------------------

# Maps unit words to (days_multiplier, is_month, is_year)
_UNIT_MAP: dict[str, tuple[int, bool, bool]] = {
    "day": (1, False, False), "days": (1, False, False),
    "week": (7, False, False), "weeks": (7, False, False),
    "fortnight": (14, False, False), "fortnights": (14, False, False),
    "month": (0, True, False), "months": (0, True, False),
    "year": (0, False, True), "years": (0, False, True),
}

_COMPONENT_RE = re.compile(
    r"(\d+|(?:(?:twenty|thirty|forty|fifty)[\s\-])?(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|zero|a\b|an\b))\s+"
    r"(days?|weeks?|fortnights?|months?|years?)"
)


def _parse_delta(
    s: str,
) -> list[tuple[int, str]] | None:
    """
    Parse an offset expression like "3 days", "1 year and 2 months", "two weeks".
    Returns a list of (amount, unit) tuples or None if no match found.
    """
    s = s.strip()
    # Normalise "and" connectors
    s = re.sub(r"\s+and\s+", " ", s)
    s = re.sub(r",\s*", " ", s)

    components: list[tuple[int, str]] = []
    for m in _COMPONENT_RE.finditer(s):
        amount = _parse_number(m.group(1))
        unit = m.group(2)
        if amount is None:
            return None
        components.append((amount, unit))

    if not components:
        return None
    return components


def _apply_delta(ref: date, delta: list[tuple[int, str]], sign: int) -> date:
    """Apply a parsed delta to a reference date."""
    result = ref
    for amount, unit in delta:
        signed = sign * amount
        info = _UNIT_MAP.get(unit)
        if info is None:
            continue
        days_mult, is_month, is_year = info
        if is_year:
            result = _add_months(result, signed * 12)
        elif is_month:
            result = _add_months(result, signed)
        else:
            result = result + timedelta(days=signed * days_mult)
    return result


def _add_months(d: date, months: int) -> date:
    """Add a number of months to a date, clamping to end of month if needed."""
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    day = min(d.day, last_day)
    return date(year, month, day)


def _parse_offset_expression(s: str, today: date) -> date | None:
    """Parse a bare offset like '3 days', '1 year 2 months'."""
    delta = _parse_delta(s)
    if delta is None:
        return None
    return _apply_delta(today, delta, sign=1)


# ---------------------------------------------------------------------------
# Top-level resolver
# ---------------------------------------------------------------------------

_PARSERS = [
    _try_anchor,
    _try_next_last_this_weekday,
    _try_next_last_month_year,
    _try_end_of_month,
    _try_start_of_month,
    _try_offset_before_after_date,
    _try_n_units_ago,
    _try_n_units_from_anchor,
    _try_n_units_later_earlier,
    _try_in_n_units,
    _try_absolute,
]


def _resolve(s: str, today: date) -> date | None:
    """Try every sub-parser in order and return the first match."""
    s = _normalise(s)
    for parser in _PARSERS:
        result = parser(s, today)
        if result is not None:
            return result
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse(s: str, today: date | None = None) -> date:
    """
    Parse a natural-language date string and return a :class:`datetime.date`.

    Parameters
    ----------
    s:
        A natural-language date expression, e.g. ``"5 days before December 1st, 2025"``,
        ``"next Tuesday"``, or ``"in 3 weeks"``.
    today:
        Reference date for relative expressions.  Defaults to the current date.

    Returns
    -------
    datetime.date

    Raises
    ------
    ValueError
        If *s* cannot be parsed.
    """
    if today is None:
        today = date.today()

    result = _resolve(s, today)
    if result is None:
        raise ValueError(f"Cannot parse date string: {s!r}")
    return result
