# AIG Ethiopian Calendar (`aig_ethiopian_calendar`)

Ethiopian Calendar UI and date-conversion layer for **ERPNext/Frappe v16**.
Gregorian dates remain the canonical internal representation everywhere —
this app is a **presentation/input adapter only**. It never touches Frappe or
ERPNext core, the database, or any accounting logic.

**Status: Phase 1 complete and tested (conversion engine, 31/31); Phase-3
preview live — Ethiopian date hints render under every Date field in form
view (both editable and read-only modes), browser-verified on 2026-09-30.**
Phases 2 (EC input/picker), 4 (filters), 5 (list/table rendering) and the
roadmap below are still staged.

## Architecture

```
USER / UI
   ↓  Ethiopian date (typed or picked)
CALENDAR ADAPTER  (aig_ethiopian_calendar)
   ↓  Gregorian ISO
ERPNext / Frappe          ← UNTOUCHED
   ↓
Database                  ← Gregorian only

reverse:
Database → Gregorian → ADAPTER → Ethiopian display → UI
```

The adapter is the **only** place calendar math exists:

```
aig_ethiopian_calendar/
├── calendar/          conversion engine (constants, ethiopian, gregorian, validation)
├── utils/             parser (explicit formats only) + helpers (timezone-safe today)
├── api/               THE public boundary: conversion.py + formatting.py
├── boot.py            boot_session hook: publishes the feature flag to the client
├── public/js          browser engine mirror + hint layer (flag-gated, fail-safe)
├── public/css         hint styling
├── tests/             zero-dependency suite (also pytest-collectable)
└── hooks.py           jinja print filter, include_js/css (?v= cache-busted), version gate
```

## Installation

```bash
cd frappe-bench
bench get-app <this-repo-url> aig_ethiopian_calendar
bench --site <site> install-app aig_ethiopian_calendar
bench --site <site> migrate
# feature flag (OFF by default; the app loads no UI until enabled):
bench --site <site> set-config aig_ethiopian_calendar 1
```

## Conversion model

13 months: 12 × 30 days + Pagumen (5 days; 6 in leap years).
A year is leap (Nikul) iff `Y % 4 == 3`. New Year falls on Gregorian
**Sept 12 iff the EC year is a multiple of 4**, else Sept 11.
Internally both directions reduce to one absolute day-number (N = 0 at
1 Meskerem 2019 EC = 2026-09-11 GC), so they are exact inverses by
construction — verified against externally confirmed dates:
millennium (2000 EC = 2007-09-12), Enkutatash 2019 EC = 2026-09-11,
NY 2016 EC = 2023-09-12.

## API usage (the boundary)

```python
from aig_ethiopian_calendar.api import (
    ethiopian_to_gregorian,        # (Y, M, D) -> datetime.date
    ethiopian_to_gregorian_iso,    # (Y, M, D) -> "YYYY-MM-DD"
    gregorian_to_ethiopian,        # date/ISO   -> (Y, M, D)
    ethiopian_string_to_gregorian_iso,  # "23/01/2019 EC" -> ISO (filters!)
    format_ethiopian_date,         # date/ISO   -> display string
)

from aig_ethiopian_calendar.utils import parse_ethiopian_date
```

Print formats (Jinja, explicit opt-in per format):
`{{ ethiopian_date(doc.posting_date) }}`

## Hooks used (complete list)

`app_name/app_title/...` metadata · `required_min/max_frappe_version` ·
`jinja_methods.ethiopian_date` · `boot_session` (publishes the flag via
bootinfo) · `app_include_js` / `app_include_css` (assets self-disable
without the flag; bump the `?v=` cache-buster on every asset change) ·
`after_install` version check via `install.check_compatibility`.

**Deployment note (docker/frappe_docker):** bench links
`sites/assets/<app>` on the *backend* container only; the *frontend*
container serves `/assets/*`, so the app's `public/` tree must be present
at `/home/frappe/frappe-bench/assets/aig_ethiopian_calendar/` there too.
After changing `public/js|css`, copy to both containers and clear site
cache; the `?v=` in `hooks.py` busts browser caches.

## Supported versions

Frappe **16.x**, ERPNext **16.x** (install refuses other majors — see
`install.py`; spec §15).

## Testing

```bash
python3 run_tests.py          # zero dependencies
# or: pytest aig_ethiopian_calendar/tests
```

Covers: verified anchors, New Year table 2015–2030, leap rules (both
calendars), Pagumen 5/6, invalid dates (32 Meskerem, 6 Pagumen common
year, …), full-year day-by-day round-trips (common + leap + boundary
years), Gregorian Feb 28/29, Enkutatash-week sweep, 1900/2100 extremes,
parser format whitelist, filter-range conversion, helper coercion,
Addis-Ababa "today".

## Rollback

1. `bench --site <site> set-config aig_ethiopian_calendar 0` — UI gone on
   next reload (fail-safe by design, spec §16).
2. `bench --site <site> uninstall-app aig_ethiopian_calendar` — removes the
   app; ERPNext continues on Gregorian with zero data changes (the app owns
   no date columns and never wrote to ERPNext documents).

## Known limitations

- Display hints only — typing/picking dates in Ethiopian calendar is
  Phase 2 (not implemented).
- List view, report filters and table column rendering are untouched
  (Phases 4–5).
- Date range validated 1 Jan 1900 → 2100 in tests; engine is ordinal-based
  and exact far beyond, but treat untested centuries as untested.
- Timezone: date-only values are treated as dates; "today" is Addis Ababa
  (UTC+3, no DST). Datetime fields (with time component) are out of scope
  for Phase 1.

## Security & performance

- No client-trusted conversion server-side: `ethiopian_string_to_gregorian_iso`
  raises on anything unparseable/invalid; whitelisted endpoints (Phase 4+)
  will sanitize before touching Frappe APIs.
- Zero runtime dependencies; conversions are O(1) integer math (year-walk
  is bounded by leap density, not data); formatting is a pure function —
  safe to cache per request.
