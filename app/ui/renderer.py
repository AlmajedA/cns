from __future__ import annotations
from typing import List, Optional, Tuple
import tkinter as tk

from ..core.models import Bounds, LngLat, Ring, PointFeature
from ..core import config as C

# Pillow (optional) for better resizing/opacity of the corner logo
try:
    from PIL import Image, ImageTk  # type: ignore
    _PIL_AVAILABLE = True
except Exception:
    _PIL_AVAILABLE = False
from app.core.paths import resource_path

logo_path = resource_path("assets", "logo.png")                    # image
config_path = resource_path("config", "east.json")                 # data json
cns_dir = resource_path("CNS drawings", "MPS")                     # whole folder


class CanvasRenderer:
    """Only renders and exposes hit-tags; keeps no application state."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.canvas = tk.Canvas(
            root,
            width=C.WINDOW_WIDTH,
            height=C.WINDOW_HEIGHT,
            bg=getattr(C, "BACKGROUND", "white"),
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self._poly_items: List[int] = []
        self._marker_items: List[int] = []
        self._fixed_point_items: List[int] = []
        self._label_items: List[int] = []

        self.cur_bounds: Bounds | None = None

        # Corner logo state
        self._logo_imgtk: Optional["ImageTk.PhotoImage" | tk.PhotoImage] = None
        self._logo_item: Optional[int] = None
        self._logo_margin: int = 10
        self._logo_max_w: int = 120
        self._logo_max_h: int = 60
        self._logo_opacity: int = 255  # 0..255 (Pillow only)

        self.canvas.bind("<Configure>", self._on_canvas_resize)

    # ---- projection helpers bound to current Bounds ----
    def project(self, lon: float, lat: float, w: int, h: int) -> Tuple[float, float]:
        assert self.cur_bounds is not None, "cur_bounds must be set before drawing"
        b = self.cur_bounds
        x = C.PADDING + (lon - b.min_lon) / (b.max_lon - b.min_lon) * (w - 2 * C.PADDING)
        y = C.PADDING + (b.max_lat - lat) / (b.max_lat - b.min_lat) * (h - 2 * C.PADDING)
        return x, y

    def inv_project(self, x: float, y: float, w: int, h: int) -> Tuple[float, float]:
        assert self.cur_bounds is not None, "cur_bounds must be set before drawing"
        x = max(C.PADDING, min(w - C.PADDING, x))
        y = max(C.PADDING, min(h - C.PADDING, y))
        b = self.cur_bounds
        lon = b.min_lon + ((x - C.PADDING) / (w - 2 * C.PADDING)) * (b.max_lon - b.min_lon)
        lat = b.max_lat - ((y - C.PADDING) / (h - 2 * C.PADDING)) * (b.max_lat - b.min_lat)
        return lon, lat

    # ---- public draw entrypoint ----
    def draw(
        self,
        bounds: Bounds,
        rings: List[Ring],
        points: List[PointFeature],
        user_markers: List[LngLat],
        in_detail: bool,
        detail_fill_override: Optional[str] = None,
    ) -> None:
        self.cur_bounds = bounds
        self._clear_canvas()

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        # Polygons
        for idx, ring in enumerate(rings):
            pts: List[float] = []
            for lon, lat in ring:
                x, y = self.project(lon, lat, w, h)
                pts.extend((x, y))
            if len(pts) >= 6:
                fill_color = (
                    detail_fill_override if (in_detail and detail_fill_override) else
                    (C.SECTOR_COLORS[idx % len(C.SECTOR_COLORS)] if hasattr(C, "SECTOR_COLORS") else "")
                )
                item = self.canvas.create_polygon(
                    *pts,
                    outline=C.OUTLINE_COLOR,
                    width=C.POLY_WIDTH,
                    fill=fill_color,
                    activefill=C.HOVER_FILL,
                    tags=("ring", f"ring-{idx}"),
                )
                self._poly_items.append(item)

        # Labels for main view
        if not in_detail and hasattr(C, "SECTOR_LABELS"):
            for idx, ring in enumerate(rings):
                fixed = getattr(C, "SECTOR_LABEL_POS", {}).get(idx) if hasattr(C, "SECTOR_LABEL_POS") else None
                if fixed is not None and isinstance(fixed, (list, tuple)) and len(fixed) == 2:
                    cx_lon, cy_lat = float(fixed[0]), float(fixed[1])
                else:
                    cx_lon, cy_lat = self._polygon_centroid_or_bbox(ring)
                x, y = self.project(cx_lon, cy_lat, w, h)
                label = C.SECTOR_LABELS.get(idx)
                if not label:
                    continue
                txt_item = self.canvas.create_text(
                    x, y,
                    text=label,
                    fill=getattr(C, "SECTOR_LABEL_COLOR", "#222"),
                    font=getattr(C, "SECTOR_LABEL_FONT", ("Arial", 24, "bold")),
                    state="disabled",
                    tags=("sector-label", f"sector-label-{idx}"),
                )
                self._label_items.append(txt_item)

        # Points (detail mode) or user markers (main)
        if in_detail:
            for idx, (lon, lat, site, _sector_id, _freq, _power) in enumerate(points):
                x, y = self.project(lon, lat, w, h)
                dot = self.canvas.create_oval(
                    x - C.POINT_RADIUS, y - C.POINT_RADIUS,
                    x + C.POINT_RADIUS, y + C.POINT_RADIUS,
                    fill=C.POINT_FILL, outline=C.POINT_OUTLINE, width=2,
                    tags=("point", f"point-{idx}"),
                )
                txt = self.canvas.create_text(
                    x + 8, y - 8, text=site,
                    anchor="sw", fill=C.POINT_LABEL_COLOR, font=C.POINT_FONT,
                    tags=("point", f"point-{idx}"),
                )
                self._fixed_point_items.extend([dot, txt])
        else:
            for lon, lat in user_markers:
                x, y = self.project(lon, lat, w, h)
                dot = self.canvas.create_oval(
                    x - C.MARKER_RADIUS, y - C.MARKER_RADIUS,
                    x + C.MARKER_RADIUS, y + C.MARKER_RADIUS,
                    fill=C.MARKER_COLOR, outline="",
                )
                lbl = self.canvas.create_text(
                    x + 8, y - 8,
                    text=f"{lon:.3f}, {lat:.3f}",
                    anchor="sw", fill=C.MARKER_LABEL_COLOR, font=C.MARKER_FONT,
                )
                self._marker_items.extend([dot, lbl])

        if self._logo_item is not None:
            self.canvas.tag_raise(self._logo_item)

    # ---- utils ----
    def _clear_canvas(self) -> None:
        logo_item = self._logo_item
        for item in self.canvas.find_all():
            if logo_item is not None and item == logo_item:
                continue
            self.canvas.delete(item)
        self._poly_items.clear()
        self._marker_items.clear()
        self._fixed_point_items.clear()
        self._label_items.clear()

    def _polygon_centroid_or_bbox(self, ring: Ring) -> Tuple[float, float]:
        if not ring:
            return 0.0, 0.0
        area_acc = cx_acc = cy_acc = 0.0
        n = len(ring)
        for i in range(n):
            x0, y0 = ring[i]
            x1, y1 = ring[(i + 1) % n]
            cross = x0 * y1 - x1 * y0
            area_acc += cross
            cx_acc += (x0 + x1) * cross
            cy_acc += (y0 + y1) * cross
        area = area_acc / 2.0
        if area == 0.0:
            lons = [lon for lon, _lat in ring]
            lats = [lat for _lon, lat in ring]
            return (min(lons) + max(lons)) / 2.0, (min(lats) + max(lats)) / 2.0
        cx = cx_acc / (6.0 * area)
        cy = cy_acc / (6.0 * area)
        return cx, cy

    # =========================
    # Corner logo (overlay API)
    # =========================
    def set_corner_logo(
        self,
        image_path: str,
        *,
        max_width: int = 120,
        max_height: int = 60,
        opacity: int = 255,
        margin: int = 10,
    ) -> None:
        """
        Load a logo and pin it to the top-right corner.
        - If Pillow is available: high-quality resize + optional opacity.
        - Else: Tk PhotoImage with integer subsample (fully opaque).
        """
        self._logo_max_w = int(max(1, max_width))
        self._logo_max_h = int(max(1, max_height))
        self._logo_margin = int(max(0, margin))
        self._logo_opacity = max(0, min(255, int(opacity)))

        try:
            if _PIL_AVAILABLE:
                img = Image.open(image_path).convert("RGBA")
                # Resize preserving aspect ratio within the bounds
                img.thumbnail((self._logo_max_w, self._logo_max_h), Image.LANCZOS)
                # Apply opacity by scaling alpha channel
                if self._logo_opacity < 255:
                    r, g, b, a = img.split()
                    a = a.point(lambda v: int(v * (self._logo_opacity / 255.0)))
                    img = Image.merge("RGBA", (r, g, b, a))
                self._logo_imgtk = ImageTk.PhotoImage(img)
            else:
                img = tk.PhotoImage(file=image_path)
                w0, h0 = img.width(), img.height()
                sx = (w0 + self._logo_max_w - 1) // self._logo_max_w
                sy = (h0 + self._logo_max_h - 1) // self._logo_max_h
                s = max(1, sx, sy)
                if s > 1:
                    img = img.subsample(s, s)
                self._logo_imgtk = img
        except Exception as e:
            print(f"Failed to load logo: {e}")
            self._logo_imgtk = None
            return

        if getattr(self, "_logo_item", None) is None:
            self._logo_item = self.canvas.create_image(
                0, 0, image=self._logo_imgtk, anchor="ne", tags=("corner-logo",)
            )
        else:
            self.canvas.itemconfig(self._logo_item, image=self._logo_imgtk)

        self._position_logo()
        self.canvas.tag_raise(self._logo_item)

    def _position_logo(self) -> None:
        if self._logo_item is None:
            return
        w = self.canvas.winfo_width()
        if w < 2:
            return
        x = w - self._logo_margin
        y = self._logo_margin
        self.canvas.coords(self._logo_item, x, y)

    def _on_canvas_resize(self, _evt: tk.Event) -> None:
        self._position_logo()
        if self._logo_item is not None:
            self.canvas.tag_raise(self._logo_item)

    def reposition_logo(self) -> None:
        self._position_logo()
        if self._logo_item is not None:
            self.canvas.tag_raise(self._logo_item)