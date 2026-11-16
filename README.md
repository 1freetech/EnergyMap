# EnergyMap — U.S. energy infrastructure desktop atlas

A **read-only Python/Tkinter map viewer** for EIA-sourced and curated U.S. ≥1 GW energy infrastructure records. No browser, JavaScript, map-tile server, Plotly runtime, or internet connection is required to view the included datasets once installed.

## Start EnergyMap

Download the [complete repository ZIP](https://github.com/1freetech/EnergyMap/archive/refs/heads/main.zip) and extract it, retaining the `data/`, `assets/` and `desktop/` folders. Run with Python 3.12+ and Tkinter:

```sh
python desktop/energymap.py
```

The desktop entry script now includes its own map renderer; opening `energymap.py` by itself no longer raises `ModuleNotFoundError: atlas_view`. **Extract the whole ZIP for the simplest offline setup.** If you run only the `.py` script, it still needs the research and basemap data; its first-run recovery prompt can download and validate the public repository ZIP with your permission or use a complete local ZIP/folder. An install-free Windows, macOS or Linux executable can be downloaded from the latest **successful** [Python desktop build](https://github.com/1freetech/EnergyMap/actions/workflows/python-desktop.yml) → **Artifacts**. The automated native build bundles both `data/` and `assets/`. Actual Windows/macOS screen acceptance must be checked on those platforms; GitHub CI alone is not a full usability certification.

If the original JSON data is unavailable, EnergyMap can prompt for an explicit one-time public repository download or let you select a local complete repository ZIP/folder. It validates the eight research datasets and both map outlines. Downloaded data remains in `~/.energymap/EnergyMap-data.zip` for offline use. Saved custom site files from older versions are left untouched, but the editing interface is retired.

## Verified historical ≥1 GW atlas expansion

The default **All ≥1 GW sites** view includes **303 unique geocoded records**: 23 pre-existing curated plants plus 280 additional power stations. The separate **EIA ≥1 GW (2024)** view has **302** sourced plants across seven JSON files; **22** overlap curated plants and are suppressed *only in the combined view*. Existing state and national ranking datasets remain unchanged.

Every new EIA record carries a plant ID, reported location, ≥1,000 MW of **December 2024 operable nameplate capacity**, positive **calendar-2024 net generation (MWh)**, and direct EIA source references. **These are historical 2024 site and capacity records, not confirmation of current 2026 operation.** The sources, admission rules and reconciliation are explained in [EIA provenance](data/EIA-2024-PROVENANCE.md). Keep 2024 annual history separate from EIA's final 2025 and preliminary 2026 updates.

## What is new

- A real U.S. basemap with state outlines, a selected-state highlight, and Alaska/Hawaii geographic insets.
- A native **orthographic spinning globe** with real country boundaries, a **Spin globe / Stop spinning** control, and mouse-drag rotation. Like a Plotly orthographic projection, only hemisphere-facing points are visible.
- The selected dataset's actual latitude/longitude sites are overlaid as clickable dots. A missing coordinate is never invented or geocoded.
- Resizable panes and controls; concise table columns with a horizontal fallback scrollbar; full record names, notes, measurements and URLs in a vertically scrollable, word-wrapped details panel.
- Three vetted catalog views: **Operating plants**, **State rankings** (all 50 U.S. states), and **National top 10**. Search, local reload and opening original source articles remain available.
- Editing, personal-map creation, record import/export and deletion buttons are removed. The focus is reading established datasets rather than modifying them.

## What the records mean

The original source JSON records remain unchanged: `data/states-01.json` to `data/states-07-national.json` plus `data/operating-1gw.json`. The historic ranking corpus includes 50 state lists and ten national projects, while the operating layer is a curated selection, not a complete inventory of U.S. plants.

**MW denotes rated or planned power capacity, not generated energy.** MWh requires a measurement period. Planned data-center loads and operating generating stations are displayed as distinct kinds of records. Dot coordinates reflect original approximate source geographies, not exact land parcels.

## Basemap sources

- U.S. state outline vector data adapted from [PublicaMundi MappingAPI](https://github.com/PublicaMundi/MappingAPI/blob/master/data/geojson/us-states.json).
- Country boundaries adapted from [Natural Earth 1:110m Admin-0](https://www.naturalearthdata.com/), which is [public-domain map data](https://www.naturalearthdata.com/about/terms-of-use/).

The map vectors are simplified for a fast, entirely offline Tkinter canvas. Geographic borders are generalized and should not be used for navigation, legal boundaries, or survey measurements.

## Testing and build

```sh
python -m unittest discover -s desktop -p "test_*.py" -v
python -m unittest discover -s tests -p "test_*.py" -v
python desktop/energymap.py --check-data
```

Linux GUI smoke checks run in CI under Xvfb. The packaging workflow runs across Windows, macOS and Linux and checks the bundled datasets before launch; it does not replace real-device checks.

Project files: `desktop/energymap.py` (canonical, self-contained Python GUI, map projection, data loading), `data/eia2024-1gw-*.json` (verified historical additions), `assets/` (geography), `data/` (vetted records), `desktop/test_*.py` and `tests/test_data_integrity.py` (regressions).

Previous browser-version code remains in Git history; [migration context](https://github.com/1freetech/Bitcoinversus.tech/pull/2).
