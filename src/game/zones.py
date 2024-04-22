from collections.abc import Mapping
from dataclasses import dataclass

import yaml


@dataclass
class Zone:
    zone_id: str
    name: str
    description: str
    public: bool


def load_zones() -> Mapping[str, Zone]:
    with open("data/zones.yaml", mode="r") as f:
        zone_list_yaml = yaml.safe_load(f)
    zones: dict[str, Zone] = {}
    for zone_yaml in zone_list_yaml:
        zone_id: str = zone_yaml["zone"]
        name: str = zone_yaml.get("name", zone_id.replace("_", " ")).lower()
        description: str = zone_yaml.get("description", "")
        public: bool = zone_yaml.get("public", False)
        zone = Zone(zone_id, name, description, public)
        zones[zone_id] = zone
    return zones


ZONES = load_zones()
