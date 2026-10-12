"""Tesla plugin for FiestaBoard supporting Tessie, TeslaMate, and Tesla Fleet API."""

from __future__ import annotations

import datetime
import logging
from typing import Any, Dict, List

try:
    from src.plugins.base import PluginBase, PluginResult, TriggerResult
except ImportError:
    # Standalone compatibility fallback
    from dataclasses import dataclass

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

    class PluginBase:  # type: ignore[no-redef]
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


from .formatters import (
    format_battery_badge,
    format_battery_bar_ascii,
    format_battery_bar_color,
    format_car_type,
    format_distance,
    format_odometer,
    format_speed,
    format_state,
    format_temp,
    format_time_remaining,
)
from .providers import (
    BaseTeslaProvider,
    DemoProvider,
    ProviderError,
    TeslaFleetApiProvider,
    TeslaMateProvider,
    TessieProvider,
)

logger = logging.getLogger(__name__)


class TeslaPlugin(PluginBase):
    """Tesla telemetry plugin for FiestaBoard."""

    @property
    def plugin_id(self) -> str:
        return "tesla"

    def _get_provider(self, cfg: Dict[str, Any]) -> BaseTeslaProvider:
        """Instantiate the appropriate telemetry provider based on configuration."""
        provider_name = (cfg.get("provider") or "").lower().strip()
        demo_mode = bool(cfg.get("demo_mode", False))

        if demo_mode or provider_name == "demo":
            return DemoProvider()

        if provider_name == "teslamate" or bool(cfg.get("teslamate_url")):
            car_id_raw = cfg.get("car_id", 1)
            try:
                car_id = int(car_id_raw)
            except (ValueError, TypeError):
                car_id = 1
            return TeslaMateProvider(
                base_url=cfg.get("teslamate_url", ""),
                api_key=cfg.get("teslamate_api_key"),
                car_id=car_id,
            )

        if provider_name == "fleet_api":
            return TeslaFleetApiProvider(
                access_token=cfg.get("api_key", ""),
                region=cfg.get("fleet_region", "eu"),
                custom_endpoint=cfg.get("fleet_custom_endpoint"),
                vin=cfg.get("vin"),
            )

        # Default: Tessie
        return TessieProvider(
            api_key=cfg.get("api_key", ""),
            vin=cfg.get("vin", ""),
        )

    def fetch_data(self) -> PluginResult:
        """Fetch Tesla vehicle telemetry and return formatted variables."""
        cfg = self.config or {}
        unit_system = cfg.get("unit_system", "metric")

        try:
            provider = self._get_provider(cfg)
            raw = provider.get_vehicle_data()

            # Extract sub-states safely
            charge = raw.get("charge_state", {}) or {}
            climate = raw.get("climate_state", {}) or {}
            vehicle = raw.get("vehicle_state", {}) or {}
            drive = raw.get("drive_state", {}) or {}
            vehicle_config = raw.get("vehicle_config", {}) or {}

            # Battery & charging values
            battery_level = charge.get("battery_level")
            battery_level_int = int(battery_level) if battery_level is not None else 0
            battery_pct = f"{battery_level_int}%" if battery_level is not None else "--"
            battery_range = format_distance(charge.get("battery_range"), unit_system=unit_system)

            charging_state = str(charge.get("charging_state") or "Disconnected")
            is_charging = charging_state.lower() == "charging"
            charger_power_kw = charge.get("charger_power", 0) or 0
            charger_power = f"{float(charger_power_kw):.1f} kW" if is_charging else "0 kW"
            charge_rate = format_speed(charge.get("charge_rate"), unit_system=unit_system)
            time_to_full = format_time_remaining(charge.get("time_to_full_charge"))

            charge_limit_val = charge.get("charge_limit_soc")
            charge_limit = f"{int(charge_limit_val)}%" if charge_limit_val is not None else "--"

            # Charging summary string
            if is_charging:
                time_part = f" ({time_to_full} to {charge_limit})" if time_to_full != "--" else ""
                charging_summary = f"{charger_power}{time_part}"
            else:
                charging_summary = charging_state

            # Vehicle status
            raw_state = raw.get("state")
            shift_state = str(drive.get("shift_state") or "P")
            state_str = format_state(raw_state, shift_state=shift_state, is_charging=is_charging)

            locked_val = vehicle.get("locked")
            locked_str = "Locked" if locked_val else "Unlocked" if locked_val is not None else "--"

            sentry_val = vehicle.get("sentry_mode")
            sentry_str = "ON" if sentry_val else "OFF" if sentry_val is not None else "--"

            # Model & Car Type
            car_type_str = format_car_type(
                vehicle_config.get("car_type"),
                vehicle_config.get("trim_badging"),
            )
            display_name = raw.get("display_name") or car_type_str or "Tesla"

            # Climate
            inside_temp = format_temp(climate.get("inside_temp"), unit_system=unit_system)
            outside_temp = format_temp(climate.get("outside_temp"), unit_system=unit_system)
            climate_on = "ON" if climate.get("is_climate_on") else "OFF"

            # Speed & Odometer
            speed = format_speed(drive.get("speed"), unit_system=unit_system)
            odometer = format_odometer(vehicle.get("odometer"), unit_system=unit_system)

            # Split-flap bars & badges
            battery_bar_ascii = format_battery_bar_ascii(battery_level_int)
            battery_bar_color = format_battery_bar_color(battery_level_int)
            battery_badge = format_battery_badge(battery_level_int, is_charging=is_charging)

            # Timestamp
            last_updated = datetime.datetime.now().strftime("%H:%M")

            variables = {
                "vehicle_name": display_name,
                "vin": raw.get("vin", cfg.get("vin", "")),
                "car_type": car_type_str,
                "state": state_str,
                "locked": locked_str,
                "sentry_mode": sentry_str,
                "odometer": odometer,
                "battery_level": battery_level_int,
                "battery_pct": battery_pct,
                "battery_range": battery_range,
                "battery_bar_ascii": battery_bar_ascii,
                "battery_bar_color": battery_bar_color,
                "battery_badge": battery_badge,
                "is_charging": "YES" if is_charging else "NO",
                "charging_state": charging_state,
                "charger_power": charger_power,
                "charge_rate": charge_rate,
                "time_to_full": time_to_full,
                "charge_limit": charge_limit,
                "charging_summary": charging_summary,
                "inside_temp": inside_temp,
                "outside_temp": outside_temp,
                "climate_on": climate_on,
                "speed": speed,
                "shift_state": shift_state,
                "last_updated": last_updated,
            }

            return PluginResult(available=True, data=variables)

        except ProviderError as e:
            logger.warning("Provider error for Tesla plugin: %s", e)
            return PluginResult(available=False, error=str(e))
        except Exception as e:
            logger.exception("Unexpected error fetching Tesla data")
            return PluginResult(available=False, error=f"Unexpected error: {e}")

    def check_triggers(self) -> List[TriggerResult]:
        """Check for high-priority notification events (low battery, charging finished)."""
        triggers: List[TriggerResult] = []
        result = self.fetch_data()
        if not result.available or not result.data:
            return triggers

        data = result.data
        battery_level = data.get("battery_level", 100)
        is_charging = data.get("is_charging") == "YES"
        charging_state = (data.get("charging_state") or "").lower()
        vehicle_name = data.get("vehicle_name", "Tesla")

        # 1. Low Battery Trigger (< 20% and not currently charging)
        if battery_level < 20 and not is_charging:
            triggers.append(
                TriggerResult(
                    triggered=True,
                    trigger_id=f"tesla_low_battery_{battery_level}",
                    message=f"{vehicle_name} battery low: {battery_level}%",
                    priority=2,
                    duration_seconds=60,
                    data=data,
                )
            )

        # 2. Charging Completed Trigger
        if charging_state == "complete":
            triggers.append(
                TriggerResult(
                    triggered=True,
                    trigger_id="tesla_charging_complete",
                    message=f"{vehicle_name} charging complete: {battery_level}%",
                    priority=1,
                    duration_seconds=45,
                    data=data,
                )
            )

        return triggers

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration settings."""
        errors: List[str] = []
        if not config:
            return errors

        demo_mode = config.get("demo_mode", False)
        provider = (config.get("provider") or "").lower().strip()

        if not demo_mode and provider != "demo":
            if provider == "teslamate":
                if not (config.get("teslamate_url") or "").strip():
                    errors.append("TeslaMate base URL is required when using the TeslaMate provider.")
            else:
                # Tessie or Fleet API
                api_key = (config.get("api_key") or "").strip()
                if not api_key:
                    errors.append("API Token is required for Tessie and Tesla Fleet API unless Demo Mode is enabled.")

        refresh_seconds = config.get("refresh_seconds")
        if refresh_seconds is not None:
            try:
                val = int(refresh_seconds)
                if val < 60:
                    errors.append("Refresh interval must be at least 60 seconds.")
            except (ValueError, TypeError):
                errors.append("Refresh interval must be an integer.")

        unit_system = config.get("unit_system")
        if unit_system and unit_system not in ("metric", "imperial"):
            errors.append("Unit system must be either 'metric' or 'imperial'.")

        return errors

    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass
