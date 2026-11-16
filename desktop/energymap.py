"""EnergyMap Python desktop edition. Read-only atlas for vetted source records.

The reviewed repository datasets are bundled unchanged. Capacity (MW) is not
energy generation (MWh); proposed data-center loads are not operating plants.
"""
from __future__ import annotations

import json
import math
import sys
import urllib.request
import zipfile
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from atlas_view import AtlasMap, rings_from_features
from uuid import uuid4

DATA_FILES = [f"data/states-{i:02d}.json" for i in range(1, 7)]
DATA_FILES.append("data/states-07-national.json")
OPERATING = "data/operating-1gw.json"
VIEWS = ("Operating plants", "State rankings", "National top 10")
FIELDS = ("name", "state", "energyType", "status", "lat", "lon",
          "capacityMW", "capacityBasis", "productionMW", "energyMWh",
          "energyPeriod", "article", "brief")


# EnergyMap works from a complete checkout, a standalone EXE, an adjacent
# data/ folder, or a complete GitHub repository ZIP. No working-directory guess
# is used until the complete eight-file dataset has been verified.
DATA_PATHS = (*DATA_FILES, OPERATING)
DATA_ZIP_URL = "https://github.com/1freetech/EnergyMap/archive/refs/heads/main.zip"
MAX_DATA_ZIP_BYTES = 12 * 1024 * 1024
MAX_JSON_BYTES = 5 * 1024 * 1024


def _data_store():
    return Path.home() / ".energymap"


def _candidate_sources():
    """Yield likely complete dataset locations, in precedence order."""
    if getattr(sys, "_MEIPASS", None):
        yield Path(sys._MEIPASS)
    script = Path(__file__).resolve()
    yield script.parent.parent              # normal desktop/energymap.py
    yield script.parent                     # copied energymap.py + data/
    yield Path(sys.executable).resolve().parent  # adjacent to native executable
    selected = _data_store() / "data-source.txt"
    if selected.is_file():
        try:
            yield Path(selected.read_text(encoding="utf-8").strip())
        except OSError:
            pass
    yield _data_store() / "EnergyMap-data.zip"  # first-launch download
    yield Path.cwd()                      # running from a complete checkout


def _zip_entries(archive):
    """Map all eight expected files without extracting any ZIP entries."""
    names = set(archive.namelist())
    suffix = DATA_FILES[0]
    prefixes = sorted({name[:-len(suffix)] for name in names
                       if name.endswith("/" + suffix) or name == suffix})
    for prefix in prefixes:
        if all(prefix + relative in names for relative in DATA_PATHS):
            return {relative: prefix + relative for relative in DATA_PATHS}
    raise FileNotFoundError("ZIP must contain all eight data/*.json files from EnergyMap.")


def _load_source(source):
    if source.is_file() and source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as archive:
            entries = _zip_entries(archive)
            def read(relative):
                info = archive.getinfo(entries[relative])
                if info.file_size > MAX_JSON_BYTES:
                    raise ValueError(f"Data file too large: {relative}")
                return json.loads(archive.read(info).decode("utf-8-sig"))
            return _records_from_reader(read)
    base = source.parent if source.name.lower() == "data" else source
    if not all((base / relative).is_file() for relative in DATA_PATHS):
        raise FileNotFoundError(f"Missing EnergyMap JSON files under {base / 'data'}")
    def read(relative):
        path = base / relative
        if path.stat().st_size > MAX_JSON_BYTES:
            raise ValueError(f"Data file too large: {relative}")
        return json.loads(path.read_text(encoding="utf-8-sig"))
    return _records_from_reader(read)


def _records_from_reader(read):
    rankings = []
    for relative in DATA_FILES:
        value = read(relative)
        if not isinstance(value, list):
            raise ValueError(f"{relative} must contain a JSON array")
        rankings.extend(value)
    operating = read(OPERATING)
    if not isinstance(operating, list):
        raise ValueError(f"{OPERATING} must contain a JSON array")
    return rankings, operating


def load_data(source=None):
    """Only accept a complete local dataset; never fabricate missing records."""
    if source is not None:
        return _load_source(Path(source).expanduser())
    seen = set()
    for candidate in _candidate_sources():
        candidate = candidate.expanduser()
        if candidate in seen:
            continue
        seen.add(candidate)
        if ((candidate.is_file() and candidate.suffix.lower() == ".zip")
                or candidate.is_dir()):
            try:
                return _load_source(candidate)
            except FileNotFoundError:
                continue  # partial/copy-only folders are not authoritative
    raise FileNotFoundError(
        "The eight EnergyMap data/*.json files are missing from this installation. "
        "Choose a complete EnergyMap repository folder/ZIP or download the data once."
    )


