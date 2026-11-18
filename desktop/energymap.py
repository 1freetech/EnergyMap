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
from uuid import uuid4

# Native map renderer is included here so a single-script launch from a Windows ZIP
# preview cannot fail because desktop/atlas_view.py was not extracted.
MAP_MODES = ("United States", "World globe")


def rings_from_features(geojson):
    """Yield (name, ring) for polygon exteriors; coordinates remain lon, lat."""
    for feature in geojson.get("features", []):
        geometry = feature.get("geometry") or {}
        kind = geometry.get("type")
        if kind == "Polygon":
            polygons = [geometry.get("coordinates", [])]
        elif kind == "MultiPolygon":
            polygons = geometry.get("coordinates", [])
        else:
            continue
        for polygon in polygons:
            if polygon and len(polygon[0]) >= 3:
                yield feature.get("name", ""), polygon[0]


def project_orthographic(lon, lat, center_lon, center_lat=20.0):
    """Orthographic unit-disk coordinates and positive visible-hemisphere depth."""
    a, b = math.radians(lat), math.radians(center_lat)
    delta = math.radians((lon - center_lon + 180) % 360 - 180)
    ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
    return (ca * math.sin(delta), cb * sa - sb * ca * math.cos(delta),
            sb * sa + cb * ca * math.cos(delta))


def _horizon(a, b):
    """Interpolate a boundary crossing onto the orthographic circle."""
    t = a[2] / (a[2] - b[2])
    x = a[0] + t * (b[0] - a[0])
    y = a[1] + t * (b[1] - a[1])
    size = math.hypot(x, y)
    return (x / size, y / size) if size else (0.0, 1.0)


def clip_hemisphere(ring, center_lon, center_lat=20.0):
    """Clip geographic polygons at the visible hemisphere (z >= 0).

    Returns unit-disk x/y positions. Backside geographic points never appear.
    """
    if len(ring) < 3:
        return []
    vertices = [project_orthographic(lon, lat, center_lon, center_lat)
                for lon, lat in ring]
    clipped = []
    prev = vertices[-1]
    for curr in vertices:
        inside_prev, inside_curr = prev[2] >= 0, curr[2] >= 0
        if inside_curr:
            if not inside_prev:
                clipped.append(_horizon(prev, curr))
            clipped.append((curr[0], curr[1]))
        elif inside_prev:
            clipped.append(_horizon(prev, curr))
        prev = curr
    return clipped if len(clipped) >= 3 else []


