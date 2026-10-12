"""Pytest fixtures and environment configuration for Tesla plugin."""

from dataclasses import dataclass
import json
from pathlib import Path
import sys
import types
from typing import Any
import pytest

# Ensure plugin root and plugins/ are on sys.path
PLUGIN_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))
sys.path.insert(0, str(PLUGIN_ROOT / "plugins"))

# Mock src.plugins.base for standalone testing if not running inside FiestaBoard
if "src.plugins.base" not in sys.modules:
    src_mod = types.ModuleType("src")
    src_plugins_mod = types.ModuleType("src.plugins")
    src_plugins_base_mod = types.ModuleType("src.plugins.base")

    @dataclass
    class PluginResult:
        available: bool
        data: dict[str, Any] | None = None
        error: str | None = None
        formatted_lines: list[str] | None = None

    @dataclass
    class TriggerResult:
        triggered: bool
        trigger_id: str = ""
        message: str | None = None
        formatted_lines: list[str] | None = None
        priority: int = 0
        duration_seconds: int = 30
        data: dict[str, Any] | None = None

    class PluginBase:
        def __init__(self, manifest: dict[str, Any]):
            self._manifest = manifest
            self._config: dict[str, Any] = {}
            self._enabled = False

        @property
        def config(self) -> dict[str, Any]:
            return self._config

        @config.setter
        def config(self, value: dict[str, Any]) -> None:
            self._config = value

        @property
        def enabled(self) -> bool:
            return self._enabled

        @enabled.setter
        def enabled(self, value: bool) -> None:
            self._enabled = value

        def cleanup(self) -> None:
            pass

    src_plugins_base_mod.PluginBase = PluginBase
    src_plugins_base_mod.PluginResult = PluginResult
    src_plugins_base_mod.TriggerResult = TriggerResult

    sys.modules["src"] = src_mod
    sys.modules["src.plugins"] = src_plugins_mod
    sys.modules["src.plugins.base"] = src_plugins_base_mod


@pytest.fixture
def manifest_dict():
    """Load manifest.json from plugin root."""
    manifest_path = PLUGIN_ROOT / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_tessie_vehicle_state():
    """Sample Tessie state for a Model Y."""
    return {
        "vin": "5YJ3E1EB8NF123456",
        "display_name": "Starship",
        "state": "asleep",
        "charge_state": {
            "battery_level": 75,
            "battery_range": 240.5,
            "charging_state": "Disconnected",
            "charger_power": 0,
            "charge_rate": 0.0,
            "time_to_full_charge": 0.0,
            "charge_limit_soc": 80,
        },
        "climate_state": {
            "inside_temp": 20.5,
            "outside_temp": 14.0,
            "is_climate_on": False,
        },
        "vehicle_state": {
            "locked": True,
            "sentry_mode": False,
            "odometer": 15000.0,
        },
        "drive_state": {
            "shift_state": "P",
            "speed": 0,
            "heading": 90,
        },
        "vehicle_config": {
            "car_type": "modely",
            "trim_badging": "longrange",
        },
    }


@pytest.fixture
def sample_charging_vehicle_state():
    """Sample Tessie state for a vehicle that is actively charging."""
    return {
        "vin": "5YJ3E1EB8NF123456",
        "display_name": "Starship",
        "state": "online",
        "charge_state": {
            "battery_level": 55,
            "battery_range": 170.0,
            "charging_state": "Charging",
            "charger_power": 11.0,
            "charge_rate": 65.0,
            "time_to_full_charge": 1.5,
            "charge_limit_soc": 80,
        },
        "climate_state": {
            "inside_temp": 21.0,
            "outside_temp": 12.0,
            "is_climate_on": True,
        },
        "vehicle_state": {
            "locked": True,
            "sentry_mode": True,
            "odometer": 15000.0,
        },
        "drive_state": {
            "shift_state": "P",
            "speed": 0,
            "heading": 90,
        },
        "vehicle_config": {
            "car_type": "modely",
            "trim_badging": "longrange",
        },
    }
