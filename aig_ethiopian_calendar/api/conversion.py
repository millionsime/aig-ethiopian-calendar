# Public conversion API boundary (spec §7).
#
#   USER/UI -> Ethiopian -> calendar adapter -> Gregorian -> ERPNext -> DB
#
# Everything outside this package imports from here (or formatting.py).
# Nothing else in the app performs calendar math, and NO code path lets an
# Ethiopian-formatted string reach an ERPNext Date field - parsers here
# return structured tuples/ISO strings that are explicitly converted.
import datetime

from ..calendar.ethiopian import (
    ethiopic_to_gregorian as _e2g,
    gregorian_to_ethiopian as _g2e,
    EthiopianDateError,
)
from ..utils.parser import parse_ethiopian_date


def ethiopian_to_gregorian(year, month, day):
    """Ethiopian (Y, M, D) -> datetime.date. Raises EthiopianDateError."""
    return _e2g(year, month, day)


def ethiopian_to_gregorian_iso(year, month, day):
    """Ethiopian (Y, M, D) -> canonical "YYYY-MM-DD" string for Date fields."""
    return _e2g(year, month, day).isoformat()


def gregorian_to_ethiopian(gdate):
    """datetime.date / ISO string -> Ethiopian (Y, M, D) tuple."""
    if isinstance(gdate, str):
        gdate = datetime.date.fromisoformat(gdate)
    return _g2e(gdate)


def ethiopian_string_to_gregorian_iso(text):
    """User-typed Ethiopian date string -> canonical ISO Gregorian string.

    This is THE function for report/list filters and picker input:
      "23/01/2019 EC" -> "2026-09-30"
    Raises EthiopianDateError on anything unparseable or invalid.
    """
    y, m, d = parse_ethiopian_date(text)
    return _e2g(y, m, d).isoformat()


__all__ = [
    "ethiopian_to_gregorian", "ethiopian_to_gregorian_iso",
    "gregorian_to_ethiopian", "ethiopian_string_to_gregorian_iso",
    "EthiopianDateError",
]
