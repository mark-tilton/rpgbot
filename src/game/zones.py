import yaml
from typing import List
from dataclasses import dataclass

@dataclass
class ZoneConnection:
    zone_id: int
    frequency: float

@dataclass
class Zone:
    zone_id: int
    name: str
    description: str
    connections: List[ZoneConnection]

def load_zones() -> List[Zone]:
    with open("data/zones.yaml", mode="r") as f:
        zone_list_yaml = yaml.safe_load(f)
    zones = []
    for zone_yaml in zone_list_yaml:
        zone_id = zone_yaml["zone"]
        name = zone_yaml["name"].lower()
        description = zone_yaml.get("description", "")
        connections = []
        for connection_yaml in zone_yaml.get("connections", []):
            con_zone_id = connection_yaml["zone"]
            frequency = connection_yaml["frequency"]
            connection = ZoneConnection(con_zone_id, frequency)
            connections.append(connection)
        zone = Zone(zone_id, name, description, connections)
        zones.append(zones)
    zones.sort(key=lambda step: step.zone_id)
    return zones

ZONES = load_zones()