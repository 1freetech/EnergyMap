# EnergyMap — Tkinter Desktop Atlas

Run `python desktop/energymap.py` from the **fully extracted** repository directory (Python 3.12+ / Tkinter).
Keep `data/*.json` and `assets/*.geojson` in their repository folders. The native atlas renderer is included directly in the canonical `energymap.py`; the old redundant `atlas_view.py` module has been retired. A single-file import no longer raises `ModuleNotFoundError`. The standalone script can request a one-time official data ZIP download or a local complete folder/ZIP, but fully extracting the repository first is recommended.
An executable built by the [Python desktop workflow](https://github.com/1freetech/EnergyMap/actions/workflows/python-desktop.yml) bundles all geography and research data.

## New EIA-sourced operating history

**303** unique generating facilities appear in **Power plants**: the 23 existing curated plants and **280** additional historical EIA facilities. **EIA ≥1 GW (2024)** shows all 302 EIA source records, including 22 that overlap curated entries (deduplicated in the combined map). Admission requires ≥1,000 MW of **December 2024 operable nameplate capacity**, valid EIA-sourced coordinates and positive calendar-2024 net generation. **Data are historical; 2026 operations require a new check.** See [source provenance](../data/EIA-2024-PROVENANCE.md).

## Unified category views

The new master **All sites** list includes **459 distinct facilities/projects** (303 generating facilities plus 156 data-center/energy-campus profiles). **All ≥1 GW** contains **373** matching source records: 303 generating facilities plus 70 campus profiles. The original 10 national projects overlap 10 state projects, so each has **one canonical identity**, and its state and national snapshots remain available in the record's details.

Choose a dataset using **Dataset**, restrict by **State** or **Category**, and search names, states, status or evidence. Every view initially sorts **Capacity MW highest to lowest**. Click Project/plant, State, Category, or Capacity MW to sort; clicking the same heading reverses direction. The compact **Row #** column numbers the currently visible list, without implying a MW ranking. In **State rankings** and **National top 25**, the column instead shows the calculated **State #** or **Top 25 #**, and the numerical heading sorts by the calculated rank. Sites with unknown MW are marked **N/R** in ranking views. Missing numerical capacities appear last, not as zero. Switching datasets clears a previously selected state/category filter to avoid hidden entries.

Capacities are intentionally separated by scope in details: historic power plant nameplate MW, verified curated generating capacity and editorial future-campus demand/supply claims are **not directly comparable**. For Roswell Information Park the 6,500 MW planned net onsite generation figure differs from 4,960 MW planned IT load. For Homer City 4,400 MW is the updated planned generating figure, while the earlier state story reported 4,500 MW. Campus markers now use 116 public geographic town references from the source descriptions; these are approximate **municipality reference points, not surveyed site coordinates**. Forty remaining campus profiles remain in the table but are **not plotted**, avoiding invented site coordinates and visually distracting aggregates. See [catalog methodology](../data/CATALOG-ORGANIZATION.md).

## Expanded rankings

**State rankings** now contains **all 459 unique sites**, including 303 power plants and 156 data-center/energy-campus projects. Select any state to view all of its sites sorted by reported MW, including entries below 1 GW and projects without numerical capacity. The **State #** column is recalculated within each state from the canonical source list. Equal MW receives equal competition rank (1, 1, 3); missing MW remains listed but unranked.

**National top 25** expands the original data-center/energy-campus national list by calculating the 25 largest reported-MW projects from the complete, deduplicated 156-campus catalog. It is **not a newly published editorial Top 25**; the original published national Top 10 rank stays in each record's details, separate from the newly computed Top 25 position. When the 25th cutoff falls on a reported MW tie, alphabetical site name is used only to select exactly 25 rows.

The project-level figures mix proposed IT load, onsite generation, power requests, and full-campus visions; they are not directly comparable to existing generator nameplate capacities. Unlocated campus profiles remain in lists without invented pins.

## Read-only catalog

The desktop interface intentionally omits Add site, Edit, Delete, Import, Export and My map. It shows the combined ≥1 GW map, the 2024 EIA historical catalog, the existing operating plants, the complete per-state rankings, and the calculated national Top 25 campus projects, with search, source links, and measured-vs-rated capacity distinctions. Former personal JSON site files remain unchanged under `~/.energymap/`.

## Maps

Select **United States** for real state boundaries, Alaska/Hawaii inset maps, and current dataset points. Select **World globe** for the orthographic global projection; use **Spin globe** to rotate continuously, **Stop spinning** to pause, or drag the map horizontally. The global boundary layer uses Natural Earth 1:110m public-domain geographic outlines; state outlines are adapted from PublicaMundi MappingAPI. Both are bundled for offline operation.

For every dataset, category and state filter, teal filled points show plant locations and hollow orange points show approximate campus reference towns. Forty campus profiles without usable locality coordinates remain in the table and are counted in the map caption, not displayed as squares or fabricated dots. All location markers are circular; clicking one selects its corresponding table record. Details use a resizable, word-wrapped, scrolling pane. The project table automatically fits its columns inside the available left pane; its horizontal scrollbar is removed. Resizing the window or pane redistributes column widths, with extra room going to project names. The bottom-left footer carries the neon-green **BitcoinVersus.tech** tag on a black background.

## Local recovery and tests

If the eight original data JSON files or the two geographic asset files are missing, choose the complete repository ZIP, select an extracted checkout, or allow an explicit one-time public GitHub download. Changes to the vetted source data are not introduced by any recovery step.

```sh
python -m unittest discover -s desktop -p 'test_*.py' -v
python -m unittest discover -s tests -p 'test_*.py' -v
python desktop/energymap.py --check-data
```

The native build workflow includes `--add-data "data:data"` and `--add-data "assets:assets"` and smoke-tests packaged startup. Windows and macOS still require real-device acceptance testing.
