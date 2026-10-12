"""Tessie data provider for Tesla telemetry."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import requests

from .base import BaseTeslaProvider, ProviderError

logger = logging.getLogger(__name__)
TESSIE_API_BASE = "https://api.tessie.com"
DEFAULT_TIMEOUT = 12


class TessieProvider(BaseTeslaProvider):
    """Fetches telemetry from Tessie REST API using cached vehicle state."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        vin: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.vin = (vin or "").strip()
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "FiestaBoard-Tesla-Plugin/0.2.0",
        }

    def get_vehicle_data(self) -> Dict[str, Any]:
        if not self.api_key:
            raise ProviderError("Tessie API key is not configured.")

        if self.vin:
            return self._fetch_vehicle_state(self.vin)

        vehicles = self._fetch_vehicles()
        if not vehicles:
            raise ProviderError("No Tesla vehicles found on this Tessie account.")

        first_vehicle = vehicles[0]
        vin = first_vehicle.get("vin")
        if not vin:
            raise ProviderError("Vehicle entry from Tessie does not contain a VIN.")

        if "charge_state" in first_vehicle and "vehicle_state" in first_vehicle:
            return first_vehicle

        return self._fetch_vehicle_state(vin)

    def _fetch_vehicles(self) -> list[Dict[str, Any]]:
        url = f"{TESSIE_API_BASE}/vehicles"
        try:
            response = requests.get(
                url,
                headers=self._headers(),
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            logger.error("Network error connecting to Tessie API: %s", e)
            raise ProviderError(f"Network error connecting to Tessie: {e}") from e

        if response.status_code == 401:
            raise ProviderError("Invalid Tessie API token (401 Unauthorized).")
        if response.status_code == 429:
            raise ProviderError("Tessie API rate limit exceeded (429).")
        if not response.ok:
            raise ProviderError(f"Tessie API error ({response.status_code}): {response.text}")

        data = response.json()
        if isinstance(data, dict):
            return data.get("results", [])
        if isinstance(data, list):
            return data
        return []

    def _fetch_vehicle_state(self, vin: str) -> Dict[str, Any]:
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
            raise ProviderError(f"Network error contacting Tessie for VIN {vin}: {e}") from e

        if response.status_code == 401:
            raise ProviderError("Invalid Tessie API token (401 Unauthorized).")
        if response.status_code == 404:
            raise ProviderError(f"Vehicle VIN {vin} not found on Tessie account (404).")
        if response.status_code == 429:
            raise ProviderError("Tessie API rate limit exceeded (429).")
        if not response.ok:
            raise ProviderError(f"Tessie API error ({response.status_code}): {response.text}")

        return response.json()