class AtlasMap(ttk.Frame):
    """Data viewer map: real polygons, plot point selection, and rotating globe."""

    def __init__(self, parent, states, countries, on_select):
        super().__init__(parent)
        self.states = tuple(rings_from_features(states))
        self.countries = tuple(rings_from_features(countries))
        self.on_select = on_select
        self.visible = {}
        self.selected = None
        self.focus_state = ""
        self.point_hits = []
        self._locality_stack = {}
        self.globe_lon = -100.0
        self.spin_id = None
        self.drag_from = None
        self.drag_moved = False
        self.mode = tk.StringVar(value=MAP_MODES[0])
        self.note = tk.StringVar(value="Real boundaries • Approximate source coordinates")
        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(2, 5))
        ttk.Label(controls, text="GEOGRAPHIC ATLAS", font=("Segoe UI", 10, "bold")).pack(
            anchor="w", padx=2
        )
        # Keep the atlas tools on their own line so the right pane does not
        # demand 600+ pixels and squeeze the projects table out of view.
        toolbar = ttk.Frame(controls)
        toolbar.pack(fill="x", pady=(4, 0))
        self.map_combo = ttk.Combobox(toolbar, textvariable=self.mode, values=MAP_MODES,
                                      state="readonly", width=13)
        self.map_combo.pack(side="left", padx=(2, 4))
        self.map_combo.bind("<<ComboboxSelected>>", self.change_mode)
        self.spin_button = ttk.Button(toolbar, text="Spin globe", command=self.toggle_spin, width=11)
        self.spin_button.pack(side="left", padx=(0, 4))
        ttk.Button(toolbar, text="Reset", command=self.reset_map, width=6).pack(side="left")
        self.canvas = tk.Canvas(self, bg="#e5f1f5", highlightthickness=0, height=400)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_map_resize)
        self.canvas.bind("<ButtonPress-1>", self.mouse_down)
        self.canvas.bind("<B1-Motion>", self.mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.mouse_up)
        self.caption = ttk.Label(self, textvariable=self.note, padding=(3, 5), wraplength=270)
        self.caption.pack(fill="x")
        self._sync_spin_state()

    def _on_map_resize(self, event):
        self.caption.configure(wraplength=max(170, event.width - 12))
        self.draw()

    def _sync_spin_state(self):
        if self.mode.get() != "World globe":
            self.spin_button.configure(state="disabled", text="Spin globe")
        else:
            self.spin_button.configure(state="normal", text="Stop spinning" if self.spin_id else "Spin globe")

    def set_records(self, visible, selected=None, focus_state=""):
        self.visible = visible
        self.selected = selected
        self.focus_state = focus_state
        self.draw()

    def change_mode(self, _event=None):
        if self.mode.get() != "World globe":
            self.stop_spin()
        self._sync_spin_state()
        self.draw()

    def reset_map(self):
        self.stop_spin()
        self.globe_lon = -100.0
        self.draw()

    def toggle_spin(self):
        if self.spin_id is not None:
            self.stop_spin()
        elif self.mode.get() == "World globe":
            self.spin_id = self.after(100, self._spin)
            self._sync_spin_state()

    def _spin(self):
        self.spin_id = None
        if self.mode.get() != "World globe" or not self.winfo_exists():
            return
        self.globe_lon = (self.globe_lon + 5 + 180) % 360 - 180
        self.draw()
        self.spin_id = self.after(100, self._spin)

    def stop_spin(self):
        if self.spin_id is not None:
            self.after_cancel(self.spin_id)
            self.spin_id = None
        self._sync_spin_state()

    def destroy(self):
        self.stop_spin()
        super().destroy()

    def mouse_down(self, event):
        self.drag_from = (event.x, event.y)
        self.drag_moved = False

    def mouse_drag(self, event):
        if not self.drag_from or self.mode.get() != "World globe":
            return
        dx = event.x - self.drag_from[0]
        if abs(dx) > 2:
            self.drag_moved = True
            self.stop_spin()
            self.globe_lon = (self.globe_lon - dx * .55 + 180) % 360 - 180
            self.drag_from = (event.x, event.y)
            self.draw()

    def mouse_up(self, event):
        if not self.drag_moved and self.point_hits:
            nearest = min(self.point_hits, key=lambda item: (item[0]-event.x)**2 + (item[1]-event.y)**2)
            if (nearest[0]-event.x)**2 + (nearest[1]-event.y)**2 < 15**2:
                self.on_select(nearest[2])
        self.drag_from = None
        self.drag_moved = False

    @staticmethod
    def _position(lon, lat, bounds, screen):
        x0, y0, x1, y1 = screen
        l0, a0, l1, a1 = bounds
        return x0 + (lon - l0) / (l1 - l0) * (x1 - x0), y1 - (lat - a0) / (a1 - a0) * (y1 - y0)

    @staticmethod
    def _viewport(w, h):
        """Keep a predictable USA map aspect ratio when panes are resized."""
        margin = 24
        available_w = max(80, w - 2 * margin)
        available_h = max(80, h - 92)
        aspect = 1.85
        width = min(available_w, available_h * aspect)
        height = width / aspect
        x0 = (w - width) / 2
        y0 = max(12, (available_h - height) / 2 + 10)
        return (x0, y0, x0 + width, y0 + height)


    def draw(self):
        c = self.canvas
        c.delete("all")
        w = max(300, c.winfo_width())
        h = max(230, c.winfo_height())
        self.point_hits = []
        self._locality_stack = {}
        if self.mode.get() == "World globe":
            self._draw_globe(c, w, h)
        else:
            self._draw_united_states(c, w, h)
        locations = sum(1 for r in self.visible.values() if self._coordinates(r))
        approximate = sum(1 for r in self.visible.values()
                          if self._coordinates(r) and r.get("markerKind") == "locality")
        missing = len(self.visible) - locations
        self.note.set(
            f"{locations} location dots ({approximate} approximate town references)  •  "
            f"{missing} unlocated (list only; no invented dots)  •  "
            "All map site markers are circles"
        )

    def _draw_united_states(self, c, w, h):
        bounds = (-125.0, 24.0, -66.0, 50.0)
        screen = self._viewport(w, h)
        c.create_rectangle(0, 0, w, h, fill="#e7f1f6", outline="")
        for state, ring in self.states:
            if state in ("Alaska", "Hawaii"):
                continue
            coords = []
            for lon, lat in ring:
                if -127 <= lon <= -64 and 22 <= lat <= 52:
                    coords.extend(self._position(lon, lat, bounds, screen))
            if len(coords) >= 6:
                chosen = state == self.focus_state
                c.create_polygon(coords, fill="#c4dfd5" if not chosen else "#f5d788",
                                 outline="#7a9b9e" if not chosen else "#a27d30", width=1)
        # Alaska and Hawaii are real geographic polygons displayed as standard insets.
        inset_y = h - 69
        alaska_box = (max(18, screen[0]), inset_y, max(18, screen[0]) + 112, h - 10)
        hawaii_box = (alaska_box[2] + 10, inset_y, alaska_box[2] + 88, h - 10)
        for name, box, inset_bounds in (("Alaska", alaska_box, (-179, 50, -129, 72)),
                                       ("Hawaii", hawaii_box, (-161.5, 18, -154, 23))):
            c.create_rectangle(*box, fill="#daecf1", outline="#8eb5c1", width=1)
            for state, ring in self.states:
                if state != name:
                    continue
                pieces = []
                for lon, lat in ring:
                    if inset_bounds[0] <= lon <= inset_bounds[2] and inset_bounds[1] <= lat <= inset_bounds[3]:
                        pieces.extend(self._position(lon, lat, inset_bounds, box))
                if len(pieces) >= 6:
                    c.create_polygon(pieces, fill="#c4dfd5" if self.focus_state != name else "#f5d788",
                                     outline="#648d96")
            c.create_text(box[0] + 5, box[1] + 7, text=name[:2].upper(), anchor="w",
                          fill="#38596a", font=("Segoe UI", 8, "bold"))
        for key, row in self.visible.items():
            loc = self._coordinates(row)
            if loc is None:
                continue
            lon, lat = loc
            if bounds[0] <= lon <= bounds[2] and bounds[1] <= lat <= bounds[3]:
                x, y = self._position(lon, lat, bounds, screen)
            elif -179 <= lon <= -129 and 50 <= lat <= 72:
                x, y = self._position(lon, lat, (-179, 50, -129, 72), alaska_box)
            elif -161.5 <= lon <= -154 and 18 <= lat <= 23:
                x, y = self._position(lon, lat, (-161.5, 18, -154, 23), hawaii_box)
            else:
                continue
            self._pin(c, x, y, key)
        c.create_text(w - 10, h - 13, text="Source: PublicaMundi U.S. state outlines",
                      anchor="e", fill="#536c79", font=("Segoe UI", 8))

    @staticmethod
    def _coordinates(row):
        try:
            lon, lat = float(row["lon"]), float(row["lat"])
            if math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90:
                return lon, lat
        except (KeyError, TypeError, ValueError):
            pass
        return None

    def _pin(self, c, x, y, key):
        selected = key == self.selected
        approximate = self.visible[key].get("markerKind") == "locality"
        if approximate:
            # Spread collocated town-reference symbols only in screen pixels,
            # not by changing recorded lat/lon or promising exact site position.
            anchor = (round(x / 7), round(y / 7))
            occurrence = self._locality_stack.get(anchor, 0)
            self._locality_stack[anchor] = occurrence + 1
            if occurrence:
                theta = math.radians(occurrence * 137.5)
                radius = min(14, 7 + occurrence * 2)
                x += math.cos(theta) * radius
                y += math.sin(theta) * radius
        r = 6.5 if selected else 4.3
        fill = "#ffd166" if selected else "#fff6e8" if approximate else "#007e8e"
        outline = "#a45500" if approximate else "#103b52"
        c.create_oval(x-r, y-r, x+r, y+r, fill=fill, outline=outline,
                      width=2.1 if approximate or selected else 1)
        self.point_hits.append((x, y, key))

    def _draw_globe(self, c, w, h):
        c.create_rectangle(0, 0, w, h, fill="#081e33", outline="")
        radius = max(50, min((w - 55) / 2, (h - 38) / 2))
        cx, cy = w / 2, h / 2
        c.create_oval(cx-radius, cy-radius, cx+radius, cy+radius,
                      fill="#1c597a", outline="#79b6ce", width=2)
        def to_canvas(x, y):
            return cx + radius * x, cy - radius * y
        # Physical meridians and parallels, drawn only on the visible hemisphere.
        for lat in (-60, -30, 0, 30, 60):
            self._draw_grid_line(c, [(lon, lat) for lon in range(-180, 181, 3)], to_canvas)
        for lon in range(-180, 180, 30):
            self._draw_grid_line(c, [(lon, lat) for lat in range(-90, 91, 3)], to_canvas)
        for _name, ring in self.countries:
            points = clip_hemisphere(ring, self.globe_lon)
            if len(points) >= 3:
                coords = []
                for x, y in points:
                    coords.extend(to_canvas(x, y))
                c.create_polygon(coords, fill="#c0d7b1", outline="#7baba4", width=.7)
        # Redraw the globe edge to hide any boundary strokes outside the circle.
        c.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, outline="#a5d6e6", width=2)
        for key, row in self.visible.items():
            loc = self._coordinates(row)
            if loc is None:
                continue
            px, py, z = project_orthographic(loc[0], loc[1], self.globe_lon)
            if z >= 0:
                x, y = to_canvas(px, py)
                self._pin(c, x, y, key)
        c.create_text(10, 12, text=f"GLOBE • {self.globe_lon:+.0f}° longitude",
                      fill="#d9e9ef", anchor="w", font=("Segoe UI", 9, "bold"))
        c.create_text(w-10, h-13, text="Natural Earth 1:110m • public domain",
                      anchor="e", fill="#b7ced9", font=("Segoe UI", 8))

    def _draw_grid_line(self, c, geographic_points, to_canvas):
        part = []
        for lon, lat in geographic_points:
            x, y, z = project_orthographic(lon, lat, self.globe_lon)
            if z >= 0:
                part.extend(to_canvas(x, y))
            else:
                if len(part) >= 4:
                    c.create_line(part, fill="#2c7592", width=1)
                part = []
        if len(part) >= 4:
            c.create_line(part, fill="#2c7592", width=1)


