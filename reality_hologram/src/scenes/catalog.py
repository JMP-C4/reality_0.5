"""Lightweight catalog of preset scenes."""

DEFAULT_SCENES = {
    "default": {"asset_id": "ground_terrain_part_1", "notes": "Placeholder terrain sample."},
    "machinery": {"asset_id": "excavator", "notes": "Example heavy machinery model."},
    "truck": {"asset_id": "dump_truck", "notes": "Hauling vehicle example."},
}


def get_scene_config(name: str) -> dict:
    """Return a simple config dict for a scene id."""
    return DEFAULT_SCENES.get(name, {"asset_id": name, "notes": "Custom scene id."})

