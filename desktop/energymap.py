"""EnergyMap Python desktop edition. Offline data viewer and personal-site editor.

The reviewed repository datasets are bundled unchanged. Capacity (MW) is not
energy generation (MWh); proposed data-center loads are not operating plants.
"""
from __future__ import annotations

import json
import math
import sys
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from uuid import uuid4

DATA_FILES = [f"data/states-{i:02d}.json" for i in range(1, 7)]
DATA_FILES.append("data/states-07-national.json")
OPERATING = "data/operating-1gw.json"
VIEWS = ("Operating plants", "State rankings", "National top 10", "My map")
FIELDS = ("name", "state", "energyType", "status", "lat", "lon",
          "capacityMW", "capacityBasis", "productionMW", "energyMWh",
          "energyPeriod", "article", "brief")


def asset_path(relative):
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return root / relative


def load_data():
    def read(relative):
        path = asset_path(relative)
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, list):
            raise ValueError(f"{relative} must contain a JSON array")
        return value
    rankings = []
    for name in DATA_FILES:
        rankings.extend(read(name))
    return rankings, read(OPERATING)


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


class SiteDialog(tk.Toplevel):
    def __init__(self, parent, site=None):
        super().__init__(parent)
        self.title("My site")
        self.resizable(True, True)
        self.result = None
        self.entries = {}
        self.transient(parent)
        self.grab_set()
        body = ttk.Frame(self, padding=12)
        body.pack(fill="both", expand=True)
        for i, field in enumerate(FIELDS):
            ttk.Label(body, text=field).grid(row=i, column=0, sticky="w", pady=2)
            widget = ttk.Entry(body, width=68)
            widget.grid(row=i, column=1, sticky="ew", pady=2)
            value = "" if site is None else site.get(field)
            if value is not None:
                widget.insert(0, str(value))
            self.entries[field] = widget
        body.columnconfigure(1, weight=1)
        ttk.Button(body, text="Save site", command=self.save).grid(
            row=len(FIELDS), column=1, sticky="e", pady=8)
        self.bind("<Escape>", lambda _e: self.destroy())
        self.wait_visibility()
        self.focus_set()
        self.wait_window()

    def save(self):
        try:
            entry = {k: v.get() for k, v in self.entries.items()}
            self.result = validate_site(entry)
        except (ValueError, TypeError) as exc:
            messagebox.showerror("Invalid site", str(exc), parent=self)
            return
        self.destroy()


class EnergyMapApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EnergyMap — Python Desktop")
        self.geometry("1180x760")
        self.minsize(850, 540)
        self.rankings, self.operating = load_data()
        self.custom = self._read_custom()
        self.visible = {}
        self.point_hits = []
        self.view = tk.StringVar(value=VIEWS[0])
        states = sorted({r.get("state", "") for r in self.rankings if r.get("state")})
        self.state = tk.StringVar(value=states[0] if states else "")
        self.search = tk.StringVar()
        self.status = tk.StringVar()
        tools = ttk.Frame(self, padding=8)
        tools.pack(fill="x")
        ttk.Label(tools, text="View").pack(side="left")
        cb = ttk.Combobox(tools, textvariable=self.view, values=VIEWS, state="readonly", width=19)
        cb.pack(side="left", padx=5)
        cb.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        ttk.Label(tools, text="State").pack(side="left", padx=(10, 2))
        state_cb = ttk.Combobox(tools, textvariable=self.state, values=states,
                                state="readonly", width=18)
        state_cb.pack(side="left", padx=5)
        state_cb.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        ttk.Label(tools, text="Search").pack(side="left", padx=(10, 2))
        ttk.Entry(tools, textvariable=self.search, width=22).pack(side="left", padx=5)
        self.search.trace_add("write", lambda *_: self.refresh())
        for label, command in (("Add site", self.add_site), ("Edit", self.edit_site),
                               ("Delete", self.delete_site), ("Import", self.import_sites),
                               ("Export", self.export_sites), ("Open source", self.open_source)):
            ttk.Button(tools, text=label, command=command).pack(side="left", padx=2)
        pane = ttk.Panedwindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=8, pady=5)
        left = ttk.Frame(pane)
        pane.add(left, weight=3)
        right = ttk.Panedwindow(pane, orient="vertical")
        pane.add(right, weight=4)
        cols = ("rank", "name", "state", "capacity", "status")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        for name, title, width in zip(cols, ("Rank", "Site", "State", "MW (rated/planned)", "Stage"),
                                      (52, 265, 100, 140, 95)):
            self.tree.heading(name, text=title)
            self.tree.column(name, width=width, stretch=name == "name")
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self.on_select())
        map_frame = ttk.Frame(right)
        right.add(map_frame, weight=3)
        ttk.Label(map_frame, text="Geographic coordinates — approximate site points, not state boundaries").pack(anchor="w")
        self.canvas = tk.Canvas(map_frame, bg="#edf3f5", height=330, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _e: self.redraw_map())
        self.canvas.bind("<Button-1>", self.map_click)
        details = ttk.Frame(right)
        right.add(details, weight=2)
        self.info = tk.Text(details, wrap="word", height=11)
        self.info.pack(fill="both", expand=True)
        ttk.Label(self, textvariable=self.status, padding=(10, 3)).pack(anchor="w")
        self.refresh()

    def _read_custom(self):
        path = user_path()
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("Custom site file is not an array")
            return [validate_site(x) for x in data]
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showwarning("Personal sites", f"Could not load {path}:\n{exc}")
            return []

    def _save_custom(self):
        path = user_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        pending = path.with_suffix(".tmp")
        pending.write_text(json.dumps(self.custom, indent=2, ensure_ascii=False), encoding="utf-8")
        pending.replace(path)

    def records(self):
        mode = self.view.get()
        if mode == "Operating plants":
            data = self.operating
        elif mode == "State rankings":
            data = state_records(self.rankings, self.state.get())
        elif mode == "National top 10":
            data = national_records(self.rankings)
        else:
            data = self.custom
        query = self.search.get().strip().casefold()
        if query:
            data = [r for r in data if query in " ".join(
                str(r.get(key, "")) for key in ("name", "state", "energyType", "brief", "status")
            ).casefold()]
        return data

    def refresh(self):
        if not hasattr(self, "tree"):
            return
        prior = self.tree.selection()
        chosen = prior[0] if prior else None
        self.tree.delete(*self.tree.get_children())
        self.visible = {}
        data = self.records()
        for index, item in enumerate(data):
            uid = str(index)
            self.visible[uid] = item
            mw = item.get("capacityMW")
            try:
                formatted = f"{float(mw):,.0f}" if mw is not None and mw != "" else "Not stated"
            except (TypeError, ValueError):
                formatted = "Not stated"
            rank = item.get("nationalRank") if self.view.get() == "National top 10" else item.get("rank")
            self.tree.insert("", "end", iid=uid, values=(
                rank if rank is not None else "", item.get("name", ""),
                item.get("state", ""), formatted, item.get("status", "")))
        self.status.set(f"{len(data)} entries shown. Missing coordinates are intentionally NOT invented. "
                        "MW is capacity, not MWh production.")
        if chosen in self.visible:
            self.tree.selection_set(chosen)
        elif data:
            self.tree.selection_set("0")
        else:
            self.info.delete("1.0", "end")
        self.redraw_map()

    def on_select(self):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.visible.get(selection[0])
        if not item:
            return
        lines = [item.get("heading") or item.get("name", ""), "",
                 f"State: {item.get('state', 'Not stated')}",
                 f"Technology: {item.get('energyType') or item.get('status') or 'Not stated'}",
                 f"Rated/planned capacity: {item.get('capacityLabel') or item.get('capacityMW') or 'Not stated'} MW",
                 f"Capacity basis: {item.get('capacityBasis') or 'See source; verify scope'}",
                 f"Measured operating power: {item.get('productionMW') if item.get('productionMW') is not None else 'Not supplied'} MW",
                 f"Reported energy: {item.get('energyMWh') if item.get('energyMWh') is not None else 'Not supplied'} MWh",
                 f"Energy reporting period: {item.get('energyPeriod') or 'Not supplied'}",
                 f"Verification/update: {item.get('verificationDate') or item.get('updated') or 'Not supplied'}",
                 "", str(item.get("brief") or ""),
                 "", f"Source: {item.get('article') or 'Not supplied'}"]
        self.info.delete("1.0", "end")
        self.info.insert("end", "\n".join(lines))
        self.redraw_map()

    def redraw_map(self):
        if not hasattr(self, "canvas"):
            return
        c = self.canvas
        c.delete("all")
        w, h = max(c.winfo_width(), 240), max(c.winfo_height(), 200)
        left, top, right, bottom = 35, 25, w - 20, h - 35
        c.create_rectangle(left, top, right, bottom, outline="#64748b")
        for lon in range(-120, -60, 10):
            x = left + (lon + 125) / 59 * (right - left)
            c.create_line(x, top, x, bottom, fill="#d9e0e6")
            c.create_text(x, bottom + 12, text=f"{lon}°", fill="#4a5568", font=("Arial", 8))
        for lat in range(25, 51, 5):
            y = bottom - (lat - 24) / 26 * (bottom - top)
            c.create_line(left, y, right, y, fill="#d9e0e6")
            c.create_text(left - 15, y, text=str(lat), font=("Arial", 8), fill="#4a5568")
        self.point_hits = []
        selection = self.tree.selection()
        selected = selection[0] if selection else None
        for key, site in self.visible.items():
            try:
                lon, lat = float(site["lon"]), float(site["lat"])
            except (KeyError, TypeError, ValueError):
                continue
            if not -125 <= lon <= -66 or not 24 <= lat <= 50:
                continue
            x = left + (lon + 125) / 59 * (right - left)
            y = bottom - (lat - 24) / 26 * (bottom - top)
            radius = 6 if key == selected else 4
            color = "#a855f7" if self.view.get() == "My map" else "#008b8b"
            c.create_oval(x-radius, y-radius, x+radius, y+radius,
                          fill=color, outline="#182c36", width=2 if key == selected else 1)
            self.point_hits.append((x, y, key))
        c.create_text(w / 2, 11, text=f"{len(self.point_hits)} mapped locations (continental U.S. viewport)",
                      fill="#334155", font=("Arial", 10))

    def map_click(self, event):
        if not self.point_hits:
            return
        x, y, key = min(self.point_hits, key=lambda p: (p[0]-event.x)**2 + (p[1]-event.y)**2)
        if (x-event.x)**2 + (y-event.y)**2 < 14**2:
            self.tree.selection_set(key)
            self.tree.see(key)

    def add_site(self):
        dialog = SiteDialog(self)
        if dialog.result:
            self.custom.append(dialog.result)
            try:
                self._save_custom()
            except OSError as exc:
                self.custom.pop()
                messagebox.showerror("Save failed", str(exc))
                return
            self.view.set("My map")
            self.refresh()

    def _selected_custom(self):
        if self.view.get() != "My map":
            messagebox.showinfo("My map", "Switch to My map to edit or delete personal sites.")
            return None
        selection = self.tree.selection()
        return self.visible.get(selection[0]) if selection else None

    def edit_site(self):
        old = self._selected_custom()
        if old is None:
            return
        dialog = SiteDialog(self, old)
        if dialog.result:
            dialog.result["id"] = old["id"]
            index = self.custom.index(old)
            self.custom[index] = dialog.result
            try:
                self._save_custom()
            except OSError as exc:
                self.custom[index] = old
                messagebox.showerror("Save failed", str(exc))
                return
            self.refresh()

    def delete_site(self):
        site = self._selected_custom()
        if site and messagebox.askyesno("Delete site", f"Remove {site['name']}?"):
            previous = self.custom[:]
            self.custom = [s for s in self.custom if s["id"] != site["id"]]
            try:
                self._save_custom()
            except OSError as exc:
                self.custom = previous
                messagebox.showerror("Save failed", str(exc))
                return
            self.refresh()

    def import_sites(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            if Path(path).stat().st_size > 2000000:
                raise ValueError("Import must be 2 MB or smaller")
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(payload, list) or len(payload) > 5000:
                raise ValueError("Expected a JSON array of at most 5,000 sites.")
            incoming = [validate_site(s) for s in payload]
            current = self.custom[:]
            by_id = {s["id"]: s for s in current}
            by_id.update({s["id"]: s for s in incoming})
            self.custom = list(by_id.values())
            try:
                self._save_custom()
            except OSError:
                self.custom = current
                raise
            self.view.set("My map")
            self.search.set("")
            self.refresh()
            messagebox.showinfo("Import complete", f"Imported {len(incoming)} personal records.")
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            messagebox.showerror("Import failed", str(exc))

    def export_sites(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                    initialfile="energymap-my-sites.json", filetypes=[("JSON", "*.json")])
        if path:
            try:
                Path(path).write_text(json.dumps(self.custom, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
                messagebox.showinfo("Export complete", f"Saved {len(self.custom)} records.")
            except OSError as exc:
                messagebox.showerror("Export failed", str(exc))

    def open_source(self):
        selection = self.tree.selection()
        record = self.visible.get(selection[0]) if selection else None
        url = record.get("article", "") if record else ""
        if isinstance(url, str) and url.startswith(("https://", "http://")):
            webbrowser.open(url)
        else:
            messagebox.showinfo("Source unavailable", "No valid source URL for this record.")


if __name__ == "__main__":
    try:
        EnergyMapApp().mainloop()
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("EnergyMap data unavailable",
            f"Could not load the bundled data files:\n{exc}\n\nDownload the complete repository ZIP "
            "or use a packaged desktop build with its embedded data.")
        root.destroy()
