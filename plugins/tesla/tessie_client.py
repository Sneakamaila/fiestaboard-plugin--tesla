"""Tessie API client for fetching Tesla vehicle telemetry."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import requests

logger = logging.getLogger(__name__)

TESSIE_API_BASE = "https://api.tessie.com"
DEFAULT_TIMEOUT = 12


class TessieApiError(Exception):
    """Exception raised when a Tessie API call fails."""


class TessieClient:
    """Client for querying the Tessie REST API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        vin: Optional[str] = None,
        demo_mode: bool = False,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.vin = (vin or "").strip()
        self.demo_mode = demo_mode
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "FiestaBoard-Tesla-Plugin/0.1.0",
        }

    def get_vehicle_data(self) -> Dict[str, Any]:
        """Fetch vehicle telemetry from Tessie or return simulated demo data."""
        if self.demo_mode or not self.api_key:
            if self.demo_mode:
                return self._get_demo_data()
            raise TessieApiError("Tessie API key is not configured.")

        # If VIN is provided, fetch state directly using cached endpoint
        if self.vin:
            return self._fetch_vehicle_state(self.vin)

        # Otherwise fetch vehicle list and use the first vehicle
        vehicles = self._fetch_vehicles()
        if not vehicles:
            raise TessieApiError("No Tesla vehicles found on this Tessie account.")

        first_vehicle = vehicles[0]
        vin = first_vehicle.get("vin")
        if not vin:
            raise TessieApiError("Vehicle entry from Tessie does not contain a VIN.")

        # If vehicle item in /vehicles already contains detailed states, return it
        if "charge_state" in first_vehicle and "vehicle_state" in first_vehicle:
            return first_vehicle

        # Otherwise fetch full state by VIN
        return self._fetch_vehicle_state(vin)

    def _fetch_vehicles(self) -> list[Dict[str, Any]]:
        """Fetch list of vehicles associated with the Tessie account."""
        url = f"{TESSIE_API_BASE}/vehicles"
        try:
            response = requests.get(
                url,
                headers=self._headers(),
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            logger.error("Network error connecting to Tessie API: %s", e)
            raise TessieApiError(f"Network error connecting to Tessie: {e}") from e

        if response.status_code == 401:
            raise TessieApiError("Invalid Tessie API token (401 Unauthorized).")
        if response.status_code == 429:
            raise TessieApiError("Tessie API rate limit exceeded (429).")
        if not response.ok:
            raise TessieApiError(f"Tessie API error ({response.status_code}): {response.text}")

        data = response.json()
        if isinstance(data, dict):
            # Tessie /vehicles often returns {"results": [...]}
            return data.get("results", [])
        if isinstance(data, list):
            return data
        return []

    def _fetch_vehicle_state(self, vin: str) -> Dict[str, Any]:
        """Fetch state for a specific vehicle VIN using Tessie cache."""
        url = f"{TESSIE_API_BASE}/{vin}/state"
        params = {"use_cache": "true"}

        try:
            response = requests.get(
                url,
                headers=self._headers(),
                params=params,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            logger.error("Network error fetching vehicle state for %s: %s", vin, e)
            raise TessieApiError(f"Network error contacting Tessie for VIN {vin}: {e}") from e

        if response.status_code == 401:
            raise TessieApiError("Invalid Tessie API token (401 Unauthorized).")
        if response.status_code == 404:
            raise TessieApiError(f"Vehicle VIN {vin} not found on Tessie account (404).")
        if response.status_code == 429:
            raise TessieApiError("Tessie API rate limit exceeded (429).")
        if not response.ok:
            raise TessieApiError(f"Tessie API error ({response.status_code}): {response.text}")

        return response.json()

    def _get_demo_data(self) -> Dict[str, Any]:
        """Generate realistic mock data for preview and demo testing."""
        return {
            "vin": "5YJ3E1EB8NF987654",
            "display_name": "Model Y",
            "state": "asleep",
            "charge_state": {
                "battery_level": 82,
                "battery_range": 256.0,  # ~412 km in miles
                "charging_state": "Disconnected",
                "charger_power": 0,
                "charge_rate": 0.0,
                "time_to_full_charge": 0.0,
                "charge_limit_soc": 80,
            },
            "climate_state": {
                "inside_temp": 21.0,
                "outside_temp": 16.0,
                "is_climate_on": False,
            },
            "vehicle_state": {
                "locked": True,
                "sentry_mode": False,
                "odometer": 26315.0,  # ~42,350 km in miles
            },
            "drive_state": {
                "shift_state": "P",
                "speed": 0,
                "heading": 180,
            },
            "vehicle_config": {
                "car_type": "modely",
                "trim_badging": "longrange",
            },
        }
