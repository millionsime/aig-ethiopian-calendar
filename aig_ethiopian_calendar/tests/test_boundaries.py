# Boundary battery from spec §19 + Gregorian-leap interactions.
import datetime

from ..calendar import (
    ethiopic_to_gregorian, gregorian_to_ethiopian, pagumen_days,
)


def _next_day(d):
    return d + datetime.timedelta(days=1)


BOUNDARY_YEARS = [2018, 2019, 2020, 2021, 2023, 2027]


def test_first_day_follows_prev_year():
    for year in BOUNDARY_YEARS:
        last_prev = ethiopic_to_gregorian(year - 1, 13,
                                          pagumen_days(year - 1))
        assert (ethiopic_to_gregorian(year, 1, 1) - last_prev).days == 1, year


def test_spec_boundary_dates():
    for year in BOUNDARY_YEARS:
        # 30/12/YYYY followed by 1/13/YYYY
        assert ethiopic_to_gregorian(year, 12, 30) < \
            ethiopic_to_gregorian(year, 13, 1)
        # 5/13/YYYY always exists
        assert gregorian_to_ethiopian(
            ethiopic_to_gregorian(year, 13, 5)) == (year, 13, 5)
        # 6/13 exists iff leap
        if pagumen_days(year) == 6:
            assert gregorian_to_ethiopian(
                ethiopic_to_gregorian(year, 13, 6)) == (year, 13, 6)
        # 1/1/YYYY+1 adjacency
        assert (ethiopic_to_gregorian(year + 1, 1, 1)
                - ethiopic_to_gregorian(year, 13,
                                        pagumen_days(year))).days == 1


def test_gregorian_feb_around_leap():
    for g in [datetime.date(2028, 2, 28), datetime.date(2028, 2, 29),
              datetime.date(2028, 3, 1)]:
        y, m, d = gregorian_to_ethiopian(g)
        assert ethiopic_to_gregorian(y, m, d) == g
    # 2028 GC leap day falls in Ethiopian 2020 EC
    assert gregorian_to_ethiopian(datetime.date(2028, 2, 29))[0] == 2020


def test_midnight_sweep_around_enkutatash_2026():
    # the week around Enkutatash 2019 EC must stay 1:1
    for offset in range(-3, 4):
        g = datetime.date(2026, 9, 11) + datetime.timedelta(days=offset)
        y, m, d = gregorian_to_ethiopian(g)
        assert ethiopic_to_gregorian(y, m, d) == g


def test_far_past_and_future():
    for g in [datetime.date(1900, 1, 1), datetime.date(2100, 12, 31)]:
        y, m, d = gregorian_to_ethiopian(g)
        assert ethiopic_to_gregorian(y, m, d) == g
