"""Unit tests for the FiestaBoard TeslaPlugin."""

import pytest
import responses
from plugins.tesla import TeslaPlugin
from plugins.tesla.providers.tessie import TESSIE_API_BASE


def test_plugin_properties(manifest_dict):
    plugin = TeslaPlugin(manifest=manifest_dict)
    assert plugin.plugin_id == "tesla"


def test_validate_config(manifest_dict):
    plugin = TeslaPlugin(manifest=manifest_dict)

    # Valid config with api_key
    assert plugin.validate_config({"api_key": "token_123", "refresh_seconds": 300}) == []

    # Valid config with demo_mode
    assert plugin.validate_config({"demo_mode": True}) == []

    # Valid config with TeslaMate
    assert plugin.validate_config({"provider": "teslamate", "teslamate_url": "http://192.168.1.50:8080"}) == []

    # Invalid: missing api_key and demo_mode is False
    errors = plugin.validate_config({"demo_mode": False})
    assert any("API Token is required" in err for err in errors)

    # Invalid: TeslaMate without URL
    errors = plugin.validate_config({"provider": "teslamate", "teslamate_url": ""})
    assert any("TeslaMate base URL is required" in err for err in errors)

    # Invalid: refresh_seconds too low
    errors = plugin.validate_config({"demo_mode": True, "refresh_seconds": 30})
    assert any("at least 60 seconds" in err for err in errors)

    # Invalid: unit_system
    errors = plugin.validate_config({"demo_mode": True, "unit_system": "kelvin"})
    assert any("Unit system must be" in err for err in errors)


def test_fetch_data_demo_mode(manifest_dict):
    plugin = TeslaPlugin(manifest=manifest_dict)
    plugin.config = {"demo_mode": True, "unit_system": "metric"}

    result = plugin.fetch_data()
    assert result.available is True
    assert result.error is None
    assert result.data is not None

    data = result.data
    assert data["vehicle_name"] == "Model Y"
    assert data["battery_level"] == 82
    assert data["battery_pct"] == "82%"
    assert "km" in data["battery_range"]
    assert data["state"] == "Asleep"
    assert data["locked"] == "Locked"
    assert data["sentry_mode"] == "OFF"
    assert data["is_charging"] == "NO"
    assert "{66}" in data["battery_bar_color"]


def test_fetch_data_manifest_variable_completeness(manifest_dict):
    """Ensure all variables declared in manifest.json are provided by fetch_data."""
    plugin = TeslaPlugin(manifest=manifest_dict)
    plugin.config = {"demo_mode": True}

    result = plugin.fetch_data()
    assert result.available is True
    manifest_vars = manifest_dict["variables"]["simple"].keys()

    for var_key in manifest_vars:
        assert var_key in result.data, f"Variable '{var_key}' declared in manifest is missing from fetch_data!"


@responses.activate
def test_fetch_data_charging_state(manifest_dict, sample_charging_vehicle_state):
    vin = "5YJ3E1EB8NF123456"
    responses.add(
        responses.GET,
        f"{TESSIE_API_BASE}/{vin}/state?use_cache=true",
        json=sample_charging_vehicle_state,
        status=200,
    )

    plugin = TeslaPlugin(manifest=manifest_dict)
    plugin.config = {
        "api_key": "test_token",
        "vin": vin,
        "unit_system": "metric",
    }

    result = plugin.fetch_data()
    assert result.available is True
    data = result.data

    assert data["is_charging"] == "YES"
    assert data["charging_state"] == "Charging"
    assert data["charger_power"] == "11.0 kW"
    assert data["time_to_full"] == "1h 30m"
    assert data["climate_on"] == "ON"
    assert data["sentry_mode"] == "ON"


def test_check_triggers_low_battery(manifest_dict, monkeypatch):
    plugin = TeslaPlugin(manifest=manifest_dict)
    plugin.config = {"demo_mode": True}

    low_bat_data = {
        "vehicle_name": "Model Y",
        "battery_level": 12,
        "is_charging": "NO",
        "charging_state": "Disconnected",
    }

    from plugins.tesla import PluginResult

    monkeypatch.setattr(plugin, "fetch_data", lambda: PluginResult(available=True, data=low_bat_data))

    triggers = plugin.check_triggers()
    assert len(triggers) == 1
    assert triggers[0].triggered is True
    assert "battery low: 12%" in triggers[0].message


def test_check_triggers_charging_complete(manifest_dict, monkeypatch):
    plugin = TeslaPlugin(manifest=manifest_dict)
    plugin.config = {"demo_mode": True}

    complete_data = {
        "vehicle_name": "Model Y",
        "battery_level": 80,
        "is_charging": "NO",
        "charging_state": "Complete",
    }

    from plugins.tesla import PluginResult

    monkeypatch.setattr(plugin, "fetch_data", lambda: PluginResult(available=True, data=complete_data))

    triggers = plugin.check_triggers()
    assert len(triggers) == 1
    assert triggers[0].triggered is True
    assert "charging complete" in triggers[0].message


def test_manifest_previews_and_teaser_compliance(manifest_dict):
    """Ensure manifest teaser and previews strictly comply with FiestaBoard dimensional constraints."""
    import re

    color_marker_re = re.compile(r"\{([0-9]{1,2}|[a-zA-Z_]+)\}")
    valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890 !@#$()+-&=;: '\"%,./?")

    def count_tiles(text: str) -> int:
        tiles = 0
        pos = 0
        while pos < len(text):
            m = color_marker_re.match(text, pos)
            if m:
                tiles += 1
                pos = m.end()
                continue
            tiles += 1
            pos += 1
        return tiles

    # 1. Teaser check: max 15 tiles (Note width)
    teaser = manifest_dict.get("teaser", "")
    assert teaser, "Teaser is required"
    assert count_tiles(teaser) <= 15, f"Teaser exceeds 15 tiles: {count_tiles(teaser)}"

    # 2. Previews check: Flagship (22 cols, 6 rows), Note (15 cols, 3 rows)
    previews = manifest_dict.get("previews", [])
    assert previews, "Previews are required"

    dims = {"flagship": (6, 22), "note": (3, 15)}
    for p_idx, preview in enumerate(previews):
        device = preview.get("device_type")
        assert device in dims, f"Unknown device_type: {device}"
        max_rows, max_cols = dims[device]
        rows = preview.get("rows", [])
        assert len(rows) <= max_rows, f"Preview {p_idx} has too many rows ({len(rows)} > {max_rows})"
        for r_idx, row in enumerate(rows):
            width = count_tiles(row)
            assert width <= max_cols, f"Preview {p_idx} row {r_idx} exceeds {max_cols} tiles: {width} -> '{row}'"
            pos = 0
            while pos < len(row):
                m = color_marker_re.match(row, pos)
                if m:
                    pos = m.end()
                    continue
                c = row[pos].upper()
                assert c in valid_chars, f"Unmappable character '{c}' in preview {p_idx} row {r_idx}"
                pos += 1