DATA_FILES = [f"data/states-{i:02d}.json" for i in range(1, 7)]
DATA_FILES.append("data/states-07-national.json")
OPERATING = "data/operating-1gw.json"
VIEWS = ("All sites", "All ≥1 GW", "Power plants", "EIA plants (2024)", "Curated plants", "Data centers", "Data centers ≥1 GW", "State rankings", "National top 25")
CATEGORY_FILTERS = ("All categories", "Power generation", "Data centers / campuses")
ALL_STATES = "All states"
FIELDS = ("name", "state", "energyType", "status", "lat", "lon",
          "capacityMW", "capacityBasis", "productionMW", "energyMWh",
          "energyPeriod", "article", "brief")


# EnergyMap works from a complete checkout, a standalone EXE, an adjacent
# data/ folder, or a complete GitHub repository ZIP. No working-directory guess
# is used until the complete eight-file dataset has been verified.
DATA_PATHS = (*DATA_FILES, OPERATING)
EIA_PATHS = tuple(f"data/eia2024-1gw-{i:02d}.json" for i in range(1, 8))
PROJECT_LOCALITY_PATHS = tuple(f"data/project-localities-{i:02d}.json" for i in range(1, 8))
# EIA plant identities confirmed against the 23 curated existing records.
# Suppress duplicates ONLY in the combined view; keep sources separate.
CURATED_EIA_CODES = frozenset({
    "6163", "649", "6008", "46", "3399", "6145", "6152", "7722",
    "6146", "3082", "3921", "55480", "6051", "3895", "6180", "55091",
    "3407", "153", "371", "1379", "55097", "55215",
})
EIA_TECHNOLOGY = {
    "gas": "Natural gas", "coal": "Coal", "nuclear": "Nuclear",
    "hydro": "Hydroelectric", "wind": "Wind", "solar_utility": "Solar",
    "pumped_storage": "Pumped storage", "geothermal": "Geothermal",
    "biomass": "Biomass", "petroleum": "Petroleum", "other": "Other",
}
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
        load_eia_catalog(pending)
        load_project_localities(pending)
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
                load_eia_catalog(source)
                load_project_localities(source)
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
            load_eia_catalog(chosen)
            load_project_localities(chosen)
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



