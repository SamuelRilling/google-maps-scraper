"""
format_results.py  —  Flatten scraped results.csv into a clean, spreadsheet-ready CSV.

Usage:
    python format_results.py                         # reads results.csv, writes results_formatted.csv
    python format_results.py input.csv output.csv    # custom paths
"""

import csv
import json
import sys
from pathlib import Path

INPUT  = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results.csv")
OUTPUT = Path(sys.argv[2]) if len(sys.argv) > 2 else INPUT.with_stem(INPUT.stem + "_formatted")

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def parse_json(val: str):
    if not val or val in ("{}", "[]", "null"):
        return None
    try:
        return json.loads(val)
    except json.JSONDecodeError:
        return None


def format_hours(raw: str) -> str:
    """Condense open_hours JSON → 'Mon 9am-6pm | Tue 9am-6pm | Sat Closed'"""
    data = parse_json(raw)
    if not data:
        return ""
    parts = []
    for day in DAY_ORDER:
        slots = data.get(day)
        if slots is None:
            continue
        abbr = day[:3]
        text = ", ".join(slots) if slots else "Closed"
        parts.append(f"{abbr}: {text}")
    return " | ".join(parts)


def extract_address(raw: str) -> dict:
    data = parse_json(raw) or {}
    return {
        "street":      data.get("street", ""),
        "city":        data.get("city", ""),
        "postal_code": data.get("postal_code", ""),
        "state":       data.get("state", ""),
        "country":     data.get("country", ""),
    }


def extract_emails(raw: str) -> str:
    data = parse_json(raw)
    if not data:
        return ""
    if isinstance(data, list):
        return "; ".join(data)
    return str(data)


OUT_FIELDS = [
    "name", "category",
    "street", "city", "postal_code", "state", "country",
    "phone", "website", "email",
    "rating", "review_count",
    "hours",
    "latitude", "longitude",
    "maps_link",
]


def transform(row: dict) -> dict:
    addr = extract_address(row.get("complete_address", ""))
    return {
        "name":         row.get("title", ""),
        "category":     row.get("category", ""),
        "street":       addr["street"] or row.get("address", ""),
        "city":         addr["city"],
        "postal_code":  addr["postal_code"],
        "state":        addr["state"],
        "country":      addr["country"],
        "phone":        row.get("phone", ""),
        "website":      row.get("website", ""),
        "email":        extract_emails(row.get("emails", "")),
        "rating":       row.get("review_rating", ""),
        "review_count": row.get("review_count", ""),
        "hours":        format_hours(row.get("open_hours", "")),
        "latitude":     row.get("latitude", ""),
        "longitude":    row.get("longitude", ""),
        "maps_link":    row.get("link", ""),
    }


def main():
    rows_in, rows_out = 0, 0
    with INPUT.open(encoding="utf-8", newline="") as f_in, \
         OUTPUT.open("w", encoding="utf-8", newline="") as f_out:

        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=OUT_FIELDS)
        writer.writeheader()

        seen = set()
        for row in reader:
            rows_in += 1
            out = transform(row)
            key = (out["name"].lower(), out["phone"], out["street"].lower())
            if key in seen:
                continue  # skip duplicates
            seen.add(key)
            writer.writerow(out)
            rows_out += 1

    print(f"Read {rows_in} rows, wrote {rows_out} unique businesses to {OUTPUT}")


if __name__ == "__main__":
    main()
