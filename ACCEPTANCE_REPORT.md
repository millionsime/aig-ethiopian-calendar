# Acceptance Report — aig_ethiopian_calendar (updated 2026-09-30, Phase 2)

Per spec §29. Honest scope statement: **Phase 1 (conversion engine) and
Phase 2 (Ethiopian date picker + JS engine mirror) are complete, tested
(35/35) and browser-verified (2026-09-30); the Phase-3 preview (display
hints under every Date field) ships in the same client layer.** Phases 4
(filters), 5 (list/table rendering) and beyond are NOT yet implemented.
No claim of system-wide support is made.

## Phase 2 summary (this update)

- `public/js/ethiopian_calendar.js` restructured: PART 1 is a pure engine
  (no DOM/frappe at module scope) exported via UMD — `module.exports`
  under node, `window.AIGEthiopianCalendar` in the browser — so the mirror
  test exercises the exact committed bytes. PART 2 is the flag-gated UI
  (hints + picker), fail-safe, no monkey patching.
- Picker: a `ዓ.ም.` button on each editable Date field opens an EC month
  grid (13 months, correct Pagumen 5/6, weekday grid). Picking a day
  writes the Gregorian value through the field's own change event — the
  stored value stays Gregorian-canonical. Reopening syncs to the field's
  current value; Today button included; Escape/outside-click closes.
- Read-only fields (no input) get hints only — verified regression.
- Mirror tests now run the engine under node (host or the backend
  container's node via `docker exec -i`, file piped via stdin, bytes-safe):
  GC→EC and EC→GC vs Python, invalid-date rejection parity, month-grid
  weekday/length facts, and a sampled day-by-day sweep across the
  interesting years. **35/35 pass.**
- Browser-verified (inv.admin, Material Request): pick 15 Meskerem 2019 →
  doc value 2026-09-25; pick 6 Pagumen 2019 (Nikul) → 2027-09-11; hints
  update live; native Frappe datepicker untouched.

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
Phase-3 preview adds the documented `app_include_js` / `app_include_css`
and `boot_session` hooks: the JS/CSS load unconditionally but the client
layer self-disables with a single early return unless the site-config flag
`aig_ethiopian_calendar` is truthy (published to the client via
`bootinfo` in `boot.py`). Asset URLs carry `?v=N` cache-busters.

## 3–4. Core files modified
**ZERO.** No file under `apps/frappe/` or `apps/erpnext/` is touched,
patched, or monkey-patched. The repo contains only this application.

## 5. Date fields supported
Phase-3 preview: every rendered Date field (`data-fieldtype='Date'`) in
form view shows a read-only Ethiopian hint beneath the value, in BOTH
render modes (editable `<input>` and static `.control-value`); values are
parsed through `frappe.datetime.user_to_str` so user date formats
(dd-mm-yyyy etc.) work. The input itself stays Gregorian — the layer
NEVER touches field values. Print formats can already use
`{{ ethiopian_date(doc.posting_date) }}` (read-only).
Browser-verified 2026-09-30: new Material Request form shows
"20 Meskerem 2019 EC" under 30-09-2026; saved doc MAT-MR-2026-00027
shows "19 Meskerem 2019 EC" under both transaction_date and schedule_date.

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
- Picker is click-driven; typing a raw EC string ("23/01/2019 EC") into a
  date field is not accepted yet (Phase 4 filter/parser integration).
- No list/report filter or table rendering integration (Phases 4–5); the
  list view itself shows no hints yet.
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
**35 passed, 0 failed** (`python3 run_tests.py`, 2026-09-30). The four
`test_js_mirror_*` tests execute the actual JS engine file under node
(host, or the frappe_docker backend container's node via `docker exec -i`
with the file piped through stdin) and assert parity with the Python
engine in both directions, invalid-input rejection, month-grid facts,
and a sampled day-by-day sweep. They skip with a note when no node is
available.
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
   the UI layer stops rendering hints on next reload (single early return
   in the JS; fail-safe by design, spec §16).
2. `bench --site <site> uninstall-app aig_ethiopian_calendar` — full removal;
   the app owns no columns, no docs, no cron, no core patches. ERPNext
   continues normally on Gregorian.
