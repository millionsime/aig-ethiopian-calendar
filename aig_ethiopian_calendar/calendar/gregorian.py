# Gregorian-side primitives for the Ethiopian calendar layer.
# Phase 1: dependency-free (datetime only). No frappe imports anywhere in
# this package so the engine stays unit-testable and portable.

import calendar as _calendar
import datetime


def is_gregorian_leap(year):
    """Gregorian leap-year rule (divisible by 4, not by 100, unless by 400)."""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def days_in_gregorian_month(year, month):
    """Number of days in a Gregorian month (1-12)."""
    return _calendar.monthrange(year, month)[1]


def make_gregorian_date(year, month, day):
    """Construct a datetime.date, raising a descriptive error on bad input."""
    return datetime.date(year, month, day)
