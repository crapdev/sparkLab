#!/usr/bin/env python3
"""Execute the code cells of a notebook in order, in a single namespace.

Used by check-labs.py. The lab notebooks are plain Python (no IPython magics),
so running their cells with exec() behaves like "Run all" in Colab.

Prints one JSON line on the last line of stdout:
    {"ok": true}
    {"ok": false, "cell": 12, "tags": ["test"], "error": "AssertionError", "message": "..."}
"""

import json
import sys
import traceback

RESULT_PREFIX = "@@RESULT@@"


def main():
    notebook_path = sys.argv[1]
    with open(notebook_path, encoding="utf-8") as handle:
        notebook = json.load(handle)

    namespace = {"__name__": "__main__"}
    result = {"ok": True}

    for index, cell in enumerate(notebook["cells"], start=1):
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        try:
            exec(compile(source, f"<cell {index}>", "exec"), namespace)
        except BaseException as error:  # noqa: BLE001 - report any failure, including SystemExit
            traceback.print_exc()
            result = {
                "ok": False,
                "cell": index,
                "tags": cell.get("metadata", {}).get("tags", []),
                "error": type(error).__name__,
                "message": str(error)[:500],
            }
            break

    spark = namespace.get("spark")
    if spark is not None and hasattr(spark, "stop"):
        try:
            spark.stop()
        except Exception:  # noqa: BLE001 - nothing useful to do if shutdown fails
            pass

    print(RESULT_PREFIX + json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
