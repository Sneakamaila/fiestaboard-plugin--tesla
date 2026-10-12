"""TeslaMate / TeslaMateApi data provider for self-hosted setups."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import requests

from .base import BaseTeslaProvider, ProviderError

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 10
KM_TO_MILES = 1.0 / 1.609344


class TeslaMateProvider(BaseTeslaProvider):
    """Fetches telemetry from a self-hosted TeslaMateApi instance.

    Works directly with https://github.com/tobiasehlert/teslamateapi.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        car_id: int = 1,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = (base_url or "").strip().rstrip("/")
        self.api_key = (api_key or "").strip()
        self.car_id = car_id
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "FiestaBoard-Tesla-Plugin/0.2.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def get_vehicle_data(self) -> Dict[str, Any]:
        if not self.base_url:
            raise ProviderError("TeslaMate API base URL is not configured.")

        # 1. Fetch live car status from /api/v1/cars/:CarID/status
        status_url = f"{self.base_url}/api/v1/cars/{self.car_id}/status"
        try:
            resp = requests.get(status_url, headers=self._headers(), timeout=self.timeout)
        except requests.RequestException as e:
            logger.error("Failed connecting to TeslaMateApi at %s: %s", status_url, e)
            raise ProviderError(f"Network error connecting to TeslaMateApi: {e}") from e

        if resp.status_code == 401 or resp.status_code == 403:
            raise ProviderError("Authentication failed for TeslaMateApi (Check API Key).")
        if resp.status_code == 404:
            raise ProviderError(f"Car ID {self.car_id} not found on TeslaMateApi (404).")
        if not resp.ok:
            raise ProviderError(f"TeslaMateApi error ({resp.status_code}): {resp.text}")

        json_data = resp.json()
        raw_status = (json_data.get("data", {}) or {}).get("status", {}) or {}

        # 2. Extract nested sections
        battery = raw_status.get("battery_details", {}) or {}
        charging = raw_status.get("charging_details", {}) or {}
        climate = raw_status.get("climate_details", {}) or {}
        drive = raw_status.get("drive_details", {}) or {}
        vehicle = raw_status.get("vehicle_state", {}) or {}
        car_info = raw_status.get("car_details", {}) or {}

        # Range and Odometer in TeslaMate are in km; convert to miles for universal formatting
        range_km = battery.get("rated_battery_range") or battery.get("est_battery_range")
        range_miles = float(range_km) * KM_TO_MILES if range_km is not None else None

        odo_km = vehicle.get("odometer")
        odo_miles = float(odo_km) * KM_TO_MILES if odo_km is not None else None

        # Charging status
        is_charging = bool(charging.get("charging_state") == "Charging" or charging.get("charger_power", 0) > 0)
        charging_state = charging.get("charging_state")
        if not charging_state:
            charging_state = "Charging" if is_charging else "Disconnected"

        # Car model
        model_str = car_info.get("model", "")
        car_type = f"model{model_str.lower()}" if model_str else "Tesla"
        trim = car_info.get("trim_badging", "")

        return {
            "vin": raw_status.get("vin", ""),
            "display_name": raw_status.get("display_name") or car_info.get("name") or "Tesla",
            "state": raw_status.get("state", "online"),
            "charge_state": {
                "battery_level": battery.get("battery_level"),
                "battery_range": range_miles,
                "charging_state": charging_state,
                "charger_power": charging.get("charger_power", 0),
                "charge_rate": charging.get("charge_energy_added", 0),
                "time_to_full_charge": charging.get("time_to_full_charge", 0),
                "charge_limit_soc": battery.get("charge_limit_soc", 80),
            },
            "climate_state": {
                "inside_temp": climate.get("inside_temp"),
                "outside_temp": climate.get("outside_temp"),
                "is_climate_on": bool(climate.get("is_climate_on")),
            },
            "vehicle_state": {
                "locked": vehicle.get("locked", True),
                "sentry_mode": vehicle.get("sentry_mode", False),
                "odometer": odo_miles,
            },
            "drive_state": {
                "shift_state": drive.get("shift_state", "P"),
                "speed": drive.get("speed", 0),
                "heading": drive.get("heading", 0),
            },
            "vehicle_config": {
                "car_type": car_type,
                "trim_badging": trim,
            },
        }
