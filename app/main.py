from __future__ import annotations

from pathlib import Path
from tkinter import Tk, messagebox

from .core import config as C
from .core.geo import load_geo_from_json
from .ui.app import MapApp


def _error_box(title: str, msg: str) -> None:
    # Show an error dialog even if the app was built with --noconsole
    root = Tk()
    root.withdraw()
    try:
        messagebox.showerror(title, msg)
    finally:
        root.destroy()


def main() -> None:
    # Ensure the default GeoJSON exists before launching UI
    geo_path = Path(C.GEOJSON_PATH)
    if not geo_path.exists():
        _error_box("Missing data", f"GeoJSON not found:\n{geo_path}")
        return

    try:
        rings, _ = load_geo_from_json(geo_path)
    except Exception as e:
        _error_box("Failed to load map", f"Could not read\n{geo_path}\n\n{e}")
        return

    MapApp(rings).run()


if __name__ == "__main__":
    main()
