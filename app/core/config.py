from __future__ import annotations
from pathlib import Path
from app.core.paths import resource_path

logo_path = resource_path("assets", "logo.png")                    # image
config_path = resource_path("config", "east.json")                 # data json
cns_dir = resource_path("CNS drawings", "MPS")                     # whole folder

# --------------------------------------------------
# Paths (resolve relative to the project root)
# --------------------------------------------------
APP_DIR = Path(__file__).resolve().parents[1]   # .../app
PROJECT_ROOT = APP_DIR.parent                    # repo root

DATA_DIR = PROJECT_ROOT / "config"
DRAWINGS_DIR = PROJECT_ROOT / "CNS drawings"
ASSETS_DIR = PROJECT_ROOT / "assets"

GEOJSON_PATH = DATA_DIR / "sa_combined.json"

DETAIL_JSON_FOR_RING: dict[int, Path] = {
    0: DATA_DIR / "east.json",
    1: DATA_DIR / "center.json",
    2: DATA_DIR / "north.json",
    3: DATA_DIR / "south.json",
    4: DATA_DIR / "west.json",
}

# --------------------------------------------------
# UI constants
# --------------------------------------------------
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
PADDING = 24

HOVER_FILL = "#0B3D91" #"#4338CA"
OUTLINE_COLOR = "#0A5"
POLY_WIDTH = 2

BACKGROUND = "#8CD6F2"

SECTOR_COLORS = [
    "#FFFACD",  # light yellow
    "#b2df8a",  # light green
    "#fb9a99",  # light red
    "#fdbf6f",  # light orange
    "#cab2d6",  # light purple
    "#1f78b4",  # blue
    "#33a02c",  # green
    "#e31a1c",  # red
    "#ff7f00",  # orange
    "#ffff99",  # light yellow
]

SECTOR_LABELS: dict[int, str] = {
    0: "East",
    1: "Central",
    2: "North",
    3: "South",
    4: "West",
}

SECTOR_LABEL_COLOR = "#222"
SECTOR_LABEL_FONT = ("Arial", 24, "bold")
SECTOR_LABEL_POS: dict[int, tuple[float, float]] = {
    2: (40.0, 30.0),  # example fixed position for North
}

POINT_RADIUS = 10
POINT_FILL = "#1f77b4"
POINT_OUTLINE = "white"
POINT_LABEL_COLOR = "#111"
POINT_FONT = ("Arial", 16, "bold")

MARKER_COLOR = "#d33"
MARKER_LABEL_COLOR = "#444"
MARKER_RADIUS = 4
MARKER_FONT = ("Arial", 9)

TITLE = "Saudi Arabia Outline (Tkinter)"

ANIM_STEPS = 18
ANIM_TOTAL_MS = 280
TARGET_PADDING_RATIO = 0.06