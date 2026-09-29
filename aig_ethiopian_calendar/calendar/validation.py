# Validation layer - all user-entered Ethiopian dates pass through here.
from .constants import PAGUMEN_INDEX
from .ethiopian import (
    EthiopianDateError, days_in_ethiopic_month, is_ethiopic_leap,
)


def is_valid_ethiopic(year, month, day):
    """True iff (Y, M, D) is a real Ethiopian calendar date."""
    try:
        days_in_ethiopic_month(year, month)
    except EthiopianDateError:
        return False
    if not isinstance(year, int) or not isinstance(month, int) \
            or not isinstance(day, int):
        return False
    if month == PAGUMEN_INDEX and day == 6 and not is_ethiopic_leap(year):
        return False
    return 1 <= day <= days_in_ethiopic_month(year, month)


def validate_ethiopic(year, month, day):
    """Raise EthiopianDateError with a precise message if invalid."""
    if not is_valid_ethiopic(year, month, day):
        raise EthiopianDateError(
            f"Invalid Ethiopian date: {year}-{month}-{day}")
    return True
