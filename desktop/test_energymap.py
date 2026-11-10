"""Offline regression checks for the EnergyMap Python desktop model."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from energymap import load_data, validate_site, state_records, national_records, MAP_REGIONS, project_coordinate


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


    def test_geographic_viewports_cover_alaska_hawaii_and_world(self):
        examples = (
            ("Continental US", -122.3, 47.6),
            ("Alaska", -149.9, 61.2),
            ("Hawaii", -157.8, 21.3),
            ("World", 139.7, 35.7),
        )
        for region, lon, lat in examples:
            with self.subTest(region=region):
                point = project_coordinate(lon, lat, MAP_REGIONS[region], 800, 400)
                self.assertIsNotNone(point)
                self.assertTrue(0 <= point[0] <= 800)
                self.assertTrue(0 <= point[1] <= 400)
        self.assertIsNone(project_coordinate(-149.9, 61.2, MAP_REGIONS["Continental US"], 800, 400))
        self.assertIsNone(project_coordinate(None, 20, MAP_REGIONS["World"], 800, 400))
        self.assertIsNone(project_coordinate(float("nan"), 20, MAP_REGIONS["World"], 800, 400))



if __name__ == "__main__":
    unittest.main()
