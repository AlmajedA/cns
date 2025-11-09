# app/core/paths.py
from pathlib import Path
import sys

def project_root() -> Path:
    """
    When bundled with PyInstaller, files are unpacked under sys._MEIPASS.
    In dev, we want the repository root: .../saudi-arabia-map
    """
    if hasattr(sys, "_MEIPASS"):
        # In a PyInstaller .app, _MEIPASS is the temp bundle root
        return Path(sys._MEIPASS)
    # This file lives in app/core/, so parents[2] is the repo root
    return Path(__file__).resolve().parents[2]

def resource_path(*parts) -> Path:
    return project_root().joinpath(*parts)
