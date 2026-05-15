# nldate

A Python library that parses natural-language date strings into `datetime.date` objects.

## Installation

```bash
uv sync
```

## Usage

```python
from datetime import date
from nldate import parse

# Absolute dates
parse("December 1st, 2025")          # date(2025, 12, 1)
parse("2025-12-01")                  # date(2025, 12, 1)
parse("Jan 5, 2026")                 # date(2026, 1, 5)

# Relative anchors
parse("today")                       # date.today()
parse("tomorrow")
parse("yesterday")

# Weekday navigation
parse("next Tuesday")
parse("last Monday")
parse("this Friday")

# Offsets
parse("in 3 days")
parse("in two weeks")
parse("in 1 year and 2 months")
parse("3 days ago")
parse("two weeks ago")
parse("5 days before December 1st, 2025")
parse("2 weeks after tomorrow")
parse("1 year and 2 months after yesterday")

# Provide your own reference date
parse("next Tuesday", today=date(2025, 6, 11))
```

## Development

```bash
# Run tests
uv run pytest

# Type check
uv run mypy nldate

# Lint
uv run ruff check nldate tests
```
