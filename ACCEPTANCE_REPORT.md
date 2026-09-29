# Acceptance Report — aig_ethiopian_calendar (2026-09-29)

Per spec §29. Honest scope statement: **Phase 1 (conversion engine) is
complete and tested; Phases 2–7 are NOT yet implemented.** No claim of
system-wide support is made.

## 1. Files created

```
run_tests.py                                  zero-dep test runner
pyproject.toml  requirements.txt  license.txt  .gitignore
README.md  ACCEPTANCE_REPORT.md
aig_ethiopian_calendar/
├── __init__.py  hooks.py  install.py  modules.txt  patches.txt
├── api/{__init__,conversion,formatting}.py     THE public boundary
├── calendar/{__init__,constants,ethiopian,gregorian,validation}.py
├── utils/{__init__,parser,helpers}.py
└── tests/{__init__,_mini,test_conversion,test_parser,test_boundaries,test_ui_cases}.py
```

## 2. ERPNext/Frappe hooks used
Metadata hooks; `required_min/max_frappe_version`; `jinja_methods`
(one read-only print formatter, explicitly opted-in per print format).
Phases 3–5 will add flag-gated `app_include_js/css` only.

## 3–4. Core files modified
**ZERO.** No file under `apps/frappe/` or `apps/erpnext/` is touched,
patched, or monkey-patched. The repo contains only this application.

## 5. Date fields supported
Phase 1: none wired into the UI (by design). Engine + parser + formatter
are ready for Phases 2–3. Print formats can already use
`{{ ethiopian_date(doc.posting_date) }}` after install (read-only).

## 6. Report filters supported
Not yet (Phase 4). The exact boundary function they will use —
`ethiopian_string_to_gregorian_iso("01/01/2019 EC") -> "2026-09-11"` —
is implemented and tested (`test_ui_cases::test_filter_range_conversion`).

## 7. List filters supported
Not yet (Phase 4). Same boundary function covers `= > < >= <= Between`
by converting operands before the query.

## 8. Table rendering supported
Not yet (Phase 5). `format_ethiopian_date` is the single formatter the
rendering layer will call.

## 9. Known unsupported areas (honest list)
- No Ethiopian date picker / form-field wiring (Phases 2–3).
- No list/report filter or table rendering integration (Phases 4–5).
- No dashboard/timeline/search integration (Phase 5).
- Datetime (time-component) fields out of scope so far.
- User preferences / admin settings UI (Phase 6) — flag is site-config today.

## 10. Upgrade risks
- Frappe v17+ blocked at install (`install.check_compatibility`) until
  re-validated (spec §15).
- Phase 3–5 UI adapters will be the upgrade-sensitive surface; design rule:
  public hooks + attribute-existence checks, isolated in one adapter module,
  fail-safe to standard UI on any error (spec §14/§16).

## 11. Test results
**30 passed, 0 failed** (`python3 run_tests.py`, 2026-09-29).
Coverage: verified external anchors (millennium 2000 EC = 2007-09-12;
Enkutatash 2019 EC = 2026-09-11; NY 2016 EC = 2023-09-12), New Year table
2015–2030, both leap rules, Pagumen 5/6 incl. round-trip, invalid dates
(32 Meskerem, 6 Pagumen common year, month 14, zero/negative components),
full-year day-by-day round-trips (7 years incl. leap/boundary), Gregorian
Feb 28/29 2028, Enkutatash-week sweep, 1900/2100 extremes, parser whitelist
and rejections, filter-range conversion, malformed rejection, frappe-shape
coercion, Addis-Ababa today (UTC+3, no DST).
Note: the spec's §2 sample value (23/01/2019 EC = 2026-09-30) is
arithmetically off; the correct mapping (23 Meskerem 2019 = 2026-10-03) is
asserted with an explanatory comment in `test_conversion.py`.

## 12. Rollback procedure
1. `bench --site <site> set-config aig_ethiopian_calendar 0` (or unset) —
   UI extensions stop loading (once Phases 3+ exist; today the app only
   adds the opt-in Jinja filter).
2. `bench --site <site> uninstall-app aig_ethiopian_calendar` — full removal;
   the app owns no columns, no docs, no cron, no core patches. ERPNext
   continues normally on Gregorian.
