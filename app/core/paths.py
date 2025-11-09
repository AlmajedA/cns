# app/core/paths.py
from __future__ import annotations
from pathlib import Path
import sys
import json

def _project_root_dev() -> Path:
    # app/core/paths.py -> app/core -> app -> (project root)
    return Path(__file__).resolve().parents[2]

def _frozen_base() -> Path:
    # PyInstaller: onefile uses _MEIPASS; onedir puts files next to the exe
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(sys.executable).resolve().parent

def runtime_root() -> Path:
    return _frozen_base() if getattr(sys, "frozen", False) else _project_root_dev()

def app_root() -> Path:
    return runtime_root() / "app"

def config_root() -> Path:
    return runtime_root() / "config"

def assets_root() -> Path:
    return runtime_root() / "assets"

def drawings_root() -> Path:
    # Folder name has a space — keep it exact
    return runtime_root() / "CNS drawings"

# Convenience joiners
def app_path(*parts: str) -> Path:      return app_root().joinpath(*parts)
def config_path(*parts: str) -> Path:   return config_root().joinpath(*parts)
def assets_path(*parts: str) -> Path:   return assets_root().joinpath(*parts)
def drawings_path(*parts: str) -> Path: return drawings_root().joinpath(*parts)

# Tiny helpers if you read JSON configs
def load_config(name: str):
    """e.g., load_config('sa_org.json')"""
    return json.loads(config_path(name).read_text(encoding="utf-8"))
