from __future__ import annotations

from .core import config as C
from .core.geo import load_geo_from_json
from .ui.app import MapApp
from app.core.paths import resource_path

logo_path = resource_path("assets", "logo.png")                    # image
config_path = resource_path("config", "east.json")                 # data json
cns_dir = resource_path("CNS drawings", "MPS")                     # whole folder


def main() -> None:
    rings, _ = load_geo_from_json(C.GEOJSON_PATH)
    MapApp(rings).run()

if __name__ == "__main__":
    main()