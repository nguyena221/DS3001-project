"""Synthetic checks only: no IMDb records or network requests."""
import json
import gzip
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from merge_imdb import SOURCES, extract, merge_row


class MergeChecks(unittest.TestCase):
    def setUp(self):
        self.wiki = {"wikidata_id": "Q_TEST", "title": "Synthetic",
                     "imdb_ids": json.dumps([{"value": "tt_TEST"}]),
                     "languages": "[]", "countries": "[]", "budgets": "[]",
                     "release_dates": json.dumps([{"value": {
                         "time": "+2024-00-00T00:00:00Z", "precision": 9,
                         "calendarmodel": "http://www.wikidata.org/entity/Q1985727"}}])}
        self.sources = {s: {"rows": {}} for s in SOURCES}

    def test_missing_matches_preserved_and_date_not_invented(self):
        row = merge_row(self.wiki, self.sources)
        self.assertEqual(row["imdb_rating"], "")
        self.assertEqual(row["release_month"], "")
        self.assertEqual(row["planned_split"], "validation")
        self.assertIn("missing title.ratings", row["merge_review"])

    def test_source_authority_cast_order_and_nulls(self):
        self.sources["title.basics"]["rows"]["tt_TEST"] = [{
            "primaryTitle": "IMDb synthetic", "startYear": "2025",
            "titleType": "movie", "runtimeMinutes": "\\N", "genres": "Drama,Comedy"}]
        self.sources["title.principals"]["rows"]["tt_TEST"] = [
            {"category": "actor", "ordering": "3", "nconst": "nm_B"},
            {"category": "director", "ordering": "1", "nconst": "nm_D"},
            {"category": "actress", "ordering": "2", "nconst": "nm_A"}]
        row = merge_row(self.wiki, self.sources)
        self.assertEqual(json.loads(row["principal_cast_ids"]), ["nm_A", "nm_B"])
        self.assertEqual(row["runtime_minutes"], "")
        self.assertEqual(json.loads(row["genres"]), ["Drama", "Comedy"])
        self.assertEqual(row["release_year"], 2024)
        self.assertIn("release years differ", row["merge_review"])

    def test_ambiguous_ids_rejected(self):
        self.wiki["imdb_ids"] = '[{"value": "a"}, {"value": "b"}]'
        with self.assertRaises(ValueError):
            merge_row(self.wiki, self.sources)

    def test_stream_retains_all_principal_rows_and_reuses_cache(self):
        payload = ('tconst\tordering\tnconst\tcategory\n'
                   'tt_OTHER\t1\tnm_SKIP\tactor\n'
                   'tt_TEST\t1\tnm_A\tactor\n'
                   'tt_TEST\t2\tnm_B\tactress\n')
        response = io.BytesIO(gzip.compress(payload.encode()))
        response.headers = {}
        with tempfile.TemporaryDirectory() as folder:
            with patch('merge_imdb.urlopen', return_value=response) as network:
                first = extract('title.principals', {'tt_TEST'}, Path(folder))
                second = extract('title.principals', {'tt_TEST'}, Path(folder))
                self.assertEqual(len(first['rows']['tt_TEST']), 2)
                self.assertEqual(first, second)
                self.assertEqual(network.call_count, 1)


if __name__ == "__main__":
    unittest.main()