def _validate_eia_catalog(parts):
    """Defensive validation of sourced, geocoded, 1 GW+ historical facilities."""
    rows, seen = [], set()
    for part in parts:
        if not isinstance(part, list):
            raise ValueError("EIA catalog part must be a JSON array")
        for source in part:
            if not isinstance(source, dict):
                raise ValueError("EIA catalog entries must be objects")
            entry = dict(source)
            code = str(entry.get("eiaPlantCode", ""))
            mw = entry.get("capacityMW")
            lat, lon = entry.get("lat"), entry.get("lon")
            mwh = entry.get("energyMWh")
            if not code.isdigit() or code in seen:
                raise ValueError("Duplicate/missing EIA plant code: " + code)
            if not (isinstance(mw, (int, float)) and math.isfinite(mw) and mw >= 1000):
                raise ValueError("Nonqualifying MW for EIA plant " + code)
            if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))
                    and math.isfinite(lat) and math.isfinite(lon)
                    and -90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("Invalid coordinates for EIA plant " + code)
            if not (isinstance(mwh, (int, float)) and math.isfinite(mwh) and mwh > 0):
                raise ValueError("Missing positive 2024 net generation for EIA plant " + code)
            if entry.get("sourcePeriod") != "2024-12":
                raise ValueError("Wrong EIA source vintage for plant " + code)
            if not isinstance(entry.get("name"), str) or not entry["name"].strip():
                raise ValueError("Missing EIA plant name for " + code)
            entry["energyType"] = EIA_TECHNOLOGY.get(entry.get("energyType"), "Other")
            seen.add(code)
            rows.append(entry)
    return sorted(rows, key=lambda x: (-x["capacityMW"], x["name"]))


def load_eia_catalog(source=None):
    """Load all 7 sourced EIA regional parts from checkout, ZIP, or frozen build.

    Missing/incomplete additions are fatal, not silently shown as an empty map.
    """
    sources = [Path(source).expanduser()] if source is not None else list(_candidate_sources())
    for candidate in sources:
        candidate = Path(candidate).expanduser()
        if candidate.is_dir():
            root = candidate.parent if candidate.name.lower() == "data" else candidate
            if all((root / rel).is_file() for rel in EIA_PATHS):
                return _validate_eia_catalog([
                    json.loads((root / rel).read_text(encoding="utf-8-sig"))
                    for rel in EIA_PATHS
                ])
        elif candidate.is_file() and (candidate.suffix.lower() == ".zip" or zipfile.is_zipfile(candidate)):
            try:
                with zipfile.ZipFile(candidate) as archive:
                    names = set(archive.namelist())
                    prefixes = [key[:-len(EIA_PATHS[0])] for key in names
                                if key.endswith(EIA_PATHS[0])]
                    for prefix in prefixes:
                        if all(prefix + rel in names for rel in EIA_PATHS):
                            return _validate_eia_catalog([
                                json.loads(archive.read(prefix + rel).decode("utf-8-sig"))
                                for rel in EIA_PATHS
                            ])
            except zipfile.BadZipFile:
                pass
    raise FileNotFoundError(
        "New 1 GW EIA atlas records are missing. Download a fresh complete "
        "EnergyMap repository ZIP, including data/eia2024-1gw-01.json through 07.json."
    )



