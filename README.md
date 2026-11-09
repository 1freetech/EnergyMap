# EnergyMap — Python-only U.S. energy infrastructure atlas

EnergyMap is an offline **Python 3.12+ / Tkinter desktop application** for inspecting vetted U.S. power-station and data-center project records. The application and its tests are written in Python, not JavaScript. It does **not** require a browser, HTML, CSS, Node.js, a web server, or Leaflet tiles. JSON source records remain as data files.

## Run

Download/clone the complete repository, including `data/`, then run:

```sh
python desktop/energymap.py
```

Tkinter must be available in your Python installation. Install-free Windows, macOS and Linux builds are available under the latest **successful** [Python desktop build](https://github.com/1freetech/EnergyMap/actions/workflows/python-desktop.yml) → Artifacts. Builds are unsigned and have not all passed real-device acceptance testing.

## What the Python desktop application includes

- Separate views for vetted operating power plants **rated at least 1 GW**, historic state rankings, national Top 10 data-center projects, and the personal map.
- **50 state ranking lists**, including Texas Top 7 and Virginia Top 5, plus **10** separately ranked national projects in the preserved JSON corpus.
- Search by name/state/energy type/description, ranking and capacity metadata, date/source details, and approximate coordinate point plotting (not a full U.S. polygon basemap).
- User-created site records: add, edit, delete, import and export JSON. Saved locally in `~/.energymap/my-sites.json`. Reloading public data does not delete personal records.
- **Refresh data** reloads vetted JSON files from local disk. To see updated editorial records, download an updated repository/app first.
- Source URLs open in the system browser when available.

## Preserved research assets

`data/states-01.json` through `data/states-07-national.json` preserve the historical national/state development rankings. `data/operating-1gw.json` retains the separate operating-plant layer. Changes to published ranking positions or capacity figures must be sourced and reviewed, not silently guessed. Custom pins are private to the local installation; the program does not submit them for publication.

**Measurement boundaries:** MW expresses instantaneous power or rated capacity; MWh measures energy over a stated time interval. Planned data-center capacity is not operating consumption, and a generator's nameplate MW is not its measured output. Operating, planned, and suspended development records must remain distinct. Geographic dots represent approximate recorded coordinates, not parcel-accurate locations or state-outline map geometry. The operating layer is curated, **not a complete inventory** of all U.S. 1 GW plants.

## Code and quality checks

- `desktop/energymap.py`: Python GUI, data parsing, local map, personal-site editing.
- `desktop/test_energymap.py`, `desktop/gui_smoke.py`: model and Tkinter smoke tests.
- `tests/test_data_integrity.py`: Python source and dataset integrity checks.
- `.github/workflows/`: Python-only CI and cross-platform PyInstaller packaging.

```sh
python -m unittest discover -s desktop -p "test_*.py" -v
python -m unittest discover -s tests -p "test_*.py" -v
```

The prior JavaScript/HTML/Leaflet interface was retired in the Python-only conversion; original work remains in Git history. There is no automatic WordPress-to-JSON sync. Detailed scientific and reporting source URLs remain on individual data records.

Original migration context: [BitcoinVersus.Tech map PR #2](https://github.com/1freetech/Bitcoinversus.tech/pull/2).
