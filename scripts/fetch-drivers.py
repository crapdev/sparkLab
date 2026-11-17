#!/usr/bin/env python3
"""Build public/data/drivers.json from the Jolpica-F1 API (Ergast successor).

The output mimics the file used in the course: one JSON object per line
(JSON Lines) with a nested `name` struct. A small pretty-printed array is
also written to practice the `multiLine` reader option.

Usage:
    python3 scripts/fetch-drivers.py                 # fetch from the API
    python3 scripts/fetch-drivers.py --raw-dir DIR   # reuse downloaded pages
"""

import argparse
import glob
import json
import time
import urllib.request
from pathlib import Path

API_URL = "https://api.jolpi.ca/ergast/f1/drivers.json?limit={limit}&offset={offset}"
PAGE_SIZE = 100
OUT_DIR = Path(__file__).resolve().parent.parent / "public" / "data"
MULTILINE_SAMPLE_SIZE = 20


def fetch_pages():
    """Download every page of the drivers endpoint, politely."""
    drivers, offset, total = [], 0, None
    while total is None or offset < total:
        url = API_URL.format(limit=PAGE_SIZE, offset=offset)
        request = urllib.request.Request(url, headers={"User-Agent": "pyspark-labs-dataset-fetch"})
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)["MRData"]
        total = int(data["total"])
        drivers += data["DriverTable"]["Drivers"]
        offset += PAGE_SIZE
        time.sleep(0.6)  # stay well under the API burst limit
    return drivers


def load_pages(raw_dir):
    """Read pages previously saved as page_*.json."""
    drivers = []
    for path in sorted(glob.glob(str(Path(raw_dir) / "page_*.json"))):
        with open(path, encoding="utf-8") as handle:
            drivers += json.load(handle)["MRData"]["DriverTable"]["Drivers"]
    return drivers


def to_course_shape(index, driver):
    """Map an API record to the nested shape used in the course dataset."""
    number = driver.get("permanentNumber")
    return {
        "driverId": index,
        "driverRef": driver["driverId"],
        "number": int(number) if number is not None else None,
        "code": driver.get("code"),
        "name": {"forename": driver["givenName"], "surname": driver["familyName"]},
        "dob": driver.get("dateOfBirth"),
        "nationality": driver.get("nationality"),
        "url": driver.get("url"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw-dir", help="directory with already downloaded page_*.json files")
    args = parser.parse_args()

    raw = load_pages(args.raw_dir) if args.raw_dir else fetch_pages()
    raw.sort(key=lambda driver: driver["driverId"])
    records = [to_course_shape(index, driver) for index, driver in enumerate(raw, start=1)]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "drivers.json", "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    with open(OUT_DIR / "drivers_multiline.json", "w", encoding="utf-8") as handle:
        json.dump(records[:MULTILINE_SAMPLE_SIZE], handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"Wrote {len(records)} drivers to {OUT_DIR / 'drivers.json'}")
    print(f"Wrote {MULTILINE_SAMPLE_SIZE} drivers to {OUT_DIR / 'drivers_multiline.json'}")


if __name__ == "__main__":
    main()
