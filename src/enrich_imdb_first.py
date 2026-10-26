"""Add Wikidata supplements to the IMDb-first pilot; keep unmatched IDs visible."""
import csv
import json
import re
from urllib.parse import urlencode

from _wikidata import get_json, fetch_entities, statements
from _imdb import ROOT, SOURCES, extract, merge_row, now
from collect_imdb_first import download


def lookup_query(ids):
    if not all(re.fullmatch(r"tt\d+", value) for value in ids):
        raise ValueError("Unexpected IMDb identifier")
    values = " ".join(json.dumps(value) for value in sorted(ids))
    return ('PREFIX wdt: <http://www.wikidata.org/prop/direct/>\n'
            'SELECT DISTINCT ?imdb ?movie WHERE {\n'
            f'VALUES ?imdb {{ {values} }}\n?movie wdt:P345 ?imdb .\n}}')


def main():
    folder = ROOT / "data/raw/imdb_first"
    with (folder / "candidates.csv").open(encoding="utf-8-sig", newline="") as handle:
        candidates = list(csv.DictReader(handle))
    ids = {r["tconst"] for r in candidates}
    query = lookup_query(ids)
    response_path, query_path = folder / "wikidata_lookup.json", folder / "wikidata_lookup.sparql"
    agent = "DS3001-MovieMetadataPilot/0.3"
    if response_path.exists() and query_path.exists() and query_path.read_text(encoding="utf-8") == query:
        result = json.loads(response_path.read_text(encoding="utf-8"))
        print("Reusing saved Wikidata ID lookup", flush=True)
    else:
        # Save the query after its response, so failed refreshes cannot validate stale data.
        print(f"Looking up {len(ids)} IMDb IDs in one Wikidata query...", flush=True)
        result = get_json("https://query.wikidata.org/sparql?" + urlencode({"query": query, "format": "json"}), agent)
        response_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        query_path.write_text(query, encoding="utf-8")
    matches = {imdb: set() for imdb in ids}
    for binding in result["results"]["bindings"]:
        matches[binding["imdb"]["value"]].add(binding["movie"]["value"].rsplit("/", 1)[-1])
    unique_qids = sorted({next(iter(qids)) for qids in matches.values() if len(qids) == 1})
    entities = {}
    entity_folder = folder / "wikidata_entities"
    entity_folder.mkdir(exist_ok=True)
    missing = []
    for qid in unique_qids:
        path = entity_folder / f"{qid}.json"
        if path.exists():
            entities[qid] = json.loads(path.read_text(encoding="utf-8"))
        else:
            missing.append(qid)
    for offset in range(0, len(missing), 50):
        batch = fetch_entities(missing[offset:offset + 50], agent)
        for qid, entity in batch.items():
            (entity_folder / f"{qid}.json").write_text(json.dumps(entity, indent=2), encoding="utf-8")
            entities[qid] = entity
    print(f"Wikidata: {len(unique_qids)} unambiguous entities; fetching IMDb cast/crew...", flush=True)
    for source in ("title.crew", "title.principals"):
        if not (folder / f"{source}.json").exists():
            download(source, folder)
    sources = {s: extract(s, ids, folder) for s in SOURCES}
    merged = []
    for candidate in candidates:
        imdb = candidate["tconst"]
        qids = matches[imdb]
        qid = next(iter(qids)) if len(qids) == 1 else ""
        entity = entities.get(qid, {})
        wiki = {"wikidata_id": qid, "title": entity.get("labels", {}).get("en", {}).get("value", candidate["primaryTitle"]),
                "imdb_ids": json.dumps([{"value": imdb}])}
        for name, prop in {"languages": "P364", "countries": "P495", "budgets": "P2130", "release_dates": "P577"}.items():
            wiki[name] = json.dumps(statements(entity, prop))
        row = merge_row(wiki, sources)
        row["wikidata_match_status"] = "matched" if qid else ("ambiguous" if qids else "unmatched")
        row["wikidata_matching_ids"] = json.dumps(sorted(qids))
        if not qid:
            row["merge_review"] = (row["merge_review"] + "; Wikidata " + row["wikidata_match_status"]).strip("; ")
        merged.append(row)
    output = ROOT / "data/processed/imdb_first_combined.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(merged[0]))
        writer.writeheader()
        writer.writerows(merged)
    summary = {"created_at_utc": now(), "candidates": len(merged),
               "match_status": {status: sum(r["wikidata_match_status"] == status for r in merged) for status in ("matched", "unmatched", "ambiguous")},
               "planned_splits": {split: sum(r["planned_split"] == split for r in merged) for split in ("train", "validation", "test", "review", "outside_scope")}}
    output.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Saved {output}\n{json.dumps(summary, indent=2)}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit("Stopped; saved lookups, entities, and completed IMDb extracts can be reused.")