def _validate_project_localities(parts):
    """Use sourced municipality reference points, never inferred facility sites."""
    positions = {}
    for part in parts:
        if not isinstance(part, list):
            raise ValueError("Project locality collection must be a JSON array")
        for loc in part:
            if not isinstance(loc, dict):
                raise ValueError("Project locality must be a JSON object")
            code = loc.get("id")
            if not isinstance(code, str) or not code or code in positions:
                raise ValueError("Duplicate or invalid locality project ID: " + str(code))
            lat, lon = loc.get("lat"), loc.get("lon")
            if not (isinstance(lat, (int, float)) and not isinstance(lat, bool)
                    and isinstance(lon, (int, float)) and not isinstance(lon, bool)
                    and math.isfinite(lat) and math.isfinite(lon)
                    and -90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("Invalid project locality coordinate: " + code)
            if not all(isinstance(loc.get(field), str) and loc[field].strip()
                       for field in ("name", "state", "referencePlace", "source", "precision", "evidence")):
                raise ValueError("Missing project locality provenance: " + code)
            if not loc["source"].startswith("https://github.com/"):
                raise ValueError("Expected public locality provenance: " + code)
            positions[code] = loc
    return positions


def load_project_localities(source=None):
    """Find seven externally sourced, approximate project-locality mapping files."""
    candidates = [Path(source).expanduser()] if source is not None else list(_candidate_sources())
    for candidate in candidates:
        candidate = Path(candidate).expanduser()
        if candidate.is_dir():
            root = candidate.parent if candidate.name.lower() == "data" else candidate
            if all((root / rel).is_file() for rel in PROJECT_LOCALITY_PATHS):
                return _validate_project_localities([
                    json.loads((root / rel).read_text(encoding="utf-8-sig"))
                    for rel in PROJECT_LOCALITY_PATHS
                ])
        elif candidate.is_file() and (candidate.suffix.lower() == ".zip"
                                      or zipfile.is_zipfile(candidate)):
            try:
                with zipfile.ZipFile(candidate) as archive:
                    names = set(archive.namelist())
                    prefixes = [key[:-len(PROJECT_LOCALITY_PATHS[0])] for key in names
                                if key.endswith(PROJECT_LOCALITY_PATHS[0])]
                    for prefix in prefixes:
                        if all(prefix + rel in names for rel in PROJECT_LOCALITY_PATHS):
                            return _validate_project_localities([
                                json.loads(archive.read(prefix + rel).decode("utf-8-sig"))
                                for rel in PROJECT_LOCALITY_PATHS
                            ])
            except zipfile.BadZipFile:
                pass
    raise FileNotFoundError(
        "The sourced project-locality map layer is missing. Download a fresh complete "
        "EnergyMap repository ZIP with data/project-localities-01.json through 07.json."
    )


def combine_power_catalog(curated, eia):
    """Preserve all curated sites, then append nonduplicate historical EIA plants."""
    extra = [r for r in eia if r["eiaPlantCode"] not in CURATED_EIA_CODES]
    return sorted([*curated, *extra],
                  key=lambda x: (-float(x.get("capacityMW") or 0), x.get("name", "")))


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



# Every national Top 10 entry is an alternate published profile of a state
# ranking record. Explicit ID relationships prevent fuzzy-name conflation.
NATIONAL_TO_STATE_ID = {
    "27743-1": "27440-1", "27743-2": "27460-1",
    "27743-3": "27460-2", "27743-4": "27320-1",
    "27743-5": "27522-1", "27743-6": "27242-1",
    "27743-7": "26979-1", "27743-8": "27343-1",
    "27743-9": "27460-3", "27743-10": "27440-2",
}
# Those two apparent capacity conflicts refer to published power measures
# that must retain their separate units/scope and original source periods.
CAPACITY_EXPLANATIONS = {
    "27743-6": (
        "Developer's 6,500 MW proposed net onsite generation; "
        "4,960 MW is the separate proposed critical IT load.",
        "https://e2b4.com/investors/",
    ),
    "27743-8": (
        "Developer's updated 4,400 MW proposed gas generation; "
        "the earlier state editorial profile reports 4,500 MW.",
        "https://www.homercityredevelopment.com/project-overview",
    ),
}


def reconcile_data_center_rankings(rankings):
    """Build one canonical site per state profile, preserving national snapshots.

    This keeps the original research JSON untouched. Published project figures
    are planning claims and are not assumed to be commissioned capacity.
    """
    state_rows = [dict(r) for r in rankings if isinstance(r.get("rank"), (int, float))]
    national = {r["id"]: r for r in rankings
                if isinstance(r.get("nationalRank"), (int, float))}
    by_id = {r["id"]: r for r in state_rows}
    if len(by_id) != len(state_rows):
        raise ValueError("Duplicate state-ranking source ID")
    if set(national) != set(NATIONAL_TO_STATE_ID):
        raise ValueError("The national ranking source IDs have changed; review site reconciliation.")
    if len(set(NATIONAL_TO_STATE_ID.values())) != len(national):
        raise ValueError("National rankings contain duplicate state-project mappings")
    for row in state_rows:
        row["recordType"] = "Data centers / campuses"
        row["sourceCollection"] = "State ranking"
        row["capacityBasis"] = "Published project-scale power figure; actual metric varies by source"
        row["capacityScope"] = "Development / design / load measure; refer to project notes"
        row["status"] = "Editorial project profile (status varies; check source)"
        row["sourceID"] = row["id"]
        row["statePublishedMW"] = row.get("capacityMW")
        row["stateArticle"] = row.get("article")
        row["nationalRank"] = None

    for national_id, state_id in NATIONAL_TO_STATE_ID.items():
        if state_id not in by_id:
            raise ValueError("Missing state project for national entry " + national_id)
        national_record, row = national[national_id], by_id[state_id]
        if row["state"] != national_record["state"]:
            raise ValueError("National-to-state mapping crosses states: " + national_id)
        if not isinstance(national_record.get("capacityMW"), (int, float)):
            raise ValueError("Missing national project power figure: " + national_id)
        row["nationalRank"] = national_record["nationalRank"]
        row["nationalSourceID"] = national_id
        row["nationalArticle"] = national_record.get("article")
        row["nationalPublishedMW"] = national_record["capacityMW"]
        row["nationalName"] = national_record["name"]
        row["nationalPublishedDate"] = national_record.get("updated")
        row["statePublishedDate"] = row.get("updated")
        row["capacityMW"] = national_record["capacityMW"]
        row["capacityLabel"] = national_record.get("capacityLabel")
        row["sourceCollection"] = "State + national rankings"
        if national_id in CAPACITY_EXPLANATIONS:
            explanation, primary = CAPACITY_EXPLANATIONS[national_id]
            row["capacityBasis"] = explanation
            row["primarySource"] = primary
            row["capacityScope"] = ("Proposed onsite generation" if national_id == "27743-6"
                                    else "Proposed natural-gas generation")
        else:
            row["capacityBasis"] = "National ranking published project scale; compare scope in source"
        if row["statePublishedMW"] != row["nationalPublishedMW"]:
            row["reconciliationNote"] = (
                f"State ranking published {row['statePublishedMW']:,} MW; "
                f"national ranking published {row['nationalPublishedMW']:,} MW. "
                "These are retained as separate source observations, not silently averaged."
            )
        row["article"] = national_record.get("article") or row.get("article")
        row["updated"] = national_record.get("updated") or row.get("updated")
    return state_rows


def _has_capacity(record):
    value = record.get("capacityMW")
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0)


def _capacity_order(record):
    """Sort valid numerical MW first, ties by site name and permanent ID."""
    value = record["capacityMW"] if _has_capacity(record) else None
    return (value is None, -(value if value is not None else 0),
            str(record.get("name") or "").casefold(), str(record.get("id") or ""))


def assign_state_ranks(registry):
    """Rank every distinct site within its state using the same published MW field.

    Equal MW values share a competition-style rank (1, 1, 3).
    Unknown MW remains visible but is intentionally unranked.
    """
    from collections import defaultdict

    grouped = defaultdict(list)
    for site in registry:
        state = site.get("state")
        if not isinstance(state, str) or not state.strip():
            raise ValueError("Canonical site missing a state: " + str(site.get("id")))
        grouped[state].append(site)
    for state, entries in grouped.items():
        previous_mw = None
        last_rank = None
        for position, site in enumerate(sorted(entries, key=_capacity_order), start=1):
            if _has_capacity(site):
                mw = site["capacityMW"]
                if previous_mw != mw:
                    last_rank = position
                site["stateRank"] = last_rank
                previous_mw = mw
            else:
                site["stateRank"] = None
    return registry


def build_national_top_25(projects):
    """An editorially *computed* Top 25, not an extension of the published Top 10.

    Preserve original published nationalRank/record IDs in record details.
    Ties at the 25th position are resolved deterministically by project name,
    not falsely attributed to the original editorial ranking.
    """
    ordered = sorted((site for site in projects if _has_capacity(site)),
                     key=_capacity_order)
    top = ordered[:25]
    if len(top) != 25:
        raise ValueError("Fewer than 25 project profiles have reported MW")
    for rank, site in enumerate(top, start=1):
        site["nationalComputedRank"] = rank
    return top


