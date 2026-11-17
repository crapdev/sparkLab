#!/usr/bin/env python3
"""Generate lab.ipynb and solution.ipynb from each labs/<name>/source.py.

A lab is written once, in "percent" format, with the solution marked:

    # ---
    # id: 01-fundamentos
    # title: Fundamentos de Spark
    # objective: ...
    # minutes: 30
    # ---

    # %% [markdown]
    # ## Tarea 1 · ...

    # %%
    ### BEGIN SOLUTION
    answer = 42
    ### END SOLUTION
    ### BEGIN STARTER
    answer = ...
    ### END STARTER

    # %% [test]
    check("Tarea 1", lambda: answer == 42, "Pista para el estudiante.")

Cell directives:
    # %%                  code cell
    # %% [markdown]       markdown cell (lines are `# ` comments)
    # %% [test]           code cell tagged as a test
    # %% [install]        shared install cells
    # %% [helpers]        shared `check` helper
    # %% [data] a.csv b   shared download cell for the listed datasets
    # %% [summary]        shared final summary

Usage:
    python scripts/build-labs.py            # write every notebook
    python scripts/build-labs.py --check    # fail if a notebook is out of date
"""

import argparse
import json
import re
import sys
from pathlib import Path

import lab_templates as templates

ROOT = Path(__file__).resolve().parent.parent
LABS_DIR = ROOT / "labs"
CONFIG_PATH = ROOT / "site.config.json"
VARIANTS = {"lab": "lab.ipynb", "solution": "solution.ipynb"}
REQUIRED_META = ("id", "title", "objective", "minutes")

CELL_MARKER = re.compile(r"^# %%\s*(?:\[(\w+)\])?\s*(.*)$")
CHECK_CALL = re.compile(r"^\s*check\(", re.MULTILINE)


class LabError(Exception):
    """A source.py file is malformed."""


