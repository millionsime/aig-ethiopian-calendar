# Shared helpers. Timezone rule (spec §10): date-only values are DATES,
# never timestamps. "Today" for the Ethiopian UI is computed in Addis Ababa
# local time (UTC+3, no DST) from the server clock - not from browser or UTC
# midnight arithmetic in client code.
import datetime


ADDIS_ABABA_OFFSET = datetime.timedelta(hours=3)


def today_addis_ababa():
    """Today's date as seen in Ethiopia (UTC+3, no DST)."""
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    return (now_utc + ADDIS_ABABA_OFFSET).date()


def as_gregorian_date(value):
    """Coerce frappe/erpnext date representations to datetime.date safely.

    Accepts datetime.date, datetime.datetime, "YYYY-MM-DD" strings and
    ISO datetimes; returns None for empty values. Never guesses formats
    beyond the canonical ISO ones ERPNext itself emits.
    """
    import datetime as _dt
    if value in (None, ""):
        return None
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    s = str(value).strip()
    if not s:
        return None
    return _dt.date.fromisoformat(s.split(" ")[0].split("T")[0])