def build_catalogs(rankings, curated, eia, project_localities=None):
    """One canonical catalog with independently sourced location-reference overlays."""
    projects = reconcile_data_center_rankings(rankings)
    localities = load_project_localities() if project_localities is None else project_localities
    by_id = {p["id"]: p for p in projects}
    for id_, location in localities.items():
        if id_ not in by_id:
            raise ValueError("Project locality references nonexistent site ID: " + id_)
        project = by_id[id_]
        if project["state"] != location["state"] or project["name"] != location["name"]:
            raise ValueError("Project locality identity mismatch: " + id_)
        if project.get("lat") is not None or project.get("lon") is not None:
            raise ValueError("Project location overlay would replace official site coordinates")
        project["lat"], project["lon"] = location["lat"], location["lon"]
        project["markerKind"] = "locality"
        project["mapReferencePlace"] = location["referencePlace"]
        project["mapLocationSource"] = location["source"]
        project["locationPrecision"] = (
            "Approximate " + location["referencePlace"] + ", " + project["state"]
            + " municipality reference — NOT verified facility coordinates"
        )
        project["mapLocationEvidence"] = location["evidence"]
    # Copy source records so catalog metadata never mutates loaded JSON lists.
    plants = [dict(source) for source in combine_power_catalog(curated, eia)]
    for row in plants:
        row["recordType"] = "Power generation"
        row["capacityScope"] = ("EIA December 2024 operable nameplate" if row.get("eiaPlantCode")
                                else "Curated facility generating capacity")
    registry = [*plants, *projects]
    ids = [row.get("id") for row in registry]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate canonical site IDs")
    assign_state_ranks(registry)
    national_top25 = build_national_top_25(projects)
    def qualified(rows):
        return [r for r in rows if _has_capacity(r) and r["capacityMW"] >= 1000]
    return {
        "All sites": registry,
        "All ≥1 GW": qualified(registry),
        "Power plants": plants,
        "EIA plants (2024)": [r for r in plants if r.get("eiaPlantCode")] + [
            # 22 source-overlap entries remain accessible in the historical
            # view, independent of the canonical 303-site map.
            dict(r, recordType="Power generation",
                 capacityScope="EIA December 2024 operable nameplate")
            for r in eia if r["eiaPlantCode"] in CURATED_EIA_CODES],
        "Curated plants": [r for r in plants if r.get("id", "").startswith("operating-us-")],
        "Data centers": projects,
        "Data centers ≥1 GW": qualified(projects),
        "State rankings": registry,
        "National top 25": national_top25,
    }


def sort_catalog(rows, column="capacity", descending=True, view=None):
    """Stable, numeric sorting; unknown MW always last in either direction."""
    if column in ("capacity", "rank"):
        rank_field = ("nationalComputedRank" if view == "National top 25"
                      else "stateRank" if view == "State rankings" else "rank")
        value_field = "capacityMW" if column == "capacity" else rank_field
        valid, missing = [], []
        for row in rows:
            value = row.get(value_field)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
                valid.append(row)
            else:
                missing.append(row)
        valid.sort(key=lambda x: str(x.get("name", "")).casefold())
        valid.sort(key=lambda x: float(x[value_field]), reverse=descending)
        return valid + sorted(missing, key=lambda r: str(r.get("name", "")).casefold())
    field = {"name": "name", "state": "state", "category": "recordType"}.get(column, "name")
    return sorted(rows, key=lambda r: (
        str((r.get("nationalName") if column == "name" and view == "National top 25"
             else None) or r.get(field) or "").casefold(),
        str(r.get("id") or "")), reverse=descending)


TABLE_MIN_WIDTHS = {"rank": 42, "name": 145, "state": 53, "category": 100, "capacity": 95}
TABLE_PREF_WIDTHS = {"rank": 52, "name": 280, "state": 84, "category": 175, "capacity": 118}


