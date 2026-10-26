"""Keep IMDb-matched movies; preserve excluded rows and reasons separately."""

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def exclusion_reason(row):
    if not row["imdb_title_type"]:
        return "No matching IMDb basics record"
    if row["imdb_title_type"] not in ("movie", "tvMovie"):
        return f"IMDb titleType is {row['imdb_title_type']}, outside movie/tvMovie scope"
    if not row["imdb_rating"]:
        return "No IMDb rating available for target"
    if row.get("planned_split") == "review":
        return "Release year unresolved; held for review, not model-ready"
    if row.get("planned_split") == "outside_scope":
        return "Canonical release year outside 2016–2025"
    return ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/processed/imdb_first_combined.csv")
    args = parser.parse_args()
    with args.input.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        rows = list(reader)
    kept, excluded = [], []
    for row in rows:
        reason = exclusion_reason(row)
        if reason:
            excluded.append({**row, "exclusion_reason": reason})
        else:
            kept.append(row)
    for label, records, columns in (
        ("eligible", kept, fields),
        ("excluded", excluded, fields + ["exclusion_reason"]),
    ):
        output = args.input.with_name(f"{args.input.stem}_{label}.csv")
        with output.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(records)
        print(f"{label}: {len(records)} movies -> {output}")


if __name__ == "__main__":
    main()
