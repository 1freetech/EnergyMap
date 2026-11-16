"""Map coverage, source provenance and category-driven marker regression tests."""
import unittest
from energymap import (build_catalogs, load_data, load_eia_catalog,
                       load_project_localities, _validate_project_localities,
                       AtlasMap)


class ProjectLocalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rankings, curated = load_data()
        eia = load_eia_catalog()
        cls.localities = load_project_localities()
        cls.catalogs = build_catalogs(rankings, curated, eia, cls.localities)

    def test_116_approximate_localities_and_40_unlocated_records(self):
        self.assertEqual(len(self.localities), 116)
        projects = self.catalogs["Data centers"]
        self.assertEqual(len(projects), 156)
        approximate = [p for p in projects if p.get("markerKind") == "locality"]
        missing = [p for p in projects if AtlasMap._coordinates(p) is None]
        self.assertEqual(len(approximate), 116)
        self.assertEqual(len(missing), 40)
        for row in approximate:
            with self.subTest(id=row["id"]):
                self.assertIsNotNone(AtlasMap._coordinates(row))
                self.assertIn("NOT verified facility coordinates",
                              row["locationPrecision"])
                self.assertTrue(row["mapLocationSource"].startswith("https://github.com/"))
        for row in missing:
            self.assertIsNone(AtlasMap._coordinates(row))

    def test_filter_views_keep_same_coordinates_and_no_duplicates(self):
        c = self.catalogs
        self.assertEqual(len(c["All sites"]), 459)
        self.assertEqual(len(c["All ≥1 GW"]), 373)
        self.assertEqual(len(c["Power plants"]), 303)
        self.assertEqual(len(c["State rankings"]), 459)
        self.assertEqual(len(c["National top 25"]), 25)
        self.assertEqual(len([x for x in c["All sites"]
                              if AtlasMap._coordinates(x)]), 419)
        self.assertGreater(sum(AtlasMap._coordinates(x) is not None
                               for x in c["Data centers ≥1 GW"]), 20)
        self.assertGreater(sum(AtlasMap._coordinates(x) is not None
                               for x in c["National top 25"]), 10)
        all_by_id = {x["id"]: x for x in c["All sites"]}
        for name in ("State rankings", "Data centers", "Data centers ≥1 GW",
                     "National top 25"):
            for row in c[name]:
                self.assertIs(row, all_by_id[row["id"]])

    def test_source_records_not_mutated(self):
        rankings, curated = load_data()
        self.assertTrue(all(r.get("lat") is None for r in rankings
                            if r.get("rank") is not None))
        self.assertTrue(all(r.get("markerKind") is None for r in rankings))

    def test_reject_bad_source_records(self):
        good = dict(next(iter(self.localities.values())))
        with self.assertRaises(ValueError):
            _validate_project_localities([[good, dict(good)]])
        with self.assertRaises(ValueError):
            _validate_project_localities([[dict(good, lat=999)]])
        with self.assertRaises(ValueError):
            _validate_project_localities([[dict(good, source="https://invalid.example")]])
        rankings, curated = load_data()
        with self.assertRaises(ValueError):
            build_catalogs(rankings, curated, load_eia_catalog(),
                           {"unmatched-id": good})
        with self.assertRaises(ValueError):
            build_catalogs(rankings, curated, load_eia_catalog(),
                           {good["id"]: dict(good, state="Wrong State")})

    def test_no_spurious_matador_or_county_centroid(self):
        c = self.catalogs["Data centers"]
        matador = next(r for r in c if r["id"] == "27440-1")
        self.assertEqual(matador["mapReferencePlace"], "Amarillo")
        self.assertNotEqual(matador["lat"], 34.01202)
        golden = next(r for r in c if r["name"] == "Golden Valley Technology Hub, Kern County")
        self.assertIsNone(AtlasMap._coordinates(golden))


if __name__ == "__main__":
    unittest.main()
