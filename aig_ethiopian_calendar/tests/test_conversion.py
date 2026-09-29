# Phase-1 acceptance tests for the conversion engine (no pytest needed;
# also pytest-collectable). Run: python3 run_tests.py  (repo root)
import datetime

from ._mini import raises
from ..api.conversion import (
    ethiopian_to_gregorian,
    ethiopian_to_gregorian_iso,
    gregorian_to_ethiopian,
)
from ..api.formatting import format_ethiopian_date
from ..calendar import (
    EthiopianDateError,
    ethiopic_to_gregorian,
    is_ethiopic_leap,
    is_gregorian_leap,
    pagumen_days,
)


# -------------------------------------------------- verified ground truth
def test_anchor_millennium():
    # Ethiopian millennium: 1 Meskerem 2000 EC == 12 Sept 2007 GC
    assert ethiopic_to_gregorian(2000, 1, 1) == datetime.date(2007, 9, 12)
    assert gregorian_to_ethiopian(datetime.date(2007, 9, 12)) == (2000, 1, 1)


def test_anchor_enkutatash_2019():
    # Verified against multiple public sources (2026-09-29)
    assert ethiopic_to_gregorian(2019, 1, 1) == datetime.date(2026, 9, 11)
    assert gregorian_to_ethiopian(datetime.date(2026, 9, 11)) == (2019, 1, 1)


def test_anchor_year_after_leap_is_sept12():
    # New Year falls on Sept 12 iff the EC year is a multiple of 4
    # (the year AFTER a leap year): 2016 EC NY == 2023-09-12 (observed),
    # 2020 EC NY == 2027-09-12.
    assert ethiopic_to_gregorian(2016, 1, 1) == datetime.date(2023, 9, 12)
    assert ethiopic_to_gregorian(2020, 1, 1) == datetime.date(2027, 9, 12)


def test_spec_example_canonical_truth():
    # NOTE: the spec's §2 example (23/01/2019 EC -> 2026-09-30) is
    # arithmetically off: Meskerem 1-30 span Sept 11 -> Oct 10, so
    # 23 Meskerem 2019 == 2026-10-03. Canonical conversion is authoritative.
    assert ethiopian_to_gregorian_iso(2019, 1, 23) == "2026-10-03"
    assert gregorian_to_ethiopian(datetime.date(2026, 10, 3)) == (2019, 1, 23)
    # what 2026-09-30 really is: Meskerem spans Sept 11 - Oct 10
    assert gregorian_to_ethiopian(datetime.date(2026, 9, 30)) == (2019, 1, 20)


# -------------------------------------------------- New Year table 2015-2030
NEW_YEAR_TABLE = {
    # rule (verified): NY == Sept 12 iff EC year % 4 == 0
    2015: (2022, 9, 11), 2016: (2023, 9, 12), 2017: (2024, 9, 11),
    2018: (2025, 9, 11),
    2019: (2026, 9, 11),  # verified externally (Enkutatash 2026)
    2020: (2027, 9, 12), 2021: (2028, 9, 11), 2022: (2029, 9, 11),
    2023: (2030, 9, 11), 2024: (2031, 9, 12), 2025: (2032, 9, 11),
    2026: (2033, 9, 11), 2027: (2034, 9, 11), 2028: (2035, 9, 12),
    2029: (2036, 9, 11), 2030: (2037, 9, 11),
}


def test_new_year_table():
    for ec, g in NEW_YEAR_TABLE.items():
        assert ethiopic_to_gregorian(ec, 1, 1) == datetime.date(*g), ec
        assert gregorian_to_ethiopian(datetime.date(*g)) == (ec, 1, 1), ec


# -------------------------------------------------- leap rules
def test_ethiopic_leap_rule():
    # leap (Nikul, 6-day Pagumen) years are Y % 4 == 3
    for y, leap in [(2019, True), (2015, True), (2023, True), (2007, True),
                    (2018, False), (2020, False), (2022, False)]:
        assert is_ethiopic_leap(y) == leap, y


def test_pagumen_length():
    assert pagumen_days(2019) == 6   # 2019 EC is leap
    assert pagumen_days(2018) == 5
    # leap Pagumen 6 round-trips
    d = ethiopic_to_gregorian(2019, 13, 6)
    assert gregorian_to_ethiopian(d) == (2019, 13, 6)


def test_gregorian_leap_days_exist():
    assert is_gregorian_leap(2028) and not is_gregorian_leap(2100)
    assert gregorian_to_ethiopian(
        ethiopic_to_gregorian(2020, 13, 1)) == (2020, 13, 1)


# -------------------------------------------------- round-trip sweeps
def _roundtrip_year(ec_year):
    start = ethiopic_to_gregorian(ec_year, 1, 1)
    end = ethiopic_to_gregorian(ec_year, 13, pagumen_days(ec_year))
    d = start
    while d <= end:
        y, m, dd = gregorian_to_ethiopian(d)
        assert (y, m, dd) and ethiopic_to_gregorian(y, m, dd) == d, d
        d += datetime.timedelta(days=1)


def test_roundtrip_full_years():
    # every single day of common + leap + boundary years, losslessly
    for y in [2015, 2017, 2018, 2019, 2020, 2021, 2023]:
        _roundtrip_year(y)


def test_year_boundary_pagumen_to_meskerem():
    last = ethiopic_to_gregorian(2018, 13, 5)
    first = ethiopic_to_gregorian(2019, 1, 1)
    assert (first - last).days == 1


# -------------------------------------------------- invalid dates
def test_invalid_ethiopic_dates():
    for y, m, d in [(2018, 13, 6), (2019, 1, 31), (2019, 1, 32),
                    (2019, 14, 1), (2019, 0, 1), (2019, 1, 0),
                    (0, 1, 1), (-5, 1, 1)]:
        with raises(EthiopianDateError):
            ethiopic_to_gregorian(y, m, d)


# -------------------------------------------------- formatter
def test_formatter_formats():
    v = "2026-10-03"  # 23 Meskerem 2019 EC (Meskerem spans Sep 11 - Oct 10)
    assert format_ethiopian_date(v) == "23/01/2019 EC"
    assert format_ethiopian_date(v, "D MONTH YYYY") == "23 Meskerem 2019 EC"
    assert format_ethiopian_date(v, "MONTH D, YYYY") == "Meskerem 23, 2019 EC"
    assert format_ethiopian_date(None) == ""
    assert format_ethiopian_date("") == ""
    assert format_ethiopian_date(v, include_ec=False) == "23/01/2019"