def download_repo_data():
    """Download the public GitHub ZIP only after explicit user consent."""
    store = _data_store()
    store.mkdir(parents=True, exist_ok=True)
    final = store / "EnergyMap-data.zip"
    pending = store / "EnergyMap-data.zip.tmp"
    try:
        req = urllib.request.Request(DATA_ZIP_URL, headers={"User-Agent": "EnergyMap-Desktop"})
        with urllib.request.urlopen(req, timeout=30) as response, pending.open("wb") as out:
            size = 0
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_DATA_ZIP_BYTES:
                    raise ValueError("Download exceeded 12 MB; stopped for safety")
                out.write(chunk)
        with zipfile.ZipFile(pending) as archive:
            entries = _zip_entries(archive)
            def read(relative):
                info = archive.getinfo(entries[relative])
                if info.file_size > MAX_JSON_BYTES:
                    raise ValueError(f"Data file too large: {relative}")
                return json.loads(archive.read(info).decode("utf-8-sig"))
            _records_from_reader(read)
        load_geo_data(pending)
    except Exception:
        pending.unlink(missing_ok=True)
        raise
    pending.replace(final)
    return final


def recover_data(error):
    """Guide standalone .py users to an existing dataset or a one-time download."""
    root = tk.Tk()
    root.withdraw()
    try:
        answer = messagebox.askyesnocancel(
            "EnergyMap data missing",
            f"{error}\n\nYES — download the public EnergyMap repository data "
            "from GitHub (requires internet; saved for offline use).\n\n"
            "NO — choose a complete extracted repository folder or ZIP on this PC.\n\n"
            "CANCEL — exit without changing files.", parent=root)
        if answer is None:
            return False
        if answer:
            try:
                source = download_repo_data()
                load_data(source)
                load_geo_data(source)
                return True
            except (OSError, ValueError, zipfile.BadZipFile, UnicodeError) as exc:
                messagebox.showerror("Download unsuccessful", str(exc), parent=root)
                return False
        choose_zip = messagebox.askyesno("Select data source",
                                        "Is your complete repository saved as a ZIP file?\n"
                                        "YES — select ZIP. NO — select the repository or data folder.", parent=root)
        if choose_zip:
            chosen = filedialog.askopenfilename(parent=root, title="Select EnergyMap repository ZIP",
                                                filetypes=[("ZIP files", "*.zip")])
        else:
            chosen = filedialog.askdirectory(parent=root, title="Select EnergyMap folder containing data")
        if not chosen:
            return False
        try:
            load_data(chosen)
            load_geo_data(chosen)
            _data_store().mkdir(parents=True, exist_ok=True)
            (_data_store() / "data-source.txt").write_text(chosen, encoding="utf-8")
            return True
        except (OSError, ValueError, zipfile.BadZipFile, UnicodeError) as exc:
            messagebox.showerror("Invalid data source", str(exc), parent=root)
            return False
    finally:
        root.destroy()



GEO_FILES = ("assets/us_states.geojson", "assets/world_countries.geojson")


def load_geo_data(source=None):
    """Read bundled real boundary coordinates; never invent a substitute basemap."""
    sources = [Path(source).expanduser()] if source is not None else list(_candidate_sources())
    for candidate in sources:
        candidate = Path(candidate).expanduser()
        if candidate.is_dir():
            root = candidate.parent if candidate.name.lower() == "assets" else candidate
            if all((root / x).is_file() for x in GEO_FILES):
                return tuple(json.loads((root / x).read_text(encoding="utf-8-sig"))
                             for x in GEO_FILES)
        elif candidate.is_file() and (candidate.suffix.lower() == ".zip" or zipfile.is_zipfile(candidate)):
            try:
                with zipfile.ZipFile(candidate) as archive:
                    names = set(archive.namelist())
                    first = GEO_FILES[0]
                    prefixes = [key[:-len(first)] for key in names if key.endswith(first)]
                    for prefix in prefixes:
                        if all(prefix + x in names for x in GEO_FILES):
                            return tuple(json.loads(archive.read(prefix + x).decode("utf-8-sig"))
                                         for x in GEO_FILES)
            except zipfile.BadZipFile:
                pass
    raise FileNotFoundError(
        "Geographic basemap files are missing. Download the new complete EnergyMap "
        "repository ZIP with its assets/ folder or choose a complete extracted checkout."
    )


