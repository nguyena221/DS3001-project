import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from collect_data_imdb import priority
from add_wikidata_to_imdb import lookup_query
from filter_movies import exclusion_reason


class ImdbFirstChecks(unittest.TestCase):
    def test_sampling_reproducible_and_seeded(self):
        self.assertEqual(priority('tt123', 42), priority('tt123', 42))
        self.assertNotEqual(priority('tt123', 42), priority('tt123', 43))

    def test_lookup_includes_all_ids_and_rejects_query_text(self):
        query = lookup_query({'tt123', 'tt456'})
        self.assertIn('"tt123"', query)
        self.assertIn('"tt456"', query)
        self.assertNotIn('P31', query)
        with self.assertRaises(ValueError):
            lookup_query({'tt123" } UNION {'})

    def test_dates_required_for_final_scope(self):
        row = {'imdb_title_type': 'tvMovie', 'imdb_rating': '6', 'planned_split': 'review'}
        self.assertIn('held for review', exclusion_reason(row))
        row['planned_split'] = 'outside_scope'
        self.assertIn('outside', exclusion_reason(row))
        row['planned_split'] = 'test'
        self.assertEqual(exclusion_reason(row), '')


if __name__ == '__main__':
    unittest.main()
