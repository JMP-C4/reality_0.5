"""Loads 3D assets and prepares scene metadata."""

from pathlib import Path
from typing import Dict, Optional

from ..services.model_registry import ModelRegistry
from ..scenes.catalog import get_scene_config


class SceneManager:
    """Tracks available assets and basic scene state."""

    def __init__(self, asset_root: Optional[Path] = None):
        self.registry = ModelRegistry(asset_root=asset_root)

    def load(self, scene_id: str) -> Dict[str, object]:
        """Resolve a scene id to an asset path and return scene metadata."""
        config = get_scene_config(scene_id)
        candidate_ids = [config.get("asset_id") or scene_id, scene_id]

        asset_path = None
        asset_id = None
        for candidate in candidate_ids:
            asset_path = self.registry.resolve(candidate)
            if asset_path:
                asset_id = candidate
                break

        if asset_path is None:
            # Re-scan in case new assets were copied after startup.
            self.registry.refresh()
            for candidate in candidate_ids:
                asset_path = self.registry.resolve(candidate)
                if asset_path:
                    asset_id = candidate
                    break

        return {"id": scene_id, "asset_id": asset_id, "asset": asset_path, "config": config}

    def list_available(self):
        return self.registry.list_available()
