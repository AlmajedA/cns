from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from .models import Bounds, Ring, PointFeature
from app.core.paths import config_path


# Optional: default GeoJSON file in /config
DEFAULT_GEOJSON = config_path("sa_combined.json")

# -------- GeoJSON iteration helpers --------
def iter_rings(geometry: Dict[str, Any]) -> Iterable[Ring]:
    """Yield rings from a GeoJSON Polygon; holes ignored for simplicity."""
    gtype = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if gtype == "Polygon" and isinstance(coords, list):
        for ring in coords:
            if isinstance(ring, list) and all(isinstance(pt, list) and len(pt) == 2 for pt in ring):
                yield [(float(pt[0]), float(pt[1])) for pt in ring]

def iter_points(feature: Dict[str, Any]) -> Iterable[PointFeature]:
    geom = feature.get("geometry", {})
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    props = feature.get("properties", {}) if isinstance(feature.get("properties"), dict) else {}
    site = props.get("site", "")
    sector_id = props.get("sectorId", "")
    freq = props.get("freq", {})
    power = props.get("power", {})
    if gtype == "Point" and isinstance(coords, list) and len(coords) == 2:
        lon, lat = float(coords[0]), float(coords[1])
        yield (lon, lat, site, sector_id, freq, power)

# -------- Loaders --------
def load_geo_from_json(path: Path | str) -> Tuple[List[Ring], List[PointFeature]]:
    """Load rings (Polygons) and points (Point) from a FeatureCollection."""
    path = Path(path)  # allow either Path or string
    with path.open("r", encoding="utf-8") as f:
        gj = json.load(f)

    rings: List[Ring] = []
    points: List[PointFeature] = []
    features = gj.get("features", [])
    for feat in features:
        geom = feat.get("geometry", {})
        for ring in iter_rings(geom):
            rings.append(ring)
        for p in iter_points(feat):
            points.append(p)
    return rings, points

# Optional convenience: load the default combined file from /config
def load_default_geo() -> Tuple[List[Ring], List[PointFeature]]:
    return load_geo_from_json(DEFAULT_GEOJSON)
# -------- Bounds & padding --------
def compute_bounds(rings: List[Ring]) -> Bounds:
    if not rings:
        raise RuntimeError("No polygon coordinates found in the GeoJSON.")
    lons = [lon for ring in rings for (lon, _lat) in ring]
    lats = [lat for ring in rings for (_lon, lat) in ring]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    if max_lon == min_lon:
        max_lon += 1e-9
    if max_lat == min_lat:
        max_lat += 1e-9
    return Bounds(min_lon, max_lon, min_lat, max_lat)

def ring_bounds(ring: Ring) -> Bounds:
    lons = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    mn_lon, mx_lon = min(lons), max(lons)
    mn_lat, mx_lat = min(lats), max(lats)
    if mx_lon == mn_lon:
        mx_lon += 1e-9
    if mx_lat == mn_lat:
        mx_lat += 1e-9
    return Bounds(mn_lon, mx_lon, mn_lat, mx_lat)

def pad_bounds(b: Bounds, ratio: float) -> Bounds:
    w = b.max_lon - b.min_lon
    h = b.max_lat - b.min_lat
    dx = w * ratio
    dy = h * ratio
    return Bounds(b.min_lon - dx, b.max_lon + dx, b.min_lat - dy, b.max_lat + dy)