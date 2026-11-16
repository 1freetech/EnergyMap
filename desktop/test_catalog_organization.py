"""Cross-view audit: every ranking site appears exactly once in the master catalog."""
from __future__ import annotations

import unittest

from energymap import (
    NATIONAL_TO_STATE_ID, build_catalogs, load_data, load_eia_catalog,
    reconcile_data_center_rankings, sort_catalog,
)


class CatalogOrganizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rankings, curated = load_data()
        eia = load_eia_catalog()
        cls.rankings = rankings
        cls.catalogs = build_catalogs(rankings, curated, eia)

    def test_every_original_state_and_national_project_is_preserved(self):
        profiles = self.catalogs["Data centers"]
        self.assertEqual(len(profiles), 156)
        self.assertEqual(len({r["id"] for r in profiles}), 156)
        raw_state_ids = {r["id"] for r in self.rankings if r.get("rank") is not None}
        raw_national_ids = {r["id"] for r in self.rankings if r.get("nationalRank") is not None}
        self.assertEqual({r["id"] for r in profiles}, raw_state_ids)
        self.assertEqual(set(NATIONAL_TO_STATE_ID), raw_national_ids)
        self.assertEqual(
            {r["nationalSourceID"] for r in self.catalogs["National top 10"]},
            raw_national_ids,
        )
        self.assertEqual(
            {r["id"] for r in self.catalogs["National top 10"]},
            set(NATIONAL_TO_STATE_ID.values()),
        )
        for row in self.catalogs["National top 10"]:
            self.assertIn(row, self.catalogs["All sites"])
            self.assertIn(row, self.catalogs["All ≥1 GW"])
            self.assertIn(row, self.catalogs["State rankings"])

    def test_counts_unique_sites_by_type(self):
        c = self.catalogs
        self.assertEqual(len(c["EIA plants (2024)"]), 302)
        self.assertEqual(len(c["Curated plants"]), 23)
        self.assertEqual(len(c["Power plants"]), 303)
        self.assertEqual(len(c["Data centers"]), 156)
        self.assertEqual(len(c["Data centers ≥1 GW"]), 70)
        self.assertEqual(len(c["State rankings"]), 156)
        self.assertEqual(len(c["National top 10"]), 10)
        self.assertEqual(len(c["All sites"]), 459)
        self.assertEqual(len(c["All ≥1 GW"]), 373)
        self.assertEqual(len({r["id"] for r in c["All sites"]}), 459)
        self.assertEqual(
            {r["id"] for r in c["All ≥1 GW"]},
            {r["id"] for r in c["All sites"]
             if isinstance(r.get("capacityMW"), (int, float))
             and r["capacityMW"] >= 1000},
        )

    def test_different_power_scopes_not_mistaken_for_same_measure(self):
        by_id = {r["id"]: r for r in self.catalogs["Data centers"]}
        roswell = by_id["27242-1"]
        self.assertEqual(roswell["capacityMW"], 6500)
        self.assertEqual(roswell["statePublishedMW"], 4960)
        self.assertEqual(roswell["nationalPublishedMW"], 6500)
        self.assertIn("onsite generation", roswell["capacityBasis"])
        self.assertIn("IT load", roswell["capacityBasis"])
        homer = by_id["27343-1"]
        self.assertEqual(homer["capacityMW"], 4400)
        self.assertEqual(homer["statePublishedMW"], 4500)
        self.assertIn("4,500", homer["reconciliationNote"])
        self.assertIn("4,400", homer["reconciliationNote"])

    def test_sort_all_views_numeric_high_to_low_and_reverse(self):
        for view, items in self.catalogs.items():
            with self.subTest(view=view):
                desc = sort_catalog(items, "capacity", True, view)
                asc = sort_catalog(items, "capacity", False, view)
                def values(records):
                    return [r["capacityMW"] for r in records
                            if isinstance(r.get("capacityMW"), (int, float))]
                self.assertEqual(values(desc), sorted(values(desc), reverse=True))
                self.assertEqual(values(asc), sorted(values(asc)))
                self.assertEqual({r["id"] for r in items}, {r["id"] for r in desc})
                self.assertEqual({r["id"] for r in items}, {r["id"] for r in asc})
        national = sort_catalog(self.catalogs["National top 10"], "rank", False, "National top 10")
        self.assertEqual([r["nationalRank"] for r in national], list(range(1, 11)))
        national_names = sort_catalog(self.catalogs["National top 10"], "name", False, "National top 10")
        self.assertEqual(
            [r["nationalName"] for r in national_names],
            sorted((r["nationalName"] for r in national_names), key=str.casefold))
        state = sort_catalog(self.catalogs["State rankings"], "category", False, "State rankings")
        self.assertEqual(len(state), 156)
        by_state = sort_catalog(self.catalogs["All sites"], "state", False, "All sites")
        self.assertEqual(len(by_state), 459)

    def test_missing_capacity_sort_to_end(self):
        rows = [{"id":"a","name":"A","capacityMW":1200},
                {"id":"b","name":"B","capacityMW":None},
                {"id":"c","name":"C","capacityMW":1100}]
        self.assertEqual([r["id"] for r in sort_catalog(rows, "capacity", True)],
                         ["a", "c", "b"])
        self.assertEqual([r["id"] for r in sort_catalog(rows, "capacity", False)],
                         ["c", "a", "b"])


if __name__ == "__main__":
    unittest.main()
