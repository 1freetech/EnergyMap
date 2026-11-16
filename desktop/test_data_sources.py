"""Regression tests for EnergyMap data lookup, ZIP reuse and first-run recovery."""
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import energymap as app


class EnergyMapDataSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.make_files(self.root)

    @staticmethod
    def make_files(root):
        for idx, relative in enumerate(app.DATA_PATHS):
            p = root / relative
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps([{"name": f"Site {idx}", "state": "WA"}]), encoding="utf-8")

        for relative in app.GEO_FILES:
            p = root / relative
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps({"type": "FeatureCollection", "features": []}), encoding="utf-8")
        for index, relative in enumerate(app.EIA_PATHS):
            p = root / relative
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps([{
                "id": f"eia2024-{index+1}",
                "eiaPlantCode": str(index + 1), "name": f"EIA fixture {index+1}",
                "capacityMW": 1000, "lat": 35.0, "lon": -100.0,
                "energyMWh": 100, "energyType": "gas", "sourcePeriod": "2024-12",
            }]), encoding="utf-8")

    def make_zip(self, name="energy-map.zip"):
        zpath = self.root / name
        with zipfile.ZipFile(zpath, "w") as archive:
            for relative in (*app.DATA_PATHS, *app.GEO_FILES, *app.EIA_PATHS):
                archive.write(self.root / relative, f"EnergyMap-main/{relative}")
        return zpath

    def test_data_loads_from_repo_root_or_data_folder(self):
        for p in (self.root, self.root / "data"):
            a, b = app.load_data(p)
            self.assertEqual(len(a), 7)
            self.assertEqual(len(b), 1)

    def test_repo_zip_loads_without_extraction(self):
        archive = self.make_zip()
        a, b = app.load_data(archive)
        self.assertEqual(a[0]["name"], "Site 0")
        self.assertEqual(b[0]["name"], "Site 7")
        us, world = app.load_geo_data(archive)
        self.assertEqual(us["type"], "FeatureCollection")
        self.assertEqual(world["type"], "FeatureCollection")
        self.assertEqual(len(app.load_eia_catalog(archive)), 7)

    def test_missing_archive_file_is_rejected(self):
        zpath = self.root / "missing.zip"
        with zipfile.ZipFile(zpath, "w") as archive:
            archive.write(self.root / app.DATA_PATHS[0], "EnergyMap-main/data/states-01.json")
        with self.assertRaises(FileNotFoundError):
            app.load_data(zpath)

    def test_partial_checkout_is_not_silently_accepted(self):
        (self.root / app.DATA_PATHS[3]).unlink()
        with self.assertRaises(FileNotFoundError):
            app.load_data(self.root)

    def test_selected_path_is_reused(self):
        store = self.root / "user"
        store.mkdir()
        (store / "data-source.txt").write_text(str(self.root), encoding="utf-8")
        with patch.object(app, "_data_store", return_value=store), \
             patch.object(app, "__file__", str(store / "standalone.py")), \
             patch.object(app.sys, "executable", str(store / "python.exe")), \
             patch.object(app.sys, "_MEIPASS", None, create=True), \
             patch.object(app.Path, "cwd", return_value=store):
            a, b = app.load_data()
        self.assertEqual(len(a), 7)
        self.assertEqual(len(b), 1)

    def test_first_run_download_is_explicit_and_reusable(self):
        raw = self.make_zip().read_bytes()
        cache = self.root / "cache"
        with patch.object(app, "_data_store", return_value=cache), \
             patch.object(app.urllib.request, "urlopen", return_value=io.BytesIO(raw)) as fake:
            dest = app.download_repo_data()
            self.assertEqual(dest, cache / "EnergyMap-data.zip")
            self.assertEqual(len(app.load_data(dest)[0]), 7)
            self.assertEqual(len(app.load_geo_data(dest)), 2)
            self.assertEqual(len(app.load_eia_catalog(dest)), 7)
            fake.assert_called_once()


if __name__ == "__main__":
    unittest.main()
