# Core Ethiopian <-> Gregorian conversion engine.
#
# Design: the Ethiopian calendar is 13 months of exactly 30 days plus
# Pagumen (5 or 6 days). We derive conversions from a single absolute day
# count ("day number") so both directions are inverse functions of each
# other by construction - no month-walking tables that can drift.
#
# Anchors (externally verified):
#   1 Meskerem 2019 EC == 2026-09-11 GC
#   1 Meskerem 2018 EC == 2025-09-12 GC (previous year leap -> Sept 12)
#   1 Meskerem 2000 EC == 2007-09-12 GC (millennium)
#
# Day-number reference: N = 0 at 1 Meskerem 2019 EC. For any Ethiopian
# year Y, N(Y,1,1) = 365*(Y-2019) + leap_count(2019..Y-1) where a year Y
# is leap iff Y % 4 == 3 (Nikul; Pagumen has 6 days, making that year 366)
# - exactly the rule the traditional formula encodes.

import datetime

from .constants import (
    ANCHOR_EC, ANCHOR_GC, DAYS_IN_ETHIOPIC_MONTH, PAGUMEN_DAYS_COMMON,
    PAGUMEN_DAYS_LEAP, PAGUMEN_INDEX,
)


class EthiopianDateError(ValueError):
    """Raised for invalid Ethiopian (or out-of-domain) dates."""


def is_ethiopic_leap(year):
    """Ethiopian leap year (Nikul): Pagumen has 6 days. Year % 4 == 3."""
    return year % 4 == 3


def pagumen_days(year):
    return PAGUMEN_DAYS_LEAP if is_ethiopic_leap(year) else PAGUMEN_DAYS_COMMON


def days_in_ethiopic_month(year, month):
    """Length of an Ethiopian month (1-13) in the given year."""
    if month == PAGUMEN_INDEX:
        return pagumen_days(year)
    if 1 <= month <= 12:
        return DAYS_IN_ETHIOPIC_MONTH
    raise EthiopianDateError(
        f"Ethiopian month must be 1..13, got {month!r}")


def ethiopic_year_length(year):
    return 12 * DAYS_IN_ETHIOPIC_MONTH + pagumen_days(year)


def _anchor_ordinal():
    """datetime.date.toordinal() of the anchor Gregorian day (N=0)."""
    y, m, d = ANCHOR_GC
    return datetime.date(y, m, d).toordinal()


def ethiopic_to_daynumber(year, month, day):
    """Ethiopian (Y, M, D) -> absolute day number (N=0 at anchor)."""
    if not isinstance(year, int) or not isinstance(month, int) \
            or not isinstance(day, int):
        raise EthiopianDateError("Ethiopian date components must be ints")
    if year < 1:
        raise EthiopianDateError(f"Ethiopian year out of range: {year}")
    if not 1 <= month <= 13:
        raise EthiopianDateError(
            f"Ethiopian month must be 1..13, got {month}")
    if day < 1 or day > days_in_ethiopic_month(year, month):
        raise EthiopianDateError(
            f"Invalid Ethiopian date {year}-{month}-{day}: day {day} "
            f"exceeds month length {days_in_ethiopic_month(year, month)}")
    # days from 1 Meskerem 2019 to 1 Meskerem `year`
    # (common year = 365: 12x30 + 5-day Pagumen)
    years_delta = year - ANCHOR_EC[0]
    n = 365 * years_delta
    if years_delta >= 0:
        for y in range(ANCHOR_EC[0], year):
            if is_ethiopic_leap(y):
                n += 1
    else:
        for y in range(year, ANCHOR_EC[0]):
            if is_ethiopic_leap(y):
                n -= 1
    n += (month - 1) * DAYS_IN_ETHIOPIC_MONTH + (day - 1)
    return n


def daynumber_to_ethiopic(n):
    """Absolute day number -> Ethiopian (Y, M, D). Inverse of above."""
    # find the Ethiopian year by walking leap-accurate year lengths
    year = ANCHOR_EC[0]
    if n >= 0:
        while True:
            ylen = ethiopic_year_length(year)
            if n < ylen:
                break
            n -= ylen
            year += 1
    else:
        while True:
            year -= 1
            n += ethiopic_year_length(year)
            if n >= 0:
                break
    month = (n // DAYS_IN_ETHIOPIC_MONTH) + 1
    day = (n % DAYS_IN_ETHIOPIC_MONTH) + 1
    if month > 13:  # spills into Pagumen's extra days
        month = PAGUMEN_INDEX
        day = n - 12 * DAYS_IN_ETHIOPIC_MONTH + 1
    return year, month, day


def daynumber_to_gregorian(n):
    """Absolute day number -> Gregorian date. N=0 at anchor."""
    return datetime.date.fromordinal(_anchor_ordinal() + n)


def gregorian_to_daynumber(gdate):
    return gdate.toordinal() - _anchor_ordinal()


# ---------------------------------------------------------------- public API
def ethiopic_to_gregorian(year, month, day):
    """Ethiopian (Y, M, D) -> datetime.date (Gregorian). Raises on invalid."""
    return daynumber_to_gregorian(ethiopic_to_daynumber(year, month, day))


def gregorian_to_ethiopian(gdate):
    """datetime.date -> (year, month, day) Ethiopian tuple."""
    return daynumber_to_ethiopic(gregorian_to_daynumber(gdate))
