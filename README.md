# EnergyMap — U.S. energy infrastructure desktop atlas

A **read-only Python/Tkinter map viewer** for EIA-sourced and curated U.S. ≥1 GW energy infrastructure records. No browser, JavaScript, map-tile server, Plotly runtime, or internet connection is required to view the included datasets once installed.

## Download EnergyMap for Windows (.exe)

**[Download EnergyMap-Windows.exe — latest successful Windows desktop release](https://github.com/1freetech/EnergyMap/releases/download/desktop-latest/EnergyMap-Windows.exe)**

[Windows release page and SHA-256 checksum](https://github.com/1freetech/EnergyMap/releases/tag/desktop-latest) · [Windows build history](https://github.com/1freetech/EnergyMap/actions/workflows/python-desktop.yml)

The Windows executable is packaged with the current research datasets and real geographic basemaps. **Python is not required** to run it. Download the `.exe` and double-click it; the first launch may take a moment because it is a single-file packaged application. Only download a release from this official repository. The app is not code-signed, so Windows SmartScreen may show an unrecognized-publisher warning.

A GitHub Actions publishing job refreshes the stable release above **only after the Windows, Linux and macOS build/test jobs succeed on `main`**. The release includes a `SHA256SUMS.txt` checksum. If the release has not been published yet, use the latest successful Windows artifact from the build-history page.

## Start EnergyMap from Python source

Download the [complete repository ZIP](https://github.com/1freetech/EnergyMap/archive/refs/heads/main.zip) and extract it, retaining the `data/`, `assets/` and `desktop/` folders. Run with Python 3.12+ and Tkinter:

```sh
python desktop/energymap.py
```

The desktop entry script now includes its own map renderer; opening `energymap.py` by itself no longer raises `ModuleNotFoundError: atlas_view`. **Extract the whole ZIP for the simplest offline setup.** If you run only the `.py` script, it still needs the research and basemap data; its first-run recovery prompt can download and validate the public repository ZIP with your permission or use a complete local ZIP/folder. For macOS and Linux, download the latest successful build artifacts from the [desktop workflow](https://github.com/1freetech/EnergyMap/actions/workflows/python-desktop.yml). The automated native build bundles both `data/` and `assets/`. Actual Windows/macOS screen acceptance must be checked on those platforms; GitHub CI alone is not a full usability certification.

If the original JSON data is unavailable, EnergyMap can prompt for an explicit one-time public repository download or let you select a local complete repository ZIP/folder. It validates the eight research datasets and both map outlines. Downloaded data remains in `~/.energymap/EnergyMap-data.zip` for offline use. Saved custom site files from older versions are left untouched, but the editing interface is retired.

## Verified historical ≥1 GW atlas expansion

The **Power plants** view includes **303 unique geocoded records**: 23 pre-existing curated plants plus 280 additional power stations. The separate **EIA ≥1 GW (2024)** view has **302** sourced plants across seven JSON files; **22** overlap curated plants and are suppressed *only in the combined view*. Existing state and national ranking datasets remain unchanged.

Every new EIA record carries a plant ID, reported location, ≥1,000 MW of **December 2024 operable nameplate capacity**, positive **calendar-2024 net generation (MWh)**, and direct EIA source references. **These are historical 2024 site and capacity records, not confirmation of current 2026 operation.** The sources, admission rules and reconciliation are explained in [EIA provenance](data/EIA-2024-PROVENANCE.md). Keep 2024 annual history separate from EIA's final 2025 and preliminary 2026 updates.

## Unified catalog, categories and sorting

**All sites** now displays **459 unique records** across two incomparable but clearly labeled classes:
- **303 power generating facilities**: 23 manually curated facilities plus 280 additional EIA 2024 historical plants (22 overlaps removed).
- **156 data-center / energy-campus project profiles**, reconciled from 156 state-ranking records and ten overlapping national Top 10 articles. All 10 national entries occur in the state profiles, so they are *not* 10 extra physical sites.

The **All ≥1 GW** filter covers **373** unique records, including **70** of the 156 data-center / energy-campus profiles. The other 86 are smaller projects or have no numerical MW and remain accessible through All sites and Data centers. **State rankings now includes all 459 canonical sites, grouped and ranked within their own state**, including generating stations and campus proposals. **National top 25** is a newly computed capacity-ordered list of 25 data-center / energy-campus projects from the 156 canonical profiles; it does not invent 15 new published national editorial positions. Original national Top 10 identities and publication ranks remain in record details.

All views start with **numeric capacity (MW) descending**, with missing values last. Click the **Capacity MW** column heading to reverse the sort; clicking **Name, State, Category or Rank** sorts accordingly. In State rankings, the **State #** column shows calculated ranks for every facility within its own state; ties in reported MW share a rank and missing MW is unranked. Select a state from the dropdown to display its complete catalog, including facilities under 1 GW. In National top 25, **Top 25 #** is a calculated ranking among campus profiles. A reported 2,000 MW tie at the cutoff is broken deterministically by project name to keep exactly 25 rows. State/category/search filters remain available. The map plots **116 sourced approximate city/locality reference dots** for campus profiles without claiming exact site coordinates. The **40 remaining unlocated projects** stay in every applicable table and are counted in the map caption **without a symbol on the map**. Recorded plant coordinates remain filled teal dots; approximate locality references are hollow orange dots. There are **no purple squares or aggregate markers**.

**Published project-scale MW is not a uniform measure:** EIA generator nameplate, data-center IT load, power requests, proposed onsite generation and full-build campus aspirations are not directly interchangeable. Raw ranking snapshots are preserved, and the details panel shows source-specific MW values and dates. Specific reconciliation:
- **E2B4 Roswell Information Park:** the developer distinguishes **6,500 MW proposed onsite generation** and **4,960 MW proposed IT load**. Both original editorial measurements are shown, with the 6.5 GW generation figure used in the national-ranking representation. [Developer investor page](https://e2b4.com/investors/).
- **Homer City Energy Campus:** the developer's current project description identifies **4,400 MW proposed gas generation**, whereas an earlier state editorial source used **4,500 MW**. The current figure is used in the unified catalog, with both source observations retained. [Official project overview](https://www.homercityredevelopment.com/project-overview).

The source JSON records are **not rewritten** to conceal disagreements. Unified identities and source notes are constructed in memory; see [catalog organization](data/CATALOG-ORGANIZATION.md).

## What is new

- A real U.S. basemap with state outlines, a selected-state highlight, and Alaska/Hawaii geographic insets.
- A native **orthographic spinning globe** with real country boundaries, a **Spin globe / Stop spinning** control, and mouse-drag rotation. Like a Plotly orthographic projection, only hemisphere-facing points are visible.
- Every dataset/category refreshes the map from the same filtered records: **teal filled circles** mark recorded plant locations, **hollow orange circles** show approximate sourced town references for campus projects, and projects without usable coordinates stay unplotted and counted in the map caption. **Only circular dots are plotted.** Click a dot to select its corresponding list entry.
- Resizable panes and controls; concise table columns with a horizontal fallback scrollbar; full record names, notes, measurements and URLs in a vertically scrollable, word-wrapped details panel.
- Nine read-only catalog views, including all 459 sites in the state rankings and a newly computed national Top 25 of campus projects. The original published Top 10 source ranks remain independently available in the details. Search, state filters, local reload and original source links remain available.
- Editing, personal-map creation, record import/export and deletion buttons are removed. The focus is reading established datasets rather than modifying them.

## What the records mean

The original source JSON records remain unchanged: `data/states-01.json` to `data/states-07-national.json` plus `data/operating-1gw.json`. The archived editorial source includes 50 state lists and ten published national projects; the application calculates expanded State rankings and National top 25 views without rewriting those articles. The generating plant layer is a curated/historical selection, not a verified complete inventory of 2026 plants.

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
