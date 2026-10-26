"""Collect a small metadata pilot. No ratings are downloaded.

Run from the repository: python src/collect_wikidata.py --per-year 2
Uses only the Python standard library (Python 3.10 or newer).
"""

import argparse
import csv
import json
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
NEXT_QUERY_AT = 0.0
PROPERTIES = {
    "imdb_ids": "P345",
    "release_dates": "P577",
    "genres": "P136",
    "runtimes": "P2047",
    "languages": "P364",
    "countries": "P495",
    "directors": "P57",
    "budgets": "P2130",
}


def get_json(url, user_agent):
    """Make sequential requests; retry temporary server failures politely."""
    global NEXT_QUERY_AT
    is_query = url.startswith("https://query.wikidata.org/")
    for attempt in range(3):
        try:
            if is_query:
                remaining = NEXT_QUERY_AT - time.monotonic()
                if remaining > 0:
                    print(f"  Waiting {remaining:.0f}s to respect the query rate limit...", flush=True)
                    time.sleep(remaining)
                NEXT_QUERY_AT = time.monotonic() + 65
            request = Request(url, headers={"User-Agent": user_agent,
                                           "Accept": "application/json"})
            with urlopen(request, timeout=90) as response:
                result = json.load(response)
            time.sleep(1)
            return result
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
            wait = error.headers.get("Retry-After", "")
            retry_seconds = 0
            if wait.isdigit():
                retry_seconds = int(wait)
            elif wait:
                try:
                    retry_seconds = max(0, (parsedate_to_datetime(wait) - datetime.now(timezone.utc)).total_seconds())
                except (TypeError, ValueError, OverflowError):
                    pass
            delay = max(65 if error.code == 429 else 5 * (attempt + 1), retry_seconds)
            print(f"  HTTP {error.code}: waiting {delay:.0f}s before retry {attempt + 2}/3...", flush=True)
            time.sleep(delay)
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))


def candidate_query(year, count):
    # Select IDs first. Joining all optional fields here would multiply rows.
    return f'''PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?movie WHERE {{
  ?movie wdt:P31 wd:Q11424; wdt:P345 ?imdb; wdt:P577 ?date.
  FILTER(?date >= "{year}-01-01T00:00:00Z"^^xsd:dateTime &&
         ?date < "{year + 1}-01-01T00:00:00Z"^^xsd:dateTime)
}} ORDER BY ?movie LIMIT {count}'''


def fetch_entities(ids, user_agent):
    entities = {}
    for offset in range(0, len(ids), 50):
        params = urlencode({"action": "wbgetentities", "format": "json",
                            "ids": "|".join(ids[offset:offset + 50]),
                            "props": "labels|claims", "languages": "en"})
        result = get_json("https://www.wikidata.org/w/api.php?" + params, user_agent)
        entities.update(result["entities"])
    return entities


def statements(entity, property_id):
    """Keep all non-deprecated, known values; preserve precision and units."""
    values = []
    for claim in entity.get("claims", {}).get(property_id, []):
        snak = claim.get("mainsnak", {})
        if claim.get("rank") == "deprecated" or snak.get("snaktype") != "value":
            continue
        values.append({"value": snak["datavalue"]["value"],
                       "rank": claim.get("rank"),
                       "qualifiers": claim.get("qualifiers", {})})
    return values


def cached_selection(query, year):
    """Reuse a completed response only when its saved query matches exactly."""
    folders = sorted((ROOT / "data" / "raw").glob("wikidata_*"), reverse=True)
    # The first successful pilot was renamed for easier navigation.
    trial = ROOT / "data" / "raw" / "trial"
    if trial.is_dir():
        folders.append(trial)
    for folder in folders:
        query_file = folder / f"query_{year}.sparql"
        response_file = folder / f"selection_{year}.json"
        if query_file.exists() and response_file.exists():
            if query_file.read_text(encoding="utf-8") == query:
                result = json.loads(response_file.read_text(encoding="utf-8"))
                print(f"  Reusing saved {year} selection from {folder.name}", flush=True)
                return result
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-year", type=int, default=2,
                        help="Candidates per year; 2 gives up to 20, 10 up to 100")
    parser.add_argument("--start-year", type=int, default=2016)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--user-agent", default="DS3001-MovieMetadataPilot/0.1",
                        help="Descriptive client name; optionally add your contact URL")
    args = parser.parse_args()
    if not (1 <= args.per_year <= 50 and 1900 <= args.start_year <= args.end_year <= 2100):
        parser.error("Use 1–50 candidates per year and ordered years between 1900 and 2100.")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = ROOT / "data" / "raw" / f"wikidata_{stamp}"
    output.mkdir(parents=True)
    selected = {}
    for year in range(args.start_year, args.end_year + 1):
        query = candidate_query(year, args.per_year)
        (output / f"query_{year}.sparql").write_text(query, encoding="utf-8")
        params = urlencode({"query": query, "format": "json"})
        print(f"Finding up to {args.per_year} candidates for {year}...", flush=True)
        result = cached_selection(query, year)
        if result is None:
            result = get_json("https://query.wikidata.org/sparql?" + params, args.user_agent)
        (output / f"selection_{year}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        for binding in result["results"]["bindings"]:
            qid = binding["movie"]["value"].rsplit("/", 1)[-1]
            selected.setdefault(qid, []).append(year)

    if not selected:
        raise RuntimeError(f"No candidates found. Saved queries in {output}")
    print(f"Fetching metadata for {len(selected)} unique movies...", flush=True)
    entities = fetch_entities(list(selected), args.user_agent)
    (output / "entities.json").write_text(json.dumps(entities, indent=2), encoding="utf-8")
    rows = []
    for qid, years in selected.items():
        entity = entities[qid]
        row = {"wikidata_id": qid,
               "title": entity.get("labels", {}).get("en", {}).get("value", qid),
               "candidate_years": years}
        for name, property_id in PROPERTIES.items():
            row[name] = statements(entity, property_id)
        rows.append(row)
    # Arrays are JSON inside each CSV cell, so multiple values remain intact.
    with (output / "movies.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False)
                             if isinstance(value, list) else value
                             for key, value in row.items()})
    summary = {"collected_at_utc": stamp, "unique_movies": len(rows),
               "arguments": vars(args),
               "missing_counts": {name: sum(not row[name] for row in rows)
                                  for name in PROPERTIES}}
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Saved {len(rows)} movies to {output}")
    for name, count in summary["missing_counts"].items():
        print(f"  {name}: {count}/{len(rows)} missing ({count / len(rows):.0%})")


if __name__ == "__main__":
    try:
        main()
    except (HTTPError, URLError, TimeoutError) as error:
        raise SystemExit(f"Wikidata request failed: {error}. Partial files are retained; try again later.")
    except KeyboardInterrupt:
        raise SystemExit("Stopped. Completed selections are saved and will be reused on the next run.")