def parse_front_matter(lines, path):
    """Read the `# key: value` block delimited by `# ---` at the top of the file."""
    if not lines or lines[0].strip() != "# ---":
        raise LabError(f"{path}: must start with a '# ---' front matter block")
    meta = {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "# ---":
            missing = [key for key in REQUIRED_META if key not in meta]
            if missing:
                raise LabError(f"{path}: front matter is missing {', '.join(missing)}")
            return meta, lines[index + 1 :]
        key, separator, value = line.removeprefix("#").partition(":")
        if not separator:
            raise LabError(f"{path}: invalid front matter line: {line!r}")
        meta[key.strip()] = value.strip()
    raise LabError(f"{path}: front matter is never closed")


def split_cells(lines):
    """Split the body into (kind, argument, lines) tuples."""
    cells = []
    for line in lines:
        marker = CELL_MARKER.match(line)
        if marker:
            cells.append((marker.group(1) or "code", marker.group(2).strip(), []))
        elif cells:
            cells[-1][2].append(line)
        elif line.strip():
            raise LabError(f"content before the first cell marker: {line!r}")
    return cells


def strip_blank_edges(lines):
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return lines


def render_code(lines, variant):
    """Keep the solution or the starter block, depending on the variant."""
    kept, block = [], None
    for line in lines:
        marker = line.strip()
        if marker in ("### BEGIN SOLUTION", "### BEGIN STARTER"):
            if block:
                raise LabError(f"nested block marker: {marker}")
            block = "solution" if "SOLUTION" in marker else "starter"
        elif marker in ("### END SOLUTION", "### END STARTER"):
            if not block:
                raise LabError(f"unexpected block marker: {marker}")
            block = None
        elif block is None or (block == "solution") == (variant == "solution"):
            kept.append(line)
    if block:
        raise LabError(f"unclosed {block} block")
    return "\n".join(strip_blank_edges(kept))


def render_markdown(lines):
    text = []
    for line in strip_blank_edges(lines):
        if line.startswith("# "):
            text.append(line[2:])
        elif line.strip() in ("#", ""):
            text.append("")
        else:
            raise LabError(f"markdown cells must be '# ' comments: {line!r}")
    return "\n".join(text)


def build_cells(meta, body, config, lab_dir, variant):
    """Expand a parsed source into a list of (cell_type, source, tags)."""
    parsed = split_cells(body)
    test_sources = [render_code(lines, variant) for kind, _, lines in parsed if kind == "test"]
    expected_tests = sum(len(CHECK_CALL.findall(source)) for source in test_sources)

    cells = [("markdown", templates.header_cell(meta, config, lab_dir, variant), [])]
    for kind, argument, lines in parsed:
        if kind == "markdown":
            cells.append(("markdown", render_markdown(lines), []))
        elif kind == "code":
            cells.append(("code", render_code(lines, variant), []))
        elif kind == "test":
            cells.append(("code", render_code(lines, variant), ["test"]))
        elif kind == "install":
            cells.append(("markdown", templates.INSTALL_MARKDOWN, []))
            cells.append(("code", templates.install_cell(config), ["setup"]))
        elif kind == "helpers":
            cells.append(("markdown", templates.HELPERS_MARKDOWN, []))
            cells.append(("code", templates.HELPERS_CELL, ["setup"]))
        elif kind == "data":
            datasets = argument.split()
            if not datasets:
                raise LabError("[data] needs at least one dataset name")
            cells.append(("markdown", templates.data_markdown(datasets), []))
            cells.append(("code", templates.data_cell(config, datasets), ["setup"]))
        elif kind == "summary":
            cells.append(("markdown", templates.SUMMARY_MARKDOWN, []))
            cells.append(("code", templates.summary_cell(expected_tests), ["test", "summary"]))
        else:
            raise LabError(f"unknown cell directive [{kind}]")
    return cells


def to_notebook(cells):
    """Build a deterministic nbformat 4.5 document."""
    notebook_cells = []
    for index, (cell_type, source, tags) in enumerate(cells, start=1):
        lines = source.split("\n")
        cell = {
            "cell_type": cell_type,
            "id": f"cell-{index:03d}",
            "metadata": {"tags": tags} if tags else {},
            "source": [f"{line}\n" for line in lines[:-1]] + [lines[-1]],
        }
        if cell_type == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
        notebook_cells.append(cell)
    return {
        "cells": notebook_cells,
        "metadata": {
            "colab": {"provenance": []},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def build_lab(source_path, config):
    """Return {file name: notebook JSON text} for one lab."""
    lab_dir = source_path.parent.name
    meta, body = parse_front_matter(source_path.read_text(encoding="utf-8").splitlines(), source_path)
    if meta["id"] != lab_dir:
        raise LabError(f"{source_path}: id '{meta['id']}' must match the folder name")
    outputs = {}
    for variant, file_name in VARIANTS.items():
        try:
            cells = build_cells(meta, body, config, lab_dir, variant)
        except LabError as error:
            raise LabError(f"{source_path}: {error}") from None
        outputs[file_name] = json.dumps(to_notebook(cells), ensure_ascii=False, indent=1) + "\n"
    return outputs


def main():
    parser = argparse.ArgumentParser(description="Generate lab notebooks from source.py files.")
    parser.add_argument("--check", action="store_true", help="fail if any notebook is out of date")
    args = parser.parse_args()

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    sources = sorted(LABS_DIR.glob("*/source.py"))
    if not sources:
        print("No labs found.")
        return 0

    stale = []
    for source_path in sources:
        try:
            outputs = build_lab(source_path, config)
        except LabError as error:
            print(f"ERROR {error}", file=sys.stderr)
            return 1
        for file_name, content in outputs.items():
            target = source_path.parent / file_name
            current = target.read_text(encoding="utf-8") if target.exists() else None
            if current == content:
                continue
            if args.check:
                stale.append(target.relative_to(ROOT))
            else:
                target.write_text(content, encoding="utf-8")
                print(f"wrote {target.relative_to(ROOT)}")

    if stale:
        print("Out of date (run `npm run labs:build`):", *stale, sep="\n  ", file=sys.stderr)
        return 1
    print(f"{len(sources)} lab(s) up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
