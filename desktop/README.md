# EnergyMap — Python desktop application

Run `python desktop/energymap.py` with Python 3.12+ and Tkinter. Download the **whole repository**, since the desktop program reads seven state/national JSON files plus `data/operating-1gw.json`. No browser, Node.js, map-tile network or JavaScript code is used.

The app provides separate operating-plant, state, national, and personal views, search, local-coordinate point plots, article sources, site metadata, and custom-site add/edit/delete/import/export. **Refresh data** rereads vetted records from the extracted repository; it does not fetch a remote server or change the personal-site file.

Custom data is stored at `~/.energymap/my-sites.json`, portable through JSON import/export. Approximate dots are **not** a state-outline basemap; absent locations are deliberately left unmapped. Alaska, Hawaii and out-of-viewport points are still listed. Keep MW (power/capacity) distinct from MWh (energy in a period).

GitHub Actions builds PyInstaller executables for Windows, macOS and Linux: [Python desktop build](https://github.com/1freetech/EnergyMap/actions/workflows/python-desktop.yml). Builds are unsigned and require genuine platform acceptance checks before asserting full release parity.

```sh
python -m unittest discover -s desktop -p "test_*.py" -v
python -m unittest discover -s tests -p "test_*.py" -v
```

GUI smoke runs under Xvfb on Linux CI. The former web edition was removed in the Python-only conversion; see git history for the previous HTML/JavaScript source.
