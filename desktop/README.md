# EnergyMap — Tkinter Desktop Atlas

Run `python desktop/energymap.py` from the **fully extracted** repository directory (Python 3.12+ / Tkinter).
Keep `desktop/atlas_view.py`, `data/*.json`, and `assets/*.geojson` together in their repository folders.
An executable built by the [Python desktop workflow](https://github.com/1freetech/EnergyMap/actions/workflows/python-desktop.yml) bundles all geography and research data.

## Read-only catalog

The desktop interface intentionally omits Add site, Edit, Delete, Import, Export and My map. It shows the existing operating plants, the 50-state rankings, and the national top ten with search, source links, and measured-vs-rated capacity distinctions. Former personal JSON site files remain unchanged under `~/.energymap/`.

## Maps

Select **United States** for real state boundaries, Alaska/Hawaii inset maps, and current dataset points. Select **World globe** for the orthographic global projection; use **Spin globe** to rotate continuously, **Stop spinning** to pause, or drag the map horizontally. The global boundary layer uses Natural Earth 1:110m public-domain geographic outlines; state outlines are adapted from PublicaMundi MappingAPI. Both are bundled for offline operation.

Only sites with actual coordinate fields are shown. Clicking a dot selects the corresponding table record. Details use a resizable, word-wrapped, scrolling pane; table columns can be adjusted or scrolled if the window is very narrow.

## Local recovery and tests

If the eight original data JSON files or the two geographic asset files are missing, choose the complete repository ZIP, select an extracted checkout, or allow an explicit one-time public GitHub download. Changes to the vetted source data are not introduced by any recovery step.

```sh
python -m unittest discover -s desktop -p 'test_*.py' -v
python -m unittest discover -s tests -p 'test_*.py' -v
python desktop/energymap.py --check-data
```

The native build workflow includes `--add-data "data:data"` and `--add-data "assets:assets"` and smoke-tests packaged startup. Windows and macOS still require real-device acceptance testing.
