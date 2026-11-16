"""Catch regression where clicking energymap.py from an extracted ZIP fails import."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from energymap import AtlasMap, clip_hemisphere, project_orthographic, rings_from_features


class StandaloneEntryTests(unittest.TestCase):
    def test_atlas_functions_exported_from_entry(self):
        self.assertTrue(callable(project_orthographic))
        self.assertTrue(callable(clip_hemisphere))
        self.assertTrue(callable(rings_from_features))
        self.assertEqual(AtlasMap.__name__, "AtlasMap")

    def test_lone_script_import_in_isolated_python(self):
        """Simulate VS Code extracting only the clicked script from a ZIP."""
        source = Path(__file__).resolve().parent / "energymap.py"
        with tempfile.TemporaryDirectory(prefix="energymap_only_") as temp:
            target = Path(temp) / "energymap.py"
            shutil.copyfile(source, target)
            self.assertFalse((Path(temp) / "atlas_view.py").exists())
            completed = subprocess.run(
                [sys.executable, "-I", "-c",
                 "import runpy,sys; "
                 "ns=runpy.run_path(sys.argv[1],run_name='import_only'); "
                 "assert callable(ns['AtlasMap']) and callable(ns['project_orthographic'])",
                 str(target)],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(completed.returncode, 0,
                             completed.stdout + "\n" + completed.stderr)


if __name__ == "__main__":
    unittest.main()
