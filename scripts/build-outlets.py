#!/usr/bin/env python3
"""Build public/data/outlets.csv, the store table used to practice joins.

One row per store, keyed by `Outlet_Identifier`. Four columns are copied from
`bigmart_sales.csv`, where they are constant for each store:
`Outlet_Establishment_Year`, `Outlet_Size`, `Outlet_Location_Type` and
`Outlet_Type`. Three columns are made up for the course and do not exist in
the sales file: `City`, `Manager` and `Staff`.

The table is deliberately NOT a perfect match for the sales file, so that every
join type returns something different:

- OUT019 sells in BigMart (528 rows) but is MISSING here.
- OUT099 is listed here but has NO sales.

Usage:
    python3 scripts/build-outlets.py
"""

import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "public" / "data"
SALES_PATH = DATA_DIR / "bigmart_sales.csv"
OUT_PATH = DATA_DIR / "outlets.csv"

KEY = "Outlet_Identifier"
REAL_COLUMNS = ["Outlet_Establishment_Year", "Outlet_Size", "Outlet_Location_Type", "Outlet_Type"]
FICTIONAL_COLUMNS = ["City", "Manager", "Staff"]

# A store that sells in BigMart but is left out of the table on purpose.
DROPPED_OUTLET = "OUT019"

# Fictional attributes, one per store. Cities follow the Tier of each store.
FICTIONAL = {
    "OUT010": ("Nagpur", "Priya Nair", 12),
    "OUT013": ("Indore", "Rahul Mehta", 48),
    "OUT017": ("Jaipur", "Anjali Rao", 35),
    "OUT018": ("Nashik", "Vikram Singh", 40),
    "OUT027": ("Bhopal", "Neha Kapoor", 60),
    "OUT035": ("Pune", "Arjun Desai", 30),
    "OUT045": ("Lucknow", "Kavita Joshi", 33),
    "OUT046": ("Mumbai", "Sanjay Iyer", 28),
    "OUT049": ("Delhi", "Meera Pillai", 42),
}

# A store with no sales at all. Every column is made up.
EXTRA_OUTLET = {
    KEY: "OUT099",
    "Outlet_Establishment_Year": "2012",
    "Outlet_Size": "Small",
    "Outlet_Location_Type": "Tier 2",
    "Outlet_Type": "Supermarket Type1",
    "City": "Chandigarh",
    "Manager": "Rohan Bhatt",
    "Staff": 25,
}


def read_real_outlets():
    """Collect the per-store columns from the sales file, checking they are constant."""
    outlets = {}
    with open(SALES_PATH, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            values = {column: row[column] for column in REAL_COLUMNS}
            known = outlets.setdefault(row[KEY], values)
            if known != values:
                raise ValueError(f"{row[KEY]} has more than one value for a store column")
    return outlets


def build_rows(real_outlets):
    rows = []
    for outlet_id in sorted(real_outlets):
        if outlet_id == DROPPED_OUTLET:
            continue
        city, manager, staff = FICTIONAL[outlet_id]
        rows.append({KEY: outlet_id, **real_outlets[outlet_id], "City": city, "Manager": manager, "Staff": staff})
    rows.append(EXTRA_OUTLET)
    return rows


def main():
    rows = build_rows(read_real_outlets())
    with open(OUT_PATH, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[KEY, *REAL_COLUMNS, *FICTIONAL_COLUMNS], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} outlets to {OUT_PATH} (without {DROPPED_OUTLET}, with {EXTRA_OUTLET[KEY]})")


if __name__ == "__main__":
    main()
