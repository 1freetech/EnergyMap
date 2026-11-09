"""Python-only validation of historical rankings and operating-plant records."""
from __future__ import annotations

import json
import math
import unittest
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NON_PYTHON_PROGRAMS = {".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".html", ".htm", ".css", ".scss"}


def data(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


class AtlasIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all = [x for i in range(1, 7) for x in data(f"states-{i:02d}.json")]
        cls.all += data("states-07-national.json")
        cls.operating = data("operating-1gw.json")

    def test_history_50_states_and_national_top_10(self):
        all_records = self.all
        state_records = [p for p in all_records if p.get("rank") is not None]
        national_records = [p for p in all_records if p.get("nationalRank") is not None]
        self.assertEqual(len(all_records), 166)
        self.assertEqual(len(state_records), 156)
        self.assertEqual(len(national_records), 10)
        self.assertEqual(len({p["id"] for p in all_records}), len(all_records))
        counts = Counter(p["state"] for p in state_records)
        self.assertEqual(len(counts), 50)
        for state, count in counts.items():
            target = 7 if state == "Texas" else 5 if state == "Virginia" else 3
            self.assertEqual(count, target, state)
            ranks = sorted(p["rank"] for p in state_records if p["state"] == state)
            self.assertEqual(ranks, list(range(1, target + 1)), state)
        self.assertEqual(sorted(p["nationalRank"] for p in national_records),
                         list(range(1, 11)))

    def test_historic_records_have_source_and_capacity_basis(self):
        for record in self.all:
            with self.subTest(id=record.get("id")):
                for key in ("name", "heading", "brief", "article", "capacityLabel"):
                    self.assertTrue(record.get(key), (record.get("id"), key))
                self.assertTrue(record["article"].startswith("https://bitcoinversus.tech/"))
                cap = record.get("capacityMW")
                self.assertTrue(cap is None or
                                (isinstance(cap, (int, float)) and
                                 not isinstance(cap, bool) and math.isfinite(cap) and cap >= 0))

    def test_operating_layer_is_separate_and_sourced(self):
        ids = {p["id"] for p in self.all}
        names = set()
        self.assertGreaterEqual(len(self.operating), 20)
        for plant in self.operating:
            with self.subTest(id=plant.get("id")):
                self.assertTrue(plant["id"].startswith("operating-us-"))
                self.assertNotIn(plant["id"], ids)
                ids.add(plant["id"])
                name = plant["name"].strip().casefold()
                self.assertNotIn(name, names)
                names.add(name)
                self.assertEqual(plant["status"], "operating")
                self.assertTrue(isinstance(plant["capacityMW"], (int, float)))
                self.assertTrue(math.isfinite(plant["capacityMW"]))
                self.assertGreaterEqual(plant["capacityMW"], 1000)
                for key in ("capacityLabel", "capacityBasis", "energyType",
                            "locationLabel", "brief", "articleTitle", "sourceOrganization"):
                    self.assertTrue(plant.get(key), (plant["id"], key))
                self.assertIn("approximate", plant["locationPrecision"])
                self.assertGreaterEqual(plant["lat"], 24)
                self.assertLessEqual(plant["lat"], 50)
                self.assertGreaterEqual(plant["lon"], -125)
                self.assertLessEqual(plant["lon"], -66)
                self.assertTrue(plant["article"].startswith("https://"))
                self.assertLessEqual(date.fromisoformat(plant["verificationDate"]), date.today())
                self.assertIsNone(plant["productionMW"])
                self.assertIsNone(plant["energyMWh"])

    def test_no_non_python_application_code(self):
        offenders = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*")
                     if p.is_file() and p.suffix.lower() in NON_PYTHON_PROGRAMS]
        self.assertEqual(offenders, [])
        self.assertTrue((ROOT / "desktop/energymap.py").is_file())


if __name__ == "__main__":
    unittest.main()
