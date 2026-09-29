# Centralized display formatting (spec §9). All Ethiopian date rendering
# goes through these functions - never scattered conversion logic.
from ..calendar.constants import ETHIOPIC_MONTH_NAMES
from ..calendar.ethiopian import gregorian_to_ethiopian
from ..utils.helpers import as_gregorian_date

FORMATS = ("DD/MM/YYYY", "D MONTH YYYY", "MONTH D, YYYY")


def format_ethiopian_date(value, fmt="DD/MM/YYYY", include_ec=True):
    """Gregorian date (date/ISO string) -> Ethiopian display string.

    fmt: "DD/MM/YYYY" -> 23/01/2019 EC
         "D MONTH YYYY" -> 23 Meskerem 2019 EC
         "MONTH D, YYYY" -> Meskerem 23, 2019 EC
    """
    gdate = as_gregorian_date(value)
    if gdate is None:
        return ""
    y, m, d = gregorian_to_ethiopian(gdate)
    if fmt == "DD/MM/YYYY":
        out = f"{d:02d}/{m:02d}/{y}"
    elif fmt == "D MONTH YYYY":
        out = f"{d} {ETHIOPIC_MONTH_NAMES[m - 1]} {y}"
    elif fmt == "MONTH D, YYYY":
        out = f"{ETHIOPIC_MONTH_NAMES[m - 1]} {d}, {y}"
    else:
        raise ValueError(f"Unknown Ethiopian display format: {fmt!r}")
    if include_ec:
        out += " EC"
    return out


def jinja_ethiopian_date(value, fmt="DD/MM/YYYY"):
    """Jinja filter for print formats: {{ ethiopian_date(doc.posting_date) }}.

    Read-only presentation of an already-stored Gregorian value; never
    modifies the document.
    """
    return format_ethiopian_date(value, fmt=fmt)


__all__ = ["FORMATS", "format_ethiopian_date", "jinja_ethiopian_date"]
