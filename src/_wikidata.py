"""Internal Wikidata request and statement helpers used by enrichment."""

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
