"""Offline regression checks for the EnergyMap Python desktop model."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from energymap import (load_data, validate_site, state_records, national_records,
                       table_column_widths, row_display_number)


class EnergyMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rankings, cls.operating = load_data()

    def test_existing_data_loads(self):
        self.assertGreaterEqual(len(self.operating), 20)
        self.assertGreaterEqual(len(self.rankings), 150)
        self.assertEqual(len({r["state"] for r in self.rankings if r.get("rank")}), 50)

    def test_rankings_keep_source_order(self):
        texas = state_records(self.rankings, "Texas")
        self.assertGreaterEqual(len(texas), 3)
        self.assertEqual([x["rank"] for x in texas],
                         sorted(x["rank"] for x in texas))
        national = national_records(self.rankings)
        self.assertEqual(len(national), 10)
        self.assertEqual([x["nationalRank"] for x in national], list(range(1, 11)))

    def test_table_columns_fit_every_window_width(self):
        columns = ("rank", "name", "state", "category", "capacity")
        for viewport in (250, 400, 520, 600, 850, 1400):
            with self.subTest(viewport=viewport):
                widths = table_column_widths(viewport, columns)
                self.assertEqual(tuple(widths), columns)
                self.assertEqual(sum(widths.values()), viewport)
                self.assertTrue(all(width > 0 for width in widths.values()))
                self.assertGreater(widths["name"], widths["rank"])
        self.assertEqual(table_column_widths(500, ()), {})

    def test_row_labels_do_not_misrepresent_computed_ranks(self):
        site = {"stateRank": 3, "nationalComputedRank": 12}
        self.assertEqual(row_display_number(site, "All sites", 18), 18)
        self.assertEqual(row_display_number(site, "Power plants", 4), 4)
        self.assertEqual(row_display_number(site, "State rankings", 18), 3)
        self.assertEqual(row_display_number(site, "National top 25", 18), 12)
        self.assertEqual(row_display_number({}, "State rankings", 5), "N/R")

    def test_personal_site_validation(self):
        item = validate_site({"name":"Site A", "state":"WA",
                              "lat":"47.6", "lon":"-122.3",
                              "capacityMW":"80", "article":"https://example.com"})
        self.assertEqual(item["capacityMW"], 80)
        self.assertTrue(item["id"].startswith("personal-"))
        with self.assertRaises(ValueError):
            validate_site({"name":"Bad", "state":"WA", "lat":"92", "lon":"0"})
        with self.assertRaises(ValueError):
            validate_site({"name":"Bad", "state":"WA", "energyMWh":"200"})


if __name__ == "__main__":
    unittest.main()