def table_column_widths(available_width, columns):
    """Fit all list columns into the visible Treeview, without horizontal scrolling."""
    columns = tuple(columns)
    if not columns:
        return {}
    budget = max(len(columns) * 2, int(available_width))
    minimum = {key: TABLE_MIN_WIDTHS[key] for key in columns}
    preferred = {key: TABLE_PREF_WIDTHS[key] for key in columns}
    min_total = sum(minimum.values())
    if budget < min_total:
        # Permit small panes without causing a horizontal scrollbar.
        widths = {key: max(2, minimum[key] * budget // min_total) for key in columns}
    else:
        available_growth = budget - min_total
        desired_growth = sum(preferred[key] - minimum[key] for key in columns)
        fraction = min(1.0, available_growth / desired_growth) if desired_growth else 0
        widths = {key: minimum[key] + int((preferred[key] - minimum[key]) * fraction)
                  for key in columns}
    # Allocate rounding remainder and any extra width to the project name.
    fill_column = "name" if "name" in widths else columns[0]
    widths[fill_column] += budget - sum(widths.values())
    return widths


def row_display_number(record, view, position):
    """Show real computed ranks for ranking views; otherwise the visible row number."""
    if view == "State rankings":
        rank = record.get("stateRank")
        return rank if rank is not None else "N/R"
    if view == "National top 25":
        rank = record.get("nationalComputedRank")
        return rank if rank is not None else "N/R"
    return position


class EnergyMapApp(tk.Tk):
    """Resizable, read-only desktop atlas preserving the existing vetted datasets."""

    def __init__(self):
        super().__init__()
        self.title("EnergyMap — Desktop Atlas")
        screen_w, screen_h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{min(1460, max(960, screen_w-70))}x{min(860, max(590, screen_h-100))}")
        self.minsize(min(960, screen_w), min(590, screen_h))
        self.rankings, self.operating = load_data()
        self.eia_catalog = load_eia_catalog()
        self.project_localities = load_project_localities()
        self.catalogs = build_catalogs(self.rankings, self.operating, self.eia_catalog,
                                       self.project_localities)
        states_geo, world_geo = load_geo_data()
        self.visible = {}
        self.view = tk.StringVar(value=VIEWS[0])
        states = sorted({r.get("state", "") for r in self.rankings if r.get("state")})
        self.state = tk.StringVar(value=ALL_STATES)
        self.category = tk.StringVar(value=CATEGORY_FILTERS[0])
        self.sort_column = "capacity"
        self.sort_desc = True
        self.search = tk.StringVar()
        self.status = tk.StringVar()

        shell = ttk.Frame(self, padding=(12, 10, 12, 8))
        shell.pack(fill="both", expand=True)
        ttk.Label(shell, text="EnergyMap  /  U.S. ENERGY INFRASTRUCTURE ATLAS",
                  font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(0, 2))
        self.summary = tk.StringVar()
        ttk.Label(shell, textvariable=self.summary, font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 10))
        self._update_summary()
        controls = ttk.Frame(shell)
        controls.pack(fill="x", pady=(0, 9))
        first = ttk.Frame(controls)
        first.pack(fill="x")
        ttk.Label(first, text="Dataset").pack(side="left")
        cb = ttk.Combobox(first, textvariable=self.view, values=VIEWS,
                          state="readonly", width=23)
        cb.pack(side="left", padx=(6, 14))
        cb.bind("<<ComboboxSelected>>", lambda _ev: self._change_view())
        ttk.Label(first, text="State").pack(side="left")
        self.state_combo = ttk.Combobox(first, textvariable=self.state, values=[ALL_STATES, *states],
                                        state="readonly", width=17)
        self.state_combo.pack(side="left", padx=(6, 14))
        self.state_combo.bind("<<ComboboxSelected>>", lambda _ev: self.refresh())
        ttk.Label(first, text="Search").pack(side="left")
        ttk.Entry(first, textvariable=self.search, width=26).pack(side="left", padx=(6, 6), fill="x", expand=True)
        ttk.Button(first, text="Clear", command=lambda: self.search.set(""), width=6).pack(side="left")
        second = ttk.Frame(controls)
        second.pack(fill="x", pady=(6, 0))
        ttk.Label(second, text="Category").pack(side="left")
        self.category_combo = ttk.Combobox(second, textvariable=self.category, values=CATEGORY_FILTERS,
                                           state="readonly", width=25)
        self.category_combo.pack(side="left", padx=(6, 16))
        self.category_combo.bind("<<ComboboxSelected>>", lambda _ev: self.refresh())
        ttk.Button(second, text="Reload data", command=self.reload_from_disk).pack(side="left")
        ttk.Button(second, text="Open source", command=self.open_source).pack(side="left", padx=(8, 0))
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
        self.cols = ("rank", "name", "state", "category", "capacity")
        self.tree = ttk.Treeview(table_frame, columns=self.cols, show="headings", selectmode="browse")
        self.headings = {"rank": "Rank", "name": "Project / plant", "state": "State",
                         "category": "Category", "capacity": "Capacity MW"}
        for key, anchor in (
            ("rank", "center"), ("name", "w"), ("state", "w"),
            ("category", "w"), ("capacity", "e")
        ):
            self.tree.heading(key, text=self.headings[key],
                              command=lambda column=key: self.change_sort(column))
            self.tree.column(key, width=TABLE_MIN_WIDTHS[key], minwidth=1,
                             anchor=anchor, stretch=False)
        self._update_sort_headings()
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        self.tree.bind("<Configure>", self._fit_table_columns, add="+")
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
        footer = ttk.Frame(shell)
        # Reserve footer space before the expanding map/list pane is measured.
        footer.pack(side="bottom", fill="x", pady=(8, 0), before=self.pane)
        self.brand_label = tk.Label(
            footer, text="BitcoinVersus.tech", foreground="#39FF14",
            background="#080808", font=("Segoe Script", 10, "bold"),
            padx=7, pady=3, borderwidth=0
        )
        self.brand_label.pack(side="left", anchor="sw", padx=(0, 10))
        self.status_label = ttk.Label(footer, textvariable=self.status, anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)
        self.bind("<Configure>", self._resize_status)
        self.after_idle(self._initial_layout)
        self.refresh()

    def _initial_layout(self):
        try:
            width = self.pane.winfo_width()
            if width > 600:
                self.pane.sashpos(0, min(width - 310, max(520, int(width * .60))))
            self.atlas.draw()
        except tk.TclError:
            pass

    def _fit_table_columns(self, event):
        if event.widget is not self.tree:
            return
        for key, width in table_column_widths(max(5, event.width - 10), self.cols).items():
            self.tree.column(key, width=width)

    def _resize_status(self, event):
        if event.widget is self:
            remaining = event.width - self.brand_label.winfo_width() - 50
            self.status_label.configure(wraplength=max(160, remaining))

    def _update_summary(self):
        self.summary.set(f"{len(self.catalogs['All sites']):,} sites  •  "
                         f"{len(self.catalogs['All ≥1 GW']):,} ≥1 GW  •  "
                         f"{len(self.catalogs['Power plants']):,} generators  •  "
                         f"{len(self.catalogs['Data centers']):,} campus profiles  •  "
                         "MW scopes differ")

    def _update_sort_headings(self):
        ranked_view = self.view.get() in ("State rankings", "National top 25")
        for key, label in self.headings.items():
            if key == "rank":
                label = ("State #" if self.view.get() == "State rankings"
                         else "Top 25 #" if self.view.get() == "National top 25"
                         else "Row #")
            arrow = (" ↓" if self.sort_desc else " ↑") if key == self.sort_column else ""
            # Row numbers are positions in the active sort, not a separate ranking.
            sortable = key != "rank" or ranked_view
            command = (lambda column=key: self.change_sort(column)) if sortable else ""
            self.tree.heading(key, text=label + arrow, command=command)

    def change_sort(self, column):
        if column == "rank" and self.view.get() not in ("State rankings", "National top 25"):
            return
        if column == self.sort_column:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_column = column
            self.sort_desc = column == "capacity"
        self._update_sort_headings()
        self.refresh()

    def _change_view(self):
        # A new dataset opens unfiltered and in descending numeric MW order.
        # Without resetting the old state/category, users could see an empty
        # view and mistakenly assume source records were never imported.
        self.state.set(ALL_STATES)
        self.category.set(CATEGORY_FILTERS[0])
        self.sort_column, self.sort_desc = "capacity", True
        self._update_sort_headings()
        self.refresh()

    def reload_from_disk(self):
        try:
            rankings, operating = load_data()
            eia = load_eia_catalog()
            locations = load_project_localities()
            states_geo, world_geo = load_geo_data()
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            messagebox.showerror("Reload failed", str(exc), parent=self)
            return
        self.rankings, self.operating = rankings, operating
        self.eia_catalog = eia
        self.project_localities = locations
        self.catalogs = build_catalogs(rankings, operating, eia, locations)
        self._update_summary()
        self.atlas.states = tuple(rings_from_features(states_geo))
        self.atlas.countries = tuple(rings_from_features(world_geo))
        states = sorted({r.get("state", "") for r in rankings if r.get("state")})
        self.state_combo["values"] = [ALL_STATES, *states]
        if self.state.get() not in (ALL_STATES, *states):
            self.state.set(ALL_STATES)
        self.refresh()

    def records(self):
        items = self.catalogs[self.view.get()]
        if self.state.get() != ALL_STATES:
            items = [r for r in items if r.get("state") == self.state.get()]
        if self.category.get() != CATEGORY_FILTERS[0]:
            items = [r for r in items if r.get("recordType") == self.category.get()]
        needle = self.search.get().strip().casefold()
        if needle:
            items = [r for r in items if needle in " ".join(
                str(r.get(key, "")) for key in (
                    "name", "nationalName", "state", "recordType",
                    "energyType", "brief", "status", "heading", "capacityBasis"
                )).casefold()]
        return sort_catalog(items, self.sort_column, self.sort_desc, self.view.get())

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
            rank = row_display_number(item, self.view.get(), index + 1)
            display_name = (item.get("nationalName") if self.view.get() == "National top 25"
                            else item.get("name"))
            self.tree.insert("", "end", iid=key, tags=("even" if index % 2 == 0 else "odd",),
                             values=(rank, display_name or item.get("name", ""),
                                     item.get("state", ""), item.get("recordType", "Power generation"),
                                     label))
        if selected is None and self.visible:
            selected = "0"
        if selected is not None:
            self.tree.selection_set(selected)
        else:
            self._show_details(None)
        self.atlas.set_records(self.visible, selected,
                               self.state.get() if self.state.get() != ALL_STATES else "")
        mapped = sum(1 for item in self.visible.values() if self.atlas._coordinates(item))
        scope_note = ("State ranks include all site types; MW scopes differ"
                      if self.view.get() == "State rankings"
                      else "Computed Top 25 of campus plans; not published Top 10"
                      if self.view.get() == "National top 25"
                      else "MW scopes differ; see record details")
        self.status.set(f"{len(self.visible):,} records  |  {mapped:,} with coordinates  |  "
                        "Click headings to sort  |  " + scope_note)

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
                ("Category", item.get("recordType", "Power generation")),
                ("Technology", item.get("energyType")),
                ("Project status / evidence", item.get("status")),
                ("Power measurement scope", item.get("capacityScope")),
                ("Capacity (MW)", item.get("capacityLabel") or item.get("capacityMW")),
                ("Capacity basis", item.get("capacityBasis")),
                ("National publication name", item.get("nationalName")),
                ("State ranking MW (if available)", item.get("statePublishedMW")),
                ("National ranking MW (if available)", item.get("nationalPublishedMW")),
                ("State MW rank (calculated)", item.get("stateRank")),
                ("National Top 25 position (calculated)", item.get("nationalComputedRank")),
                ("Original published state rank", item.get("rank")),
                ("Original published Top 10 rank", item.get("nationalRank")),
                ("State profile date", item.get("statePublishedDate")),
                ("National profile date", item.get("nationalPublishedDate")),
                ("Capacity reconciliation", item.get("reconciliationNote")),
                ("Measured power (MW)", item.get("productionMW")),
                ("Energy (MWh)", item.get("energyMWh")),
                ("Energy period", item.get("energyPeriod")),
                ("Data period / last update", item.get("sourcePeriod") or item.get("verificationDate") or item.get("updated")),
                ("Source organization", item.get("sourceOrganization")),
                ("Location precision", item.get("locationPrecision")),
                ("Mapped reference place", item.get("mapReferencePlace")),
                ("Map reference evidence", item.get("mapLocationEvidence")),
            )
            for label, value in pairs:
                if (value is None or value == "") and label in (
                    "State ranking MW (if available)", "National ranking MW (if available)",
                    "State MW rank (calculated)", "National Top 25 position (calculated)",
                    "Original published state rank", "Original published Top 10 rank",
                    "State profile date", "National profile date",
                    "National publication name", "Capacity reconciliation", "Power measurement scope",
                    "Mapped reference place", "Map reference evidence"
                ):
                    continue
                self.info.insert("end", label + ":  ", "field")
                self.info.insert("end", f"{value if value is not None and value != '' else 'Not reported'}\n")
            self.info.insert("end", "\nResearch notes\n", "field")
            self.info.insert("end", str(item.get("brief") or "No additional description") + "\n\n")
            self.info.insert("end", "Main source:  ", "field")
            self.info.insert("end", str(item.get("article") or "Not reported") + "\n")
            for label, field in (("Mapped locality source", "mapLocationSource"),
                                 ("State profile", "stateArticle"),
                                 ("National profile", "nationalArticle"),
                                 ("Primary source", "primarySource"),
                                 ("EIA secondary source", "additionalSource")):
                if item.get(field):
                    self.info.insert("end", label + ":  ", "field")
                    self.info.insert("end", str(item[field]) + "\n")
        self.info.configure(state="disabled")

    def select_from_map(self, key):
        if key in self.visible:
            self.tree.selection_set(key)
            self.tree.see(key)
            self.on_select()

    def open_source(self):
        sel = self.tree.selection()
        item = self.visible.get(sel[0]) if sel else None
        url = (item.get("primarySource") or item.get("article")) if item else None
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
            load_eia_catalog()
            load_project_localities()
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
