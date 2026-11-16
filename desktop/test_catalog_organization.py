"""Cross-view audit: rank all 459 canonical sites by state, compute national Top 25."""
from __future__ import annotations
import unittest
from collections import Counter, defaultdict

from energymap import (
    NATIONAL_TO_STATE_ID, build_catalogs, load_data, load_eia_catalog,
    sort_catalog, _capacity_order, _has_capacity, assign_state_ranks,
)


class CatalogOrganizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rankings, curated = load_data()
        eia = load_eia_catalog()
        cls.catalogs = build_catalogs(cls.rankings, curated, eia)

    def test_national_original_top10_crosswalk_remains_intact(self):
        c = self.catalogs
        projects = c["Data centers"]
        self.assertEqual(len(projects), 156)
        raw_state = {r["id"] for r in self.rankings if r.get("rank") is not None}
        raw_national = {r["id"] for r in self.rankings if r.get("nationalRank") is not None}
        self.assertEqual({r["id"] for r in projects}, raw_state)
        self.assertEqual(set(NATIONAL_TO_STATE_ID), raw_national)
        original_ten = [p for p in projects if p.get("nationalRank") is not None]
        self.assertEqual(len(original_ten), 10)
        self.assertEqual({p["nationalSourceID"] for p in original_ten}, raw_national)
        self.assertTrue({p["id"] for p in original_ten}.issubset(
            {p["id"] for p in c["National top 25"]}))

    def test_every_state_rank_includes_all_source_types(self):
        c = self.catalogs
        self.assertEqual(len(c["State rankings"]), 459)
        self.assertEqual({p["id"] for p in c["State rankings"]},
                         {p["id"] for p in c["All sites"]})
        states = defaultdict(list)
        for row in c["State rankings"]:
            states[row["state"]].append(row)
        self.assertEqual(len(states), 50)
        self.assertEqual(sum(len(v) for v in states.values()), 459)
        for state, rows in states.items():
            with self.subTest(state=state):
                self.assertEqual(len(rows), len([r for r in c["All sites"]
                                                 if r["state"] == state]))
                descending = sorted(rows, key=_capacity_order)
                prior = None
                for position, row in enumerate(descending, start=1):
                    if _has_capacity(row):
                        expected = position if row["capacityMW"] != prior else expected
                        self.assertEqual(row["stateRank"], expected)
                        prior = row["capacityMW"]
                    else:
                        self.assertIsNone(row["stateRank"])
                self.assertGreaterEqual(len(rows), 3)

    def test_top25_is_calculated_from_all_156_unique_campuses(self):
        c = self.catalogs
        ranked = c["National top 25"]
        self.assertEqual(len(ranked), 25)
        self.assertEqual(len({x["id"] for x in ranked}), 25)
        self.assertEqual([r["nationalComputedRank"] for r in ranked],
                         list(range(1, 26)))
        source_order = sorted((r for r in c["Data centers"] if _has_capacity(r)),
                              key=_capacity_order)[:25]
        self.assertEqual([r["id"] for r in ranked],
                         [r["id"] for r in source_order])
        self.assertEqual(ranked[0]["capacityMW"], 11000)
        self.assertEqual(ranked[-1]["capacityMW"], 2000)
        self.assertTrue(all(r["recordType"] == "Data centers / campuses" for r in ranked))
        self.assertTrue(all(r in c["All sites"] and r in c["All ≥1 GW"] for r in ranked))
        self.assertEqual(len([r for r in ranked if r.get("nationalRank") is not None]), 10)

    def test_counts_unique_sites_by_type(self):
        c = self.catalogs
        for view, expected in {
            "EIA plants (2024)": 302, "Curated plants": 23, "Power plants": 303,
            "Data centers": 156, "Data centers ≥1 GW": 70,
            "State rankings": 459, "National top 25": 25,
            "All sites": 459, "All ≥1 GW": 373,
        }.items():
            self.assertEqual(len(c[view]), expected, view)
        self.assertEqual(len({r["id"] for r in c["All sites"]}), 459)
        self.assertEqual({r["id"] for r in c["All ≥1 GW"]},
                         {r["id"] for r in c["All sites"]
                          if _has_capacity(r) and r["capacityMW"] >= 1000})

    def test_conflicting_power_scopes_are_still_explicit(self):
        by_id = {r["id"]: r for r in self.catalogs["Data centers"]}
        roswell, homer = by_id["27242-1"], by_id["27343-1"]
        self.assertEqual((roswell["capacityMW"], roswell["statePublishedMW"]),
                         (6500, 4960))
        self.assertEqual((homer["capacityMW"], homer["statePublishedMW"]),
                         (4400, 4500))
        self.assertIn("onsite generation", roswell["capacityBasis"])
        self.assertIn("IT load", roswell["capacityBasis"])
        self.assertIn("4,500", homer["reconciliationNote"])
        self.assertIn("4,400", homer["reconciliationNote"])

    def test_sort_by_capacity_rank_and_other_headers(self):
        for view, rows in self.catalogs.items():
            with self.subTest(view=view):
                for descending in (True, False):
                    sorted_rows = sort_catalog(rows, "capacity", descending, view)
                    actual = [r["capacityMW"] for r in sorted_rows if _has_capacity(r)]
                    self.assertEqual(actual, sorted(actual, reverse=descending))
                    self.assertEqual({r["id"] for r in sorted_rows},
                                     {r["id"] for r in rows})
        national = sort_catalog(self.catalogs["National top 25"],
                                "rank", False, "National top 25")
        self.assertEqual([x["nationalComputedRank"] for x in national],
                         list(range(1, 26)))
        for state in {"Washington", "Texas", "Alaska", "Maine"}:
            subset = [r for r in self.catalogs["State rankings"] if r["state"] == state]
            ranked = sort_catalog(subset, "rank", False, "State rankings")
            valid = [r["stateRank"] for r in ranked if r.get("stateRank") is not None]
            self.assertEqual(valid, sorted(valid))
        for column in ("state", "category", "name"):
            sorted_rows = sort_catalog(self.catalogs["State rankings"],
                                       column, False, "State rankings")
            self.assertEqual(len(sorted_rows), 459)

    def test_equal_mw_share_state_rank_and_unknown_mw_unranked(self):
        sample = [
            {"id":"a", "name":"A", "state":"Texas", "capacityMW":2000},
            {"id":"b", "name":"B", "state":"Texas", "capacityMW":2000},
            {"id":"c", "name":"C", "state":"Texas", "capacityMW":1000},
            {"id":"d", "name":"D", "state":"Texas", "capacityMW":None},
            {"id":"e", "name":"E", "state":"Oregon", "capacityMW":500},
        ]
        assign_state_ranks(sample)
        self.assertEqual([r["stateRank"] for r in sample], [1,1,3,None,1])
        self.assertEqual([x["id"] for x in sort_catalog(sample[:4], "capacity", False)],
                         ["c","a","b","d"])


if __name__ == "__main__":
    unittest.main()
