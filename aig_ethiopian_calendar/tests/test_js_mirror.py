# Cross-check the JS engine mirror against the Python engine (spec §4: the
# browser engine must agree with the server engine on every date).
#
# Node discovery order:
#   1. host `node`/`nodejs`
#   2. the frappe_docker backend container's node (bench images ship one)
#
# In both cases the LOCAL engine file is piped into node via stdin together
# with the probe snippet, so the test always exercises the exact bytes that
# are about to be committed, not a stale deployed copy. The engine's UMD
# wrapper detects the CommonJS context and populates module.exports, which
# the probe reads. I/O is bytes throughout (the file contains Ethiopic text;
# host locale must not matter). Skips with a note when no runtime exists.
import datetime
import shutil
import subprocess
from pathlib import Path

from ..calendar import ethiopic_to_gregorian, gregorian_to_ethiopian

REPO = Path(__file__).resolve().parents[2]
JS_FILE = REPO / "aig_ethiopian_calendar" / "public" / "js" / "ethiopian_calendar.js"

MONTH_NAMES = ["Meskerem", "Tikimt", "Hidar", "Tahsas", "Tir", "Yekatit",
               "Megabit", "Miazia", "Ginbot", "Sene", "Hamle", "Nehase",
               "Pagumen"]

# fixed cases spanning anchors, leaps and extremes
GC_CASES = [
    "2026-09-11",  # Enkutatash 2019 EC (anchor)
    "2026-09-12",
    "2026-10-03",  # 23 Meskerem 2019 EC (spec-corrected case)
    "2026-10-10",  # 30 Meskerem 2019 EC
    "2026-10-11",  # 1 Tikimt 2019 EC
    "2025-09-12",  # 1 Meskerem 2018 EC (previous year leap -> Sept 12)
    "2007-09-12",  # millennium: 1 Meskerem 2000 EC
    "2023-09-12",  # NY 2016 EC
    "2028-02-29",  # Gregorian leap day
    "1900-01-01",  # low extreme
    "2100-12-31",  # high extreme
    "2016-09-11",  # before the anchor year (negative day numbers)
]

EC_CASES = [
    (2019, 1, 1),    # anchor
    (2019, 1, 30),
    (2019, 1, 23),
    (2019, 2, 1),
    (2019, 13, 5),   # Pagumen common year
    (2023, 13, 6),   # Pagumen leap year (2023 % 4 == 3 -> Nikul)
    (2000, 1, 1),    # millennium
    (2016, 1, 1),
    (1899, 13, 5),   # far past, negative day numbers
    (2100, 6, 30),   # far future
]

INVALID_EC_CASES = [
    (2019, 1, 31),   # Meskerem has 30 days
    (2020, 13, 6),   # Pagumen 6 in a common year (2020 % 4 == 0, not Nikul)
    (2019, 13, 7),   # Pagumen 7 in a leap year (2019 IS Nikul; max 6)
    (2019, 14, 1),   # month 14
    (2019, 0, 1),    # month 0
    (2019, 1, 0),    # day 0
]


def _run_node(probe_js: str):
    """Pipe engine + probe into node (host or backend container).
    Returns CompletedProcess with bytes, or None when no node is available.
    Raises AssertionError on non-zero exit."""
    engine = JS_FILE.read_bytes()
    stdin = engine + b"\n;(function(){\n" + probe_js.encode("utf-8") + b"\n})();\n"

    def run(cmd):
        return subprocess.run(cmd, input=stdin, capture_output=True)

    host = shutil.which("node") or shutil.which("nodejs")
    if host:
        out = run([host])
    else:
        docker = shutil.which("docker")
        probe = (subprocess.run(["docker", "exec", "frappe_docker-backend-1",
                                 "node", "--version"], capture_output=True)
                 if docker else None)
        if not probe or probe.returncode != 0:
            return None
        out = run(["docker", "exec", "-i", "frappe_docker-backend-1", "node"])
    if out.returncode != 0:
        raise AssertionError("node run failed: "
                             + out.stderr.decode("utf-8", "replace")[:500])
    line = out.stdout.decode("utf-8", "replace").strip().splitlines()[-1]
    import json
    return json.loads(line)


def _cases_literal(cases):
    """JSON literal (repr would use single quotes / Python bools)."""
    import json
    return json.dumps(cases)


