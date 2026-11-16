"""Native Tkinter atlas: offline U.S. outlines and orthographic rotating globe.

Bundled maps use public Natural Earth country boundaries and U.S. state polygons.
No embedded browser, JavaScript, or network calls are needed for map display.
"""
from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk

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
        self.globe_lon = -100.0
        self.spin_id = None
        self.drag_from = None
        self.drag_moved = False
        self.mode = tk.StringVar(value=MAP_MODES[0])
        self.note = tk.StringVar(value="Real boundaries • Approximate source coordinates")
        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(2, 5))
        ttk.Label(controls, text="GEOGRAPHIC ATLAS", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(2, 16))
        self.map_combo = ttk.Combobox(controls, textvariable=self.mode, values=MAP_MODES,
                                      state="readonly", width=17)
        self.map_combo.pack(side="left")
        self.map_combo.bind("<<ComboboxSelected>>", self.change_mode)
        self.spin_button = ttk.Button(controls, text="Spin globe", command=self.toggle_spin, width=13)
        self.spin_button.pack(side="left", padx=6)
        ttk.Button(controls, text="Reset", command=self.reset_map, width=7).pack(side="left")
        self.canvas = tk.Canvas(self, bg="#e5f1f5", highlightthickness=0, height=400)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self.draw())
        self.canvas.bind("<ButtonPress-1>", self.mouse_down)
        self.canvas.bind("<B1-Motion>", self.mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.mouse_up)
        caption = ttk.Label(self, textvariable=self.note, padding=(3, 5))
        caption.pack(fill="x")
        self._sync_spin_state()

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
        if self.mode.get() == "World globe":
            self._draw_globe(c, w, h)
        else:
            self._draw_united_states(c, w, h)
        counted = len(self.point_hits)
        self.note.set(f"{counted} mapped of {len(self.visible)} shown  •  "
                      "Dots use recorded coordinates; missing locations are not estimated")

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
        r = 6.5 if selected else 4.3
        c.create_oval(x-r, y-r, x+r, y+r, fill="#ffd166" if selected else "#007e8e",
                      outline="#103b52", width=1.8 if selected else 1)
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
