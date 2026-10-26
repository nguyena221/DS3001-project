"""Collect IMDb data, count title types, and select a rated movie pilot.

Downloads basics/ratings once; caches compressed files locally for future runs.
Only a bounded candidate pool is kept in memory. No third-party packages needed.
"""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import heapq
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

from imdb_merge_helpers import ROOT, now


def download(name, folder):
    path = folder / f"{name}.tsv.gz"
    if path.exists():
        print(f"Using saved {path.name}", flush=True)
        return path
    url = f"https://datasets.imdbws.com/{path.name}"
    temporary = path.with_suffix(".part")
    print(f"Downloading {path.name}...", flush=True)
    with urlopen(Request(url, headers={"User-Agent": "DS3001-MovieProject/0.3"}), timeout=120) as response:
        metadata = {"url": url, "started_at_utc": now(),
                    "last_modified": response.headers.get("Last-Modified")}
        size, last = 0, time.monotonic()
        with temporary.open("wb") as handle:
            while chunk := response.read(1024 * 1024):
                handle.write(chunk)
                size += len(chunk)
                if time.monotonic() - last > 20:
                    print(f"  Downloaded {size / 1024**2:.0f} MiB", flush=True)
                    last = time.monotonic()
    metadata.update(completed_at_utc=now(), bytes=size)
    temporary.replace(path)
    path.with_suffix(".provenance.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return path


def scan(path):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)


def priority(imdb_id, seed):
    return int(hashlib.sha256(f"{seed}:{imdb_id}".encode()).hexdigest(), 16)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-year", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if not 1 <= args.per_year <= 100:
        parser.error("Choose 1–100 rated movies per year for this pilot")
    folder = ROOT / "data/raw/imdb_first"
    folder.mkdir(parents=True, exist_ok=True)
    basics_path = download("title.basics", folder)
    ratings_path = download("title.ratings", folder)
    # First collect all rated IDs (not rating values) to avoid favoring popular films.
    print("Reading rated IMDb IDs...", flush=True)
    rated = {r["tconst"] for r in scan(ratings_path)}
    counts, window_counts = Counter(), Counter()
    pools = {year: [] for year in range(2015, 2027)}
    print("Counting all title types and selecting rated movie/tvMovie candidates...", flush=True)
    last = time.monotonic()
    for count, row in enumerate(scan(basics_path), 1):
        kind, year = row["titleType"], row["startYear"]
        counts[kind] += 1
        if year.isdigit() and 2016 <= int(year) <= 2025:
            window_counts[kind] += 1
        if kind in ("movie", "tvMovie") and year.isdigit() and int(year) in pools and row["tconst"] in rated:
            pool = pools[int(year)]
            entry = (-priority(row["tconst"], args.seed), row["tconst"], row)
            if len(pool) < args.per_year:
                heapq.heappush(pool, entry)
            elif entry > pool[0]:
                heapq.heapreplace(pool, entry)
        if time.monotonic() - last > 20:
            print(f"  Counted {count:,} titles...", flush=True)
            last = time.monotonic()
    selected = [entry[2] for year in pools for entry in sorted(pools[year], reverse=True)]
    ids = {r["tconst"] for r in selected}
    rating_rows = {r["tconst"]: [r] for r in scan(ratings_path) if r["tconst"] in ids}
    for source, rows in (("title.basics", {r["tconst"]: [r] for r in selected}), ("title.ratings", rating_rows)):
        (folder / f"{source}.json").write_text(json.dumps({
            "requested_ids": sorted(ids), "source_url": f"https://datasets.imdbws.com/{source}.tsv.gz",
            "local_snapshot": str(folder / f"{source}.tsv.gz"), "extracted_at_utc": now(),
            "rows": rows}, indent=2), encoding="utf-8")
    summary = {"created_at_utc": now(), "seed": args.seed, "per_imdb_year": args.per_year,
               "all_title_type_counts": dict(sorted(counts.items())),
               "imdb_2016_2025_type_counts": dict(sorted(window_counts.items())),
               "selected": len(selected), "selected_by_imdb_year": {y: len(pools[y]) for y in pools},
               "note": "2015 and 2026 are boundary-audit candidates, not final scope. Canonical Wikidata year governs eligibility. Hash sample is reproducible for saved snapshots, not genre/country representative."}
    (folder / "selection_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (folder / "candidates.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(selected[0]))
        writer.writeheader()
        writer.writerows(selected)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
