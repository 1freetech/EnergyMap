# EnergyMap Python desktop app

The new `desktop/energymap.py` is an **offline Tkinter application**, modeled after the Python approach in `1freetech/Lexicon`. The original browser application remains available as a separate interface.

## Download and run the Python source

1. On GitHub, use **Code → Download ZIP** for this branch and extract the complete repository. Do not download only the Python file: it needs the unchanged `data/` JSON folder.
2. Install Python 3.12 or newer with Tkinter.
3. From the repository root, run `python desktop/energymap.py`.

All eight datasets are loaded locally; no map tiles or cloud accounts are required. You can inspect verified operating plants, state project rankings, national Top 10, details and source URLs, plot locations with supplied continental-US coordinates, and create/edit/delete/import/export your own sites. Personal entries are stored at `~/.energymap/my-sites.json`; import/export uses JSON files. Empty coordinates remain unmapped; the coordinate plot is **not** a state-outline basemap. Alaska, Hawaii and other outside-viewport sites still appear in the list.

**Data integrity:** Existing operating-plant generation capacity, planned data-center MW, and measured energy MWh are distinct measures. The app does not calculate energy output from capacity or invent missing coordinates. Dataset changes must be verified independently against original sources.

## Download a packaged application

The `.github/workflows/python-desktop.yml` workflow builds PyInstaller binaries on Windows, macOS and Linux. After a successful run, open **Actions → Python desktop build → latest successful run → Artifacts**, and download the artifact matching your OS. Artifacts are ZIPs containing an executable with bundled JSON data. Windows users open `EnergyMap.exe`, while macOS/Linux users launch the platform build. macOS Gatekeeper and unsigned executables may require additional local approval; Linux binaries may require compatible system libraries. No production release is claimed until artifacts have passed actual end-to-end GUI testing.

## Development checks

```shell
python -m unittest discover -s desktop -p "test_*.py" -v
```

Automated tests validate local data loading, 50 states, national ranking order, and custom record validation. Full cross-platform clicking, file-dialog and packaged-app smoke tests are separate acceptance gates.
