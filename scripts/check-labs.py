#!/usr/bin/env python3
"""Verify every lab by running its notebooks with real PySpark.

For each labs/<name>/ it checks that:
  1. lab.ipynb and solution.ipynb are up to date with source.py.
  2. solution.ipynb runs from top to bottom without errors (tests pass).
  3. lab.ipynb, unsolved, FAILS on a test cell with an AssertionError.
     This proves the tests actually test something.

Datasets are read from public/data, so no network and no deployed site are needed.

Usage:
    python scripts/check-labs.py              # all labs
    python scripts/check-labs.py 01 03        # only labs whose folder starts with 01 or 03
    python scripts/check-labs.py --verbose    # show notebook output on failure
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LABS_DIR = ROOT / "labs"
SCRIPTS_DIR = ROOT / "scripts"
RESULT_PREFIX = "@@RESULT@@"
TIMEOUT_SECONDS = 600


def run_notebook(notebook_path):
    """Run a notebook in a fresh process and an empty working directory."""
    env = dict(os.environ)
    env["PYSPARK_LABS_DATA_DIR"] = str(ROOT / "public" / "data")
    env["PYTHONIOENCODING"] = "utf-8"
    env.setdefault("PYSPARK_PYTHON", sys.executable)
    env.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

    with tempfile.TemporaryDirectory(prefix="pyspark-labs-") as workdir:
        started = time.monotonic()
        try:
            process = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "run_notebook.py"), str(notebook_path)],
                cwd=workdir,
                env=env,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Timeout", "message": f"more than {TIMEOUT_SECONDS}s"}, "", 0
        elapsed = time.monotonic() - started

    output = process.stdout + process.stderr
    for line in reversed(process.stdout.splitlines()):
        if line.startswith(RESULT_PREFIX):
            return json.loads(line[len(RESULT_PREFIX) :]), output, elapsed
    return {"ok": False, "error": "Crash", "message": "the runner produced no result"}, output, elapsed


def check_solution(lab_dir):
    result, output, elapsed = run_notebook(lab_dir / "solution.ipynb")
    if result["ok"]:
        return True, f"solution passes ({elapsed:.0f}s)", output
    return False, f"solution FAILS at cell {result.get('cell')}: {result['error']}: {result['message']}", output


def check_unsolved(lab_dir):
    result, output, elapsed = run_notebook(lab_dir / "lab.ipynb")
    if result["ok"]:
        return False, "unsolved lab PASSES: the tests do not test anything", output
    in_test = "test" in result.get("tags", [])
    if not in_test or result["error"] != "AssertionError":
        where = "a test cell" if in_test else "a non-test cell"
        return (
            False,
            f"unsolved lab fails in {where} (cell {result.get('cell')}) with {result['error']}: "
            f"{result['message']}. It must fail with an AssertionError raised by check().",
            output,
        )
    return True, f"unsolved lab fails as expected at cell {result['cell']} ({elapsed:.0f}s)", output


def main():
    parser = argparse.ArgumentParser(description="Run every lab notebook and verify its tests.")
    parser.add_argument("labs", nargs="*", help="folder prefixes to check (default: all)")
    parser.add_argument("--verbose", action="store_true", help="print notebook output on failure")
    args = parser.parse_args()

    stale = subprocess.run([sys.executable, str(SCRIPTS_DIR / "build-labs.py"), "--check"])
    if stale.returncode != 0:
        return 1

    lab_dirs = sorted(path.parent for path in LABS_DIR.glob("*/source.py"))
    if args.labs:
        lab_dirs = [path for path in lab_dirs if any(path.name.startswith(prefix) for prefix in args.labs)]
    if not lab_dirs:
        print("No labs to check.")
        return 1

    failures = 0
    for lab_dir in lab_dirs:
        print(f"\n{lab_dir.name}")
        for check in (check_solution, check_unsolved):
            ok, message, output = check(lab_dir)
            print(f"  {'OK  ' if ok else 'FAIL'} {message}")
            if not ok:
                failures += 1
                if args.verbose:
                    print("  ---- output ----")
                    print("\n".join(f"  {line}" for line in output.splitlines()[-60:]))

    print(f"\n{len(lab_dirs)} lab(s) checked, {failures} problem(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
