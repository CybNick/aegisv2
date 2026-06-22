"""Configuration storage for Aegis modules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.storage.graph_store import StorageLayout, atomic_write_text

class ConfigStore:
    """Manages separate persistence of configuration and runtime state."""

    def __init__(self, layout: StorageLayout):
        self._layout = layout
        self._connectors_dir = self._layout.root / "connectors"

    @property
    def connectors_dir(self) -> Path:
        self._connectors_dir.mkdir(parents=True, exist_ok=True)
        return self._connectors_dir

    @property
    def config_json(self) -> Path:
        return self.connectors_dir / "config.json"

    @property
    def state_json(self) -> Path:
        return self.connectors_dir / "state.json"

    def load_config(self) -> dict[str, Any]:
        """Load connector configurations."""
        if not self.config_json.exists():
            return {"connectors": []}
        try:
            return json.loads(self.config_json.read_text(encoding="utf-8"))
        except Exception:
            return {"connectors": []}

    def save_config(self, data: dict[str, Any]) -> None:
        """Atomically save connector configurations."""
        atomic_write_text(self.config_json, json.dumps(data, indent=2))

    def load_state(self) -> dict[str, Any]:
        """Load runtime states."""
        if not self.state_json.exists():
            return {}
        try:
            return json.loads(self.state_json.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def save_state(self, data: dict[str, Any]) -> None:
        """Atomically save runtime states."""
        atomic_write_text(self.state_json, json.dumps(data, indent=2))
