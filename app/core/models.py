from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple

# Lightweight, focused shared types
LngLat = Tuple[float, float]
Ring = List[LngLat]
# (lon, lat, site, sector_id, freq_dict, power_dict)
PointFeature = Tuple[float, float, str, str, dict, dict]


@dataclass(frozen=True)
class Bounds:
    min_lon: float
    max_lon: float
    min_lat: float
    max_lat: float

    def lerp(self, other: "Bounds", t: float) -> "Bounds":
        return Bounds(
            min_lon=self.min_lon + (other.min_lon - self.min_lon) * t,
            max_lon=self.max_lon + (other.max_lon - self.max_lon) * t,
            min_lat=self.min_lat + (other.min_lat - self.min_lat) * t,
            max_lat=self.max_lat + (other.max_lat - self.max_lat) * t,
        )
