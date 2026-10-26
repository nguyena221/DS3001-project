"""Stream official IMDb files and enrich our Wikidata pilot (standard library only).

Only matching rows are stored locally. The principals file is large; its full
stream must be scanned to preserve all principal actors, including missing casts.
Completed source extracts are cached; interrupted sources restart their scan.
"""

import argparse
import csv
import gzip
import io
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from clean_release_dates import choose_release, split_for_year

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ("title.ratings", "title.basics", "title.crew", "title.principals")


def now():
    return datetime.now(timezone.utc).isoformat()


def extract(source, ids, cache):
    """Cache one complete source extract; never treat a partial scan as complete."""
    path = cache / f"{source}.json"
    if path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved["requested_ids"] == sorted(ids):
            print(f"Reusing completed {source} extract", flush=True)
            return saved
    url = f"https://datasets.imdbws.com/{source}.tsv.gz"
    print(f"Scanning {source} from IMDb (large compressed file)...", flush=True)
    started = now()
    found = {}
    last_update = time.monotonic()
    request = Request(url, headers={"User-Agent": "DS3001-MovieRatingProject/0.2"})
    with urlopen(request, timeout=120) as response:
        last_modified = response.headers.get("Last-Modified")
        with gzip.GzipFile(fileobj=response) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8") as text:
                # Check the first column before parsing: almost every row belongs
                # to an unrelated title, especially in the large principals file.
                headers = next(text).rstrip("\r\n").split("\t")
                for count, line in enumerate(text, 1):
                    imdb_id = line.partition("\t")[0]
                    if imdb_id in ids:
                        row = dict(zip(headers, line.rstrip("\r\n").split("\t")))
                        found.setdefault(imdb_id, []).append(row)
                    if time.monotonic() - last_update > 20:
                        print(f"  {source}: scanned {count:,} rows; matched {len(found)}/{len(ids)} IDs", flush=True)
                        last_update = time.monotonic()
                    # These three files have one row per movie. Principals does not.
                    if source != "title.principals" and len(found) == len(ids):
                        break
    saved = {"source_url": url, "started_at_utc": started,
             "completed_at_utc": now(), "source_last_modified": last_modified,
             "requested_ids": sorted(ids), "rows": found}
    temporary = path.with_suffix(".part")
    temporary.write_text(json.dumps(saved, indent=2), encoding="utf-8")
    temporary.replace(path)
    print(f"Finished {source}: {len(found)}/{len(ids)} IDs matched", flush=True)
    return saved


def known(value):
    return "" if value in (None, "\\N") else value


def items(value):
    return known(value).split(",") if known(value) else []


def merge_row(wiki, sources):
    ids = [s["value"] for s in json.loads(wiki["imdb_ids"])]
    if len(ids) != 1:
        raise ValueError(f"Review ambiguous IMDb IDs for {wiki['wikidata_id']}: {ids}")
    imdb_id = ids[0]
    row = {"wikidata_id": wiki["wikidata_id"], "imdb_id": imdb_id,
           "wikidata_title": wiki["title"]}
    for name in ("languages", "countries", "budgets", "release_dates"):
        row[f"wikidata_{name}"] = wiki[name]
    row.update(choose_release(json.loads(wiki["release_dates"])))
    row["planned_split"] = split_for_year(row["release_year"])
    notes = []
    records = {}
    for source in SOURCES:
        records[source] = sources[source]["rows"].get(imdb_id, [])
        if not records[source]:
            notes.append(f"missing {source}")
        if source != "title.principals" and len(records[source]) > 1:
            raise ValueError(f"Duplicate {source} rows for {imdb_id}")
    basics = (records["title.basics"] or [{}])[0]
    rating = (records["title.ratings"] or [{}])[0]
    crew = (records["title.crew"] or [{}])[0]
    row.update({"imdb_title": known(basics.get("primaryTitle")),
                "imdb_title_type": known(basics.get("titleType")),
                "imdb_start_year": known(basics.get("startYear")),
                "runtime_minutes": known(basics.get("runtimeMinutes")),
                "genres": json.dumps(items(basics.get("genres"))),
                "director_ids": json.dumps(items(crew.get("directors"))),
                "imdb_rating": known(rating.get("averageRating")),
                "imdb_vote_count": known(rating.get("numVotes"))})
    principals = records["title.principals"]
    # IMDb principals includes other jobs; only actor/actress entries are cast.
    cast = sorted((r for r in principals if r["category"] in ("actor", "actress")),
                  key=lambda r: int(r["ordering"]))
    row["principal_cast_ids"] = json.dumps(list(dict.fromkeys(r["nconst"] for r in cast)))
    if row["imdb_title_type"] and row["imdb_title_type"] != "movie":
        notes.append("IMDb titleType is not movie; review eligibility")
    if row["release_year"] != "" and row["imdb_start_year"]:
        if str(row["release_year"]) != row["imdb_start_year"]:
            notes.append("IMDb and canonical Wikidata release years differ")
    row["merge_review"] = "; ".join(notes)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/raw/trial/movies.csv")
    parser.add_argument("--cache", type=Path, default=ROOT / "data/raw/imdb_trial")
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/trial_combined.csv")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Cannot overwrite raw input")
    with args.input.open(encoding="utf-8-sig", newline="") as handle:
        wiki = list(csv.DictReader(handle))
    ids = []
    for row in wiki:
        movie_ids = [s["value"] for s in json.loads(row["imdb_ids"])]
        if len(movie_ids) != 1:
            parser.error(f"Expected one IMDb ID for {row['wikidata_id']}")
        ids.extend(movie_ids)
    if not ids or len(ids) != len(set(ids)):
        parser.error("Input must have unique, nonempty IMDb IDs")
    args.cache.mkdir(parents=True, exist_ok=True)
    sources = {source: extract(source, set(ids), args.cache) for source in SOURCES}
    merged = [merge_row(row, sources) for row in wiki]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".part")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(merged[0]))
        writer.writeheader()
        writer.writerows(merged)
    temporary.replace(args.output)
    summary = {"created_at_utc": now(), "input": str(args.input), "movies": len(merged),
               "rating_matches": sum(r["imdb_rating"] != "" for r in merged),
               "review_rows": sum(bool(r["merge_review"]) for r in merged),
               "sources": {s: {k: v for k, v in data.items() if k != "rows"}
                           for s, data in sources.items()}}
    args.output.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Saved {len(merged)} movies to {args.output}", flush=True)
    print(f"Ratings matched: {summary['rating_matches']}; rows flagged: {summary['review_rows']}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit("Stopped. Completed source extracts are cached; rerun to continue.")
    except (HTTPError, URLError, TimeoutError, EOFError) as error:
        raise SystemExit(f"IMDb scan failed: {error}. Completed extracts are safe; rerun to continue.")