def user_path():
    return Path.home() / ".energymap" / "my-sites.json"


def number(value):
    if value in ("", None):
        return None
    n = float(value)
    if not math.isfinite(n):
        raise ValueError("Numeric values must be finite.")
    return n


def validate_site(entry):
    if not isinstance(entry, dict):
        raise ValueError("Each site must be an object.")
    result = {key: str(entry.get(key) or "").strip() for key in FIELDS
              if key not in ("lat", "lon", "capacityMW", "productionMW", "energyMWh")}
    if not result["name"] or not result["state"]:
        raise ValueError("Site name and state are required.")
    for key in ("lat", "lon", "capacityMW", "productionMW", "energyMWh"):
        result[key] = number(entry.get(key))
    if (result["lat"] is None) != (result["lon"] is None):
        raise ValueError("Provide both latitude and longitude, or neither.")
    if result["lat"] is not None and not -90 <= result["lat"] <= 90:
        raise ValueError("Latitude must be between -90 and 90.")
    if result["lon"] is not None and not -180 <= result["lon"] <= 180:
        raise ValueError("Longitude must be between -180 and 180.")
    if result["energyMWh"] is not None and not result["energyPeriod"]:
        raise ValueError("Reported MWh requires a measurement period.")
    result["id"] = str(entry.get("id") or "personal-" + uuid4().hex)
    return result


def state_records(rankings, state):
    return sorted((r for r in rankings if r.get("state") == state
                   and isinstance(r.get("rank"), (int, float))),
                  key=lambda x: (x["rank"], x.get("name", "")))


def national_records(rankings):
    return sorted((r for r in rankings if isinstance(r.get("nationalRank"), (int, float))),
                  key=lambda x: (x["nationalRank"], x.get("name", "")))[:10]


