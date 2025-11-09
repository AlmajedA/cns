from __future__ import annotations

from typing import Callable, List, Optional, Dict, Any
import tkinter as tk

from ..core import config as C
from ..core.models import Bounds, LngLat, Ring, PointFeature
from ..core.geo import load_geo_from_json, compute_bounds, ring_bounds, pad_bounds
from .renderer import CanvasRenderer
from .popup import SectionPopup
from app.core.paths import resource_path

logo_path = resource_path("assets", "logo.png")                    # image
config_path = resource_path("config", "east.json")                 # data json
cns_dir = resource_path("CNS drawings", "MPS")                     # whole folder


class MapApp:
    """Controller: wires events/state/animation; uses CanvasRenderer for drawing."""

    def __init__(self, main_rings: List[Ring]) -> None:
        # Tk root
        self.root = tk.Tk()
        self.root.title(C.TITLE)

        # Title bar
        title_frame = tk.Frame(self.root, bg=C.BACKGROUND, pady=10); title_frame.pack(fill="x")
        self.map_title_label = tk.Label(title_frame, text="Automated CNS 3D Infrastructure", font=("Arial", 24, "bold"), fg="#19171C", bg=C.BACKGROUND)
        self.map_title_label.pack()

        # Map container
        map_frame = tk.Frame(self.root); map_frame.pack(fill="both", expand=True)
        self.renderer = CanvasRenderer(map_frame)

        # Optional corner logo
        logo_path = str((C.ASSETS_DIR / "logo.png"))  # place your logo here
        self.root.after(0, lambda: self.renderer.set_corner_logo(logo_path, max_width=100, max_height=100, opacity=255, margin=12))

        # Back button
        self.back_btn = tk.Button(map_frame, text="⟵ Back", command=self.back_to_map)
        self.back_btn.place(x=10, y=10); self.back_btn.lower()

        # State
        self.main_rings = main_rings
        self.main_bounds = compute_bounds(main_rings)
        self.cur_rings: List[Ring] = self.main_rings
        self.cur_points: List[PointFeature] = []
        self.cur_bounds: Bounds = self.main_bounds
        self.in_detail = False
        self.detail_for_idx: Optional[int] = None
        self._markers_ll: List[LngLat] = []
        self._point_popup: Optional[tk.Toplevel] = None

        # Events
        self.renderer.canvas.bind("<Configure>", self.on_resize)
        self.renderer.canvas.tag_bind("ring", "<Enter>", self.on_ring_enter)
        self.renderer.canvas.tag_bind("ring", "<Leave>", self.on_ring_leave)
        self.renderer.canvas.tag_bind("ring", "<Button-1>", self.on_ring_click)
        self.renderer.canvas.tag_bind("point", "<Button-1>", self.on_point_click)
        self.renderer.canvas.tag_bind("point", "<Enter>", lambda e: self.renderer.canvas.config(cursor="hand2"))
        self.renderer.canvas.tag_bind("point", "<Leave>", lambda e: self.renderer.canvas.config(cursor=""))
        self.root.bind("<Escape>", self._on_escape)

        self._redraw()

    # ---------- Draw ----------
    def _redraw(self) -> None:
        if self.in_detail: self.back_btn.lift()
        else: self.back_btn.lower()

        detail_fill = None
        if self.in_detail and self.detail_for_idx is not None and hasattr(C, "SECTOR_COLORS"):
            detail_fill = C.SECTOR_COLORS[self.detail_for_idx % len(C.SECTOR_COLORS)]

        self.renderer.draw(
            bounds=self.cur_bounds,
            rings=self.cur_rings,
            points=self.cur_points,
            user_markers=self._markers_ll,
            in_detail=self.in_detail,
            detail_fill_override=detail_fill,
        )

    # ---------- Events ----------
    def on_resize(self, _evt: tk.Event) -> None:
        self._redraw()
        self.renderer.reposition_logo()

    def on_ring_enter(self, _event: tk.Event) -> None:
        self.renderer.canvas.config(cursor="hand2")

    def on_ring_leave(self, _event: tk.Event) -> None:
        self.renderer.canvas.config(cursor="")

    def on_ring_click(self, _event: tk.Event) -> None:
        if self.in_detail: return
        current = self.renderer.canvas.find_withtag("current")
        if not current: return
        item = current[0]
        tags = self.renderer.canvas.gettags(item)
        ring_tag = next((t for t in tags if t.startswith("ring-")), None)
        if ring_tag is None: return
        try:
            idx = int(ring_tag.split("-")[1])
        except (IndexError, ValueError):
            return
        tgt = pad_bounds(ring_bounds(self.main_rings[idx]), C.TARGET_PADDING_RATIO)
        self.animate_zoom_to(tgt, then=lambda: self._load_detail_and_show(idx))

    def _on_escape(self, _evt: tk.Event) -> None:
        if self.in_detail: self.back_to_map()

    # ---------- Detail loading ----------
    def _load_detail_and_show(self, idx: int) -> None:
        path = C.DETAIL_JSON_FOR_RING.get(idx)
        if path is None or not path.exists():
            self._redraw(); return
        detail_rings, detail_points = load_geo_from_json(path)
        if not detail_rings:
            self._redraw(); return
        self.in_detail = True
        self.detail_for_idx = idx
        self.cur_rings = detail_rings
        self.cur_points = detail_points
        detail_bounds = compute_bounds(detail_rings)
        self.animate_zoom_to(detail_bounds, then=self._redraw)

    # ---------- Back ----------
    def back_to_map(self) -> None:
        self.in_detail = False
        self.detail_for_idx = None
        self.cur_rings = self.main_rings
        self.cur_points = []
        self.animate_zoom_to(self.main_bounds, then=self._redraw)

    # ---------- Point click -> Popup ----------
    def on_point_click(self, event: tk.Event) -> None:
        if not self.in_detail: return
        current = self.renderer.canvas.find_withtag("current")
        if not current: return
        tags = self.renderer.canvas.gettags(current[0])
        ptag = next((t for t in tags if t.startswith("point-")), None)
        if ptag is None: return
        try: pidx = int(ptag.split("-")[1])
        except (IndexError, ValueError): return
        try:
            lon, lat, site, sector_id, freq, power = self.cur_points[pidx]
        except IndexError:
            return
        section_info = {"site": site, "lon": lon, "lat": lat, "sectorId": sector_id, "freq": freq, "power": power}
        SectionPopup(self.root, site or "Details", section_info)

    # ---------- Zoom animation ----------
    def animate_zoom_to(self, target: Bounds, then: Optional[Callable[[], None]] = None) -> None:
        start = self.cur_bounds
        steps = max(1, C.ANIM_STEPS)
        delay = max(1, C.ANIM_TOTAL_MS // steps)
        frame = {"i": 0}

        def step() -> None:
            i = frame["i"]
            t = (i + 1) / steps
            self.cur_bounds = start.lerp(target, t)
            self._redraw()
            frame["i"] += 1
            if frame["i"] < steps:
                self.renderer.canvas.after(delay, step)
            else:
                self.cur_bounds = target
                if then: then()

        step()

    # ---------- Run ----------
    def run(self) -> None:
        self.root.mainloop()