#!/usr/bin/env python3
# Zero-dependency test runner for the Ethiopian calendar engine.
# Usage: python3 run_tests.py            (from the repo root)
# The same tests are also collectable by pytest if it is available.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aig_ethiopian_calendar.tests import (  # noqa: E402
    test_boundaries, test_conversion, test_js_mirror, test_parser,
    test_ui_cases,
)

MODULES = [test_conversion, test_parser, test_boundaries, test_ui_cases,
           test_js_mirror]


def main():
    passed = failed = 0
    failures = []
    for mod in MODULES:
        for name in sorted(dir(mod)):
            if not name.startswith("test_"):
                continue
            fn = getattr(mod, name)
            if not callable(fn):
                continue
            try:
                fn()
                passed += 1
                print(f"  PASS {mod.__name__.rsplit('.', 1)[-1]}::{name}")
            except Exception:
                failed += 1
                failures.append((mod.__name__, name, traceback.format_exc()))
                print(f"  FAIL {mod.__name__.rsplit('.', 1)[-1]}::{name}")
    for mod, name, tb in failures:
        print(f"\n--- FAILURE {mod}::{name} ---\n{tb}")
    print(f"\nRESULT: {passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