class EnergyMapApp(tk.Tk):
    """Resizable, read-only desktop atlas preserving the existing vetted datasets."""

    def __init__(self):
        super().__init__()
        self.title("EnergyMap — Desktop Atlas")
        screen_w, screen_h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{min(1460, max(960, screen_w-70))}x{min(860, max(590, screen_h-100))}")
        self.minsize(min(960, screen_w), min(590, screen_h))
        self.rankings, self.operating = load_data()
        states_geo, world_geo = load_geo_data()
        self.visible = {}
        self.view = tk.StringVar(value=VIEWS[0])
        states = sorted({r.get("state", "") for r in self.rankings if r.get("state")})
        self.state = tk.StringVar(value=states[0] if states else "")
        self.search = tk.StringVar()
        self.status = tk.StringVar()

        shell = ttk.Frame(self, padding=(12, 10, 12, 8))
        shell.pack(fill="both", expand=True)
        ttk.Label(shell, text="EnergyMap  /  U.S. ENERGY INFRASTRUCTURE ATLAS",
                  font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(0, 2))
        ttk.Label(shell, text="Browse verified power plants, state rankings and national projects — read-only source data",
                  font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 10))
        controls = ttk.Frame(shell)
        controls.pack(fill="x", pady=(0, 9))
        first = ttk.Frame(controls)
        first.pack(fill="x")
        ttk.Label(first, text="Dataset").pack(side="left")
        cb = ttk.Combobox(first, textvariable=self.view, values=VIEWS,
                          state="readonly", width=19)
        cb.pack(side="left", padx=(6, 14))
        cb.bind("<<ComboboxSelected>>", lambda _ev: self._change_view())
        ttk.Label(first, text="State").pack(side="left")
        self.state_combo = ttk.Combobox(first, textvariable=self.state, values=states,
                                        state="disabled", width=17)
        self.state_combo.pack(side="left", padx=(6, 14))
        self.state_combo.bind("<<ComboboxSelected>>", lambda _ev: self.refresh())
        ttk.Label(first, text="Search").pack(side="left")
        ttk.Entry(first, textvariable=self.search, width=26).pack(side="left", padx=(6, 6), fill="x", expand=True)
        ttk.Button(first, text="Clear", command=lambda: self.search.set(""), width=6).pack(side="left")
        second = ttk.Frame(controls)
        second.pack(fill="x", pady=(6, 0))
        ttk.Button(second, text="Reload local data", command=self.reload_from_disk).pack(side="left")
        ttk.Button(second, text="Open source article", command=self.open_source).pack(side="left", padx=(8, 0))
        ttk.Label(second, text="Records are read-only  •  MW = capacity, not MWh generated",
                  font=("Segoe UI", 9)).pack(side="right")
        self.search.trace_add("write", lambda *_: self.refresh())

        self.pane = ttk.Panedwindow(shell, orient="horizontal")
        self.pane.pack(fill="both", expand=True)
        left = ttk.Frame(self.pane, padding=2)
        self.pane.add(left, weight=5)
        right = ttk.Panedwindow(self.pane, orient="vertical")
        self.pane.add(right, weight=6)

        ttk.Label(left, text="PROJECTS & OPERATING PLANTS",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(2, 8))
        table_frame = ttk.Frame(left)
        table_frame.pack(fill="both", expand=True)
        self.cols = ("rank", "name", "state", "capacity")
        self.tree = ttk.Treeview(table_frame, columns=self.cols, show="headings", selectmode="browse")
        for key, title, width, anchor in (
            ("rank", "Rank", 45, "center"),
            ("name", "Project / plant", 295, "w"),
            ("state", "State", 102, "w"),
            ("capacity", "MW", 95, "e"),
        ):
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, minwidth=width, anchor=anchor,
                             stretch=(key == "name"))
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        self.tree.tag_configure("even", background="#f1f6fa")
        self.tree.tag_configure("odd", background="#ffffff")
        self.tree.bind("<<TreeviewSelect>>", lambda _ev: self.on_select())
        self.tree.bind("<Double-1>", lambda _ev: self.open_source())

        map_frame = ttk.Frame(right, padding=(4, 2, 4, 4))
        right.add(map_frame, weight=5)
        self.atlas = AtlasMap(map_frame, states_geo, world_geo, self.select_from_map)
        self.atlas.pack(fill="both", expand=True)
        details = ttk.Frame(right, padding=(5, 5, 5, 1))
        right.add(details, weight=3)
        ttk.Label(details, text="SELECTED RECORD  /  SOURCE & MEASUREMENTS",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))
        detail_body = ttk.Frame(details)
        detail_body.pack(fill="both", expand=True)
        self.info = tk.Text(detail_body, wrap="word", bg="#f9fcfe", relief="flat",
                            font=("Segoe UI", 10), padx=13, pady=10, undo=False)
        scroll = ttk.Scrollbar(detail_body, orient="vertical", command=self.info.yview)
        self.info.configure(yscrollcommand=scroll.set)
        self.info.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        detail_body.grid_rowconfigure(0, weight=1)
        detail_body.grid_columnconfigure(0, weight=1)
        self.info.tag_configure("heading", font=("Segoe UI", 12, "bold"), spacing3=8)
        self.info.tag_configure("field", font=("Segoe UI", 9, "bold"), foreground="#365b69")
        self.info.configure(state="disabled")
        self.status_label = ttk.Label(shell, textvariable=self.status, anchor="w")
        self.status_label.pack(fill="x", pady=(8, 0))
        self.bind("<Configure>", self._resize_status)
        self.after_idle(self._initial_layout)
        self.refresh()

    def _initial_layout(self):
        try:
            self.pane.sashpos(0, max(495, int(self.pane.winfo_width() * .54)))
            self.atlas.draw()
        except tk.TclError:
            pass

    def _resize_status(self, event):
        if event.widget is self:
            self.status_label.configure(wraplength=max(500, event.width-30))

    def _change_view(self):
        self.state_combo.configure(state="readonly" if self.view.get() == "State rankings" else "disabled")
        self.refresh()

    def reload_from_disk(self):
        try:
            rankings, operating = load_data()
            states_geo, world_geo = load_geo_data()
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            messagebox.showerror("Reload failed", str(exc), parent=self)
            return
        self.rankings, self.operating = rankings, operating
        self.atlas.states = tuple(rings_from_features(states_geo))
        self.atlas.countries = tuple(rings_from_features(world_geo))
        states = sorted({r.get("state", "") for r in rankings if r.get("state")})
        self.state_combo["values"] = states
        if self.state.get() not in states:
            self.state.set(states[0] if states else "")
        self.refresh()

    def records(self):
        if self.view.get() == "Operating plants":
            items = self.operating
        elif self.view.get() == "State rankings":
            items = state_records(self.rankings, self.state.get())
        else:
            items = national_records(self.rankings)
        needle = self.search.get().strip().casefold()
        if needle:
            return [r for r in items if needle in " ".join(
                str(r.get(key, "")) for key in ("name", "state", "energyType", "brief", "status", "heading")
            ).casefold()]
        return items

    def refresh(self):
        prior = self.tree.selection()
        prior_record = self.visible.get(prior[0]) if prior else None
        prior_id = prior_record.get("id") if prior_record else None
        self.tree.delete(*self.tree.get_children())
        self.visible = {}
        selected = None
        for index, item in enumerate(self.records()):
            key = str(index)
            self.visible[key] = item
            if prior_id is not None and item.get("id") == prior_id:
                selected = key
            cap = item.get("capacityMW")
            try:
                label = f"{float(cap):,.0f}" if cap is not None and cap != "" else "Not stated"
            except (ValueError, TypeError):
                label = "Not stated"
            rank = item.get("nationalRank") if self.view.get() == "National top 10" else item.get("rank")
            self.tree.insert("", "end", iid=key, tags=("even" if index % 2 == 0 else "odd",),
                             values=(rank if rank is not None else "", item.get("name", ""),
                                     item.get("state", ""), label))
        if selected is None and self.visible:
            selected = "0"
        if selected is not None:
            self.tree.selection_set(selected)
        else:
            self._show_details(None)
        self.atlas.set_records(self.visible, selected,
                               self.state.get() if self.view.get() == "State rankings" else "")
        mapped = sum(1 for item in self.visible.values() if self.atlas._coordinates(item))
        self.status.set(f"{len(self.visible)} records displayed  |  {mapped} records with coordinates  |  "
                        "Published MW is rated/planned power; MWh requires a reporting period")

    def on_select(self):
        sel = self.tree.selection()
        key = sel[0] if sel else None
        self._show_details(self.visible.get(key))
        self.atlas.selected = key
        self.atlas.draw()

    def _show_details(self, item):
        self.info.configure(state="normal")
        self.info.delete("1.0", "end")
        if item:
            self.info.insert("end", str(item.get("name") or "Project") + "\n\n", "heading")
            pairs = (
                ("State", item.get("state")),
                ("Technology", item.get("energyType")),
                ("Project status", item.get("status")),
                ("Capacity (MW)", item.get("capacityLabel") or item.get("capacityMW")),
                ("Capacity basis", item.get("capacityBasis")),
                ("Measured power (MW)", item.get("productionMW")),
                ("Energy (MWh)", item.get("energyMWh")),
                ("Energy period", item.get("energyPeriod")),
                ("Last verified", item.get("verificationDate") or item.get("updated")),
                ("Source organization", item.get("sourceOrganization")),
                ("Location precision", item.get("locationPrecision")),
            )
            for label, value in pairs:
                self.info.insert("end", label + ":  ", "field")
                self.info.insert("end", f"{value if value is not None and value != '' else 'Not reported'}\n")
            self.info.insert("end", "\nResearch notes\n", "field")
            self.info.insert("end", str(item.get("brief") or "No additional description") + "\n\n")
            self.info.insert("end", "Source:  ", "field")
            self.info.insert("end", str(item.get("article") or "Not reported"))
        self.info.configure(state="disabled")

    def select_from_map(self, key):
        if key in self.visible:
            self.tree.selection_set(key)
            self.tree.see(key)
            self.on_select()

    def open_source(self):
        sel = self.tree.selection()
        item = self.visible.get(sel[0]) if sel else None
        url = item.get("article") if item else None
        if isinstance(url, str) and url.startswith(("https://", "http://")):
            webbrowser.open(url)
        else:
            messagebox.showinfo("No source link", "No source URL is available for the selected record.", parent=self)


if __name__ == "__main__":
    if "--check-data" in sys.argv:
        # Validate what PyInstaller actually bundled, even for --windowed builds.
        try:
            load_data()
            load_geo_data()
        except (OSError, ValueError, zipfile.BadZipFile, UnicodeError) as exc:
            if sys.stderr is not None:
                print(f"EnergyMap data check failed: {exc}", file=sys.stderr)
            raise SystemExit(1)
        raise SystemExit(0)
    try:
        load_data()
        load_geo_data()
    except (OSError, ValueError, zipfile.BadZipFile, UnicodeError) as exc:
        if not recover_data(exc):
            raise SystemExit(1)
    try:
        EnergyMapApp().mainloop()
    except (OSError, ValueError, zipfile.BadZipFile, UnicodeError) as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("EnergyMap load failed", str(exc), parent=root)
        root.destroy()
        raise SystemExit(1)
