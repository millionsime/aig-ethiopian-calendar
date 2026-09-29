# UI-facing cases (spec §20/§10 lite for Phase 1): the API boundary functions
# behave the way the Phase-3/4 integrations will use them.
import datetime

from ._mini import raises
from ..api.conversion import (
    ethiopian_string_to_gregorian_iso, ethiopian_to_gregorian_iso,
    gregorian_to_ethiopian,
)
from ..calendar import EthiopianDateError
from ..utils.helpers import as_gregorian_date, today_addis_ababa


def test_roundtrip_via_iso_fields():
    # what a form-field round-trip looks like: string in, string out
    iso = ethiopian_string_to_gregorian_iso("01/01/2019")
    assert iso == "2026-09-11"
    y, m, d = gregorian_to_ethiopian(iso)  # accepts ISO strings
    assert (y, m, d) == (2019, 1, 1)
    assert ethiopian_to_gregorian_iso(y, m, d) == iso  # lossless


def test_filter_range_conversion():
    # report filter: From/To Ethiopian dates -> Gregorian query bounds
    frm = ethiopian_string_to_gregorian_iso("01/01/2019 EC")
    to = ethiopian_string_to_gregorian_iso("30/01/2019 EC")
    assert frm == "2026-09-11"
    assert to == "2026-10-10"
    assert frm < to


def test_malformed_filter_input_rejected():
    with raises(EthiopianDateError):
        ethiopian_string_to_gregorian_iso("99/99/9999")
    with raises(EthiopianDateError):
        ethiopian_string_to_gregorian_iso("")


def test_helpers_coerce_frappe_shapes():
    assert as_gregorian_date("2026-09-30") == datetime.date(2026, 9, 30)
    assert as_gregorian_date("2026-09-30 14:00:00") == datetime.date(2026, 9, 30)
    assert as_gregorian_date("2026-09-30T14:00:00") == datetime.date(2026, 9, 30)
    dt = datetime.datetime(2026, 9, 30, 23, 30)
    assert as_gregorian_date(dt) == datetime.date(2026, 9, 30)
    assert as_gregorian_date(None) is None
    assert as_gregorian_date("") is None


def test_today_addis_is_date_not_timestamp():
    t = today_addis_ababa()
    assert isinstance(t, datetime.date) and not isinstance(t, datetime.datetime)
    assert abs((t - datetime.datetime.now(datetime.timezone.utc).date()).days) <= 1