def test_js_mirror_gregorian_to_ethiopian_matches_python():
    result = _run_node(
        "const A = module.exports;"
        "const cases = " + _cases_literal(GC_CASES) + ";"
        "console.log(JSON.stringify(cases.map(c => A.gregorianToEthiopian(c))));"
    )
    if result is None:
        print("node not available (host or backend container) - JS mirror "
              "cross-check skipped; UI self-verifies against the same anchors")
        return
    assert result and len(result) == len(GC_CASES), result
    for iso, got in zip(GC_CASES, result):
        y, m, d = (int(x) for x in iso.split("-"))
        py = gregorian_to_ethiopian(datetime.date(y, m, d))
        assert (got["year"], got["month"], got["day"]) == py, (iso, got, py)
        assert got["text"] == f"{py[2]} {MONTH_NAMES[py[1]-1]} {py[0]} EC", (iso, got)


def test_js_mirror_ethiopian_to_gregorian_matches_python():
    result = _run_node(
        "const A = module.exports;"
        "const cases = " + _cases_literal([list(c) for c in EC_CASES]) + ";"
        "console.log(JSON.stringify(cases.map(c =>"
        "  A.ethiopianToGregorianISO(c[0], c[1], c[2]))));"
    )
    if result is None:
        print("node not available - EC->GC mirror cross-check skipped")
        return
    assert result and len(result) == len(EC_CASES), result
    for case, iso in zip(EC_CASES, result):
        py = ethiopic_to_gregorian(*case)
        assert iso == py.isoformat(), (case, iso, py)


def test_js_mirror_rejects_invalid_ethiopian_dates():
    result = _run_node(
        "const A = module.exports;"
        "const cases = " + _cases_literal([list(c) for c in INVALID_EC_CASES]) + ";"
        "console.log(JSON.stringify(cases.map(c =>"
        "  A.ethiopianToGregorianISO(c[0], c[1], c[2]))));"
    )
    if result is None:
        print("node not available - invalid-date mirror check skipped")
        return
    assert result is not None and all(r is None for r in result), result


def test_js_mirror_roundtrip_every_7th_day():
    """Day-by-day sweep across the interesting years, sampled every 7th day."""
    years = sorted({int(c[:4]) for c in GC_CASES} | {2007, 2016, 2022, 2023})
    py_days = {}
    d = datetime.date(min(years), 1, 1)
    end = datetime.date(max(years), 12, 31)
    while d <= end:
        py_days[d.isoformat()] = gregorian_to_ethiopian(d)
        d += datetime.timedelta(days=1)
    sample = sorted(py_days)[::7]  # every 7th day keeps the battery fast
    result = _run_node(
        "const A = module.exports;"
        "const cases = " + _cases_literal(sample) + ";"
        "console.log(JSON.stringify(cases.map(c => {"
        "  const r = A.gregorianToEthiopian(c);"
        "  return [r.year, r.month, r.day];"
        "})));"
    )
    if result is None:
        print("node not available - roundtrip sweep skipped")
        return
    assert len(result) == len(sample)
    for iso, got in zip(sample, result):
        assert tuple(got) == py_days[iso], (iso, got, py_days[iso])


def test_js_mirror_month_grid_shape():
    """monthGrid (picker helper): 1 Meskerem grid facts vs Python engine."""
    probes = [(2019, 1), (2022, 13), (2018, 1), (2021, 13)]
    result = _run_node(
        "const A = module.exports;"
        "const cases = " + _cases_literal([list(p) for p in probes]) + ";"
        "console.log(JSON.stringify(cases.map(p =>"
        "  A.monthGrid(p[0], p[1]))));"
    )
    if result is None:
        print("node not available - month grid check skipped")
        return
    assert len(result) == len(probes)
    for (y, m), got in zip(probes, result):
        gc = ethiopic_to_gregorian(y, m, 1)
        days = 6 if (y % 4 == 3 and m == 13) else (5 if m == 13 else 30)
        assert got["days"] == days, (y, m, got)
        assert got["monthName"] == MONTH_NAMES[m - 1]
        # cross-check the weekday against Python's calendar math
        # (engine uses getDay convention 0=Sunday; Python weekday(): 0=Monday)
        assert got["firstWeekday"] == (gc.weekday() + 1) % 7, (y, m, got, gc)
