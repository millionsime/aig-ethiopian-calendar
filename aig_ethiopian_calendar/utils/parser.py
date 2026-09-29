# Isolated Ethiopian date parser.
# ONLY explicitly-defined formats are accepted - never guess. The caller
# states the calendar context; this parser always produces Ethiopian dates.
import re

from ..calendar.constants import ETHIOPIC_MONTH_NAMES
from ..calendar.ethiopian import EthiopianDateError
from ..calendar.validation import validate_ethiopic

# 23/01/2019 | 23-01-2019 | 2019-01-23  (day-first unless year-first)
_NUMERIC = re.compile(r"^\s*(\d{1,4})[/\-.](\d{1,2})[/\-.](\d{1,4})\s*$")
# 23 Meskerem 2019 | 23 መስከረም 2019
_NAMED = re.compile(
    r"^\s*(\d{1,2})\s+([A-Za-zሀ-ፐ]+)\s+(\d{1,4})\s*$")
_EC_SUFFIX = re.compile(r"\s*(?:EC|ዓ\.?\s?ም\.?)\s*$", re.IGNORECASE)


def _resolve_month(name):
    low = name.lower()
    for i, m in enumerate(ETHIOPIC_MONTH_NAMES, start=1):
        if low == m.lower():
            return i
    for i, m in enumerate(ETHIOPIC_MONTH_NAMES, start=1):
        if low.startswith(m[:4]):
            return i
    raise EthiopianDateError(f"Unknown Ethiopian month name: {name!r}")


def parse_ethiopian_date(text, today=None):
    """Parse an explicitly-Ethiopian date string -> (Y, M, D) tuple.

    Accepted (only these, by design):
      DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY   -> day/month/year (Ethiopian)
      YYYY-MM-DD                            -> year/month/day (Ethiopian)
      "D <MonthName> YYYY"                  -> e.g. 23 Meskerem 2019
    Optional trailing "EC" / "ዓ.ም". Raises EthiopianDateError otherwise,
    including for invalid calendar dates (32 Meskerem, 6 Pagumen on a
    non-leap year, ...).
    """
    if text is None:
        raise EthiopianDateError("Empty Ethiopian date")
    if isinstance(text, (list, tuple)):
        y, m, d = text
        validate_ethiopic(y, m, d)
        return y, m, d
    s = str(text).strip()
    if not s:
        raise EthiopianDateError("Empty Ethiopian date")
    s = _EC_SUFFIX.sub("", s).strip()

    m = _NUMERIC.match(s)
    if m:
        a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if a > 31 or (len(m.group(1)) == 4):  # year-first: YYYY-MM-DD
            year, month, day = a, b, c
        else:  # day-first: DD/MM/YYYY (Ethiopian day/month, both <= 30/13)
            day, month, year = a, b, c
        validate_ethiopic(year, month, day)
        return year, month, day

    m = _NAMED.match(s)
    if m:
        day, name, year = int(m.group(1)), m.group(2), int(m.group(3))
        month = _resolve_month(name)
        validate_ethiopic(year, month, day)
        return year, month, day

    raise EthiopianDateError(
        f"Unrecognised Ethiopian date format: {text!r}. Use DD/MM/YYYY, "
        "YYYY-MM-DD or 'D <Month> YYYY'.")
