"""Validate sourced 1GW+ historical additions and prevent duplicate map pins."""
import unittest
from energymap import (
    EIA_PATHS, CURATED_EIA_CODES, combine_power_catalog, load_data,
    load_eia_catalog, _validate_eia_catalog,
)


class HistoricalEiaAtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rankings, cls.curated = load_data()
        cls.eia = load_eia_catalog()

    def test_all_51_state_source_groups_imported(self):
        self.assertEqual(len(EIA_PATHS), 7)
        self.assertEqual(len(self.eia), 302)
        self.assertEqual(len({r["eiaPlantCode"] for r in self.eia}), 302)
        self.assertGreaterEqual(len({r["state"] for r in self.eia}), 30)

    def test_no_unverified_or_subthreshold_record(self):
        for row in self.eia:
            with self.subTest(plant=row["eiaPlantCode"]):
                self.assertGreaterEqual(row["capacityMW"], 1000)
                self.assertGreater(row["energyMWh"], 0)
                self.assertEqual(row["sourcePeriod"], "2024-12")
                self.assertIn("historical", row["status"])
                self.assertGreaterEqual(row["lat"], -90)
                self.assertLessEqual(row["lat"], 90)
                self.assertGreaterEqual(row["lon"], -180)
                self.assertLessEqual(row["lon"], 180)
                self.assertTrue(row["article"].startswith("https://www.eia.gov/"))

    def test_combined_view_removes_curated_duplicates(self):
        out = combine_power_catalog(self.curated, self.eia)
        self.assertEqual(len(self.curated), 23)
        self.assertEqual(len(CURATED_EIA_CODES), 22)
        self.assertEqual(len(out), 303)
        self.assertEqual(len({r["id"] for r in out}), len(out))
        self.assertEqual(len([r for r in out if r.get("eiaPlantCode")]), 280)

    def test_validation_rejects_duplicate_and_wrong_capacity(self):
        good = dict(self.eia[0])
        with self.assertRaises(ValueError):
            _validate_eia_catalog([[good, dict(good)]])
        bad = dict(good, capacityMW=999.99, eiaPlantCode="999999")
        with self.assertRaises(ValueError):
            _validate_eia_catalog([[bad]])


if __name__ == "__main__":
    unittest.main()
