"""Indexes 3D assets for the hologram renderer."""

from pathlib import Path
from typing import Dict, Iterable, Optional, Set


class ModelRegistry:
    """Scans the assets folder and keeps a simple catalog."""

    def __init__(self, asset_root: Optional[Path] = None, extensions: Optional[Iterable[str]] = None):
        self.extensions: Set[str] = set(ext.lower() for ext in (extensions or {".glb", ".gltf", ".obj"}))
        self.asset_root = self._pick_root(asset_root)
        self.catalog: Dict[str, Path] = {}
        self.refresh()

    def _pick_root(self, asset_root: Optional[Path]) -> Path:
        if asset_root:
            return Path(asset_root)

        module_root = Path(__file__).resolve().parents[2]
        repo_root = Path(__file__).resolve().parents[3]
        candidates = [
            module_root / "assets",
            repo_root / "reality" / "assets",
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        return candidates[0]

    def refresh(self) -> None:
        """Re-scan the asset directory and update the catalog."""
        self.catalog.clear()
        if not self.asset_root.exists():
            return

        for file_path in self.asset_root.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in self.extensions:
                continue

            key = file_path.stem
            self.catalog[key] = file_path

    def resolve(self, key: str) -> Optional[Path]:
        """Get a path for a registered model id."""
        return self.catalog.get(key)

    def list_available(self):
        """Return a sorted list of registered model ids."""
        return sorted(self.catalog.keys())

