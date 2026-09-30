# Cross-check the JS engine mirror against the Python engine (spec §4:
# both must agree). Skipped silently when node is unavailable.
import shutil
import subprocess
from pathlib import Path

from ..calendar import ethiopic_to_gregorian, gregorian_to_ethiopian

JS = r'''
const m = require('aig_ethiopian_calendar/public/js/ethiopian_calendar.js');
'''

def test_js_mirror_matches_python():
    node = shutil.which("node") or shutil.which("nodejs")
    if not node:
        print("node not available - JS mirror cross-check skipped (UI layer "
              "self-verifies at runtime against the same anchors)")
        return
    repo = Path(__file__).resolve().parents[2]
    script = (
        "global.window = {}; "
        f"require('{repo}/aig_ethiopian_calendar/public/js/"
        "ethiopian_calendar.js'); const A = global.window."
        "AIGEthiopianCalendar; const cases = ["
        "'2026-09-11','2026-09-12','2026-10-03','2025-09-12',"
        "'2007-09-12','2028-02-29','1900-01-01','2100-12-31']; "
        "console.log(JSON.stringify(cases.map(c => "
        "A.gregorianToEthiopian(c).text)));"
    )
    out = subprocess.run([node, "-e", script], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    js_texts = out.stdout.strip()
    # Python side for the same cases (format: "D Month Y EC")
    names = ["Meskerem", "Tikimt", "Hidar", "Tahsas", "Tir", "Yekatit",
             "Megabit", "Miazia", "Ginbot", "Sene", "Hamle", "Nehase",
             "Pagumen"]
    expect = []
    for iso in ["2026-09-11", "2026-09-12", "2026-10-03", "2025-09-12",
                "2007-09-12", "2028-02-29", "1900-01-01", "2100-12-31"]:
        y, m, d = gregorian_to_ethiopian(iso)
        expect.append(f"{d} {names[m-1]} {y} EC")
    for e in expect:
        assert e in js_texts, (e, js_texts)
