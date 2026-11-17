#!/usr/bin/env python3
"""Check that a lab's tests catch wrong solutions.

Each mutation replaces one snippet of the solution in labs/<lab>/source.py,
builds the solution notebook in memory, runs it with real PySpark and expects
a test cell to fail with an AssertionError. A mutation that passes means the
tests do not cover that mistake.

Mutations live in a JSON file next to the lab, labs/<lab>/mutations.json:

    [
      {"name": "forgot header", "old": ".option(\\"header\\", True)", "new": ""},
      ...
    ]

Usage:
    python scripts/mutate-lab.py 03-seleccionar-filtrar
    python scripts/mutate-lab.py 03-seleccionar-filtrar --verbose
"""

import argparse
import importlib.util
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


def load_builder():
    """Import build-labs.py (its name is not a valid module name)."""
    spec = importlib.util.spec_from_file_location("build_labs", SCRIPTS_DIR / "build-labs.py")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SCRIPTS_DIR))
    spec.loader.exec_module(module)
    return module


def run_notebook_text(notebook_text):
    env = dict(os.environ)
    env["PYSPARK_LABS_DATA_DIR"] = str(ROOT / "public" / "data")
    env["PYTHONIOENCODING"] = "utf-8"
    env.setdefault("PYSPARK_PYTHON", sys.executable)
    env.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

    with tempfile.TemporaryDirectory(prefix="pyspark-labs-mutate-") as workdir:
        notebook_path = Path(workdir) / "mutant.ipynb"
        notebook_path.write_text(notebook_text, encoding="utf-8")
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
            return {"ok": False, "error": "Timeout", "message": ""}, "", TIMEOUT_SECONDS
        elapsed = time.monotonic() - started

    output = process.stdout + process.stderr
    for line in reversed(process.stdout.splitlines()):
        if line.startswith(RESULT_PREFIX):
            return json.loads(line[len(RESULT_PREFIX) :]), output, elapsed
    return {"ok": False, "error": "Crash", "message": "no result"}, output, elapsed


def first_failed_test(output):
    """The name of the first ❌ test printed by check(), if any."""
    for line in output.splitlines():
        if line.startswith("❌ "):
            return line[2:].strip()
    return None


def main():
    parser = argparse.ArgumentParser(description="Run the mutations of one lab.")
    parser.add_argument("lab", help="lab folder name, e.g. 03-seleccionar-filtrar")
    parser.add_argument("--verbose", action="store_true", help="print notebook output on surprises")
    args = parser.parse_args()

    lab_dir = LABS_DIR / args.lab
    source_path = lab_dir / "source.py"
    mutations_path = lab_dir / "mutations.json"
    if not source_path.exists() or not mutations_path.exists():
        print(f"Need {source_path} and {mutations_path}", file=sys.stderr)
        return 1

    builder = load_builder()
    config = json.loads(builder.CONFIG_PATH.read_text(encoding="utf-8"))
    original = source_path.read_text(encoding="utf-8")
    mutations = json.loads(mutations_path.read_text(encoding="utf-8"))

    surprises = 0
    for mutation in mutations:
        if original.count(mutation["old"]) != 1:
            print(f"SKIP {mutation['name']}: snippet found {original.count(mutation['old'])} times")
            surprises += 1
            continue
        mutated = original.replace(mutation["old"], mutation["new"])
        meta, body = builder.parse_front_matter(mutated.splitlines(), source_path)
        cells = builder.build_cells(meta, body, config, lab_dir.name, "solution")
        notebook_text = json.dumps(builder.to_notebook(cells), ensure_ascii=False, indent=1)

        result, output, elapsed = run_notebook_text(notebook_text)
        failed_test = first_failed_test(output)
        caught = not result["ok"] and result["error"] == "AssertionError" and "test" in result.get("tags", [])
        expected = mutation.get("expect")
        if caught and (expected is None or expected in (failed_test or "")):
            print(f"OK   {mutation['name']} → {failed_test} ({elapsed:.0f}s)")
            continue
        surprises += 1
        if result["ok"]:
            print(f"MISS {mutation['name']}: every test passed ({elapsed:.0f}s)")
        elif caught:
            print(f"??   {mutation['name']}: caught by '{failed_test}', expected '{expected}' ({elapsed:.0f}s)")
        else:
            print(f"ERR  {mutation['name']}: {result['error']} in cell {result.get('cell')}: {result['message'][:120]}")
        if args.verbose:
            print("\n".join(f"     {line}" for line in output.splitlines()[-25:]))

    print(f"\n{len(mutations)} mutation(s), {surprises} surprise(s).")
    return 1 if surprises else 0


if __name__ == "__main__":
    sys.exit(main())
