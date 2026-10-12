"""Official Tesla Fleet API / Proxy data provider."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import requests

from .base import BaseTeslaProvider, ProviderError

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 12

REGIONAL_ENDPOINTS = {
    "eu": "https://fleet-api.prd.eu.vn.cloud.tesla.com",
    "na": "https://fleet-api.prd.na.vn.cloud.tesla.com",
    "cn": "https://fleet-api.prd.cn.vn.cloud.tesla.cn",
}


class TeslaFleetApiProvider(BaseTeslaProvider):
    """Fetches telemetry directly from the official Tesla Fleet API or a proxy."""

    def __init__(
        self,
        access_token: str,
        region: str = "eu",
        custom_endpoint: Optional[str] = None,
        vin: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.access_token = (access_token or "").strip()
        self.vin = (vin or "").strip()
        self.timeout = timeout

        if custom_endpoint:
            self.base_url = custom_endpoint.strip().rstrip("/")
        else:
            self.base_url = REGIONAL_ENDPOINTS.get(region.lower(), REGIONAL_ENDPOINTS["eu"])

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "User-Agent": "FiestaBoard-Tesla-Plugin/0.2.0",
        }

    def get_vehicle_data(self) -> Dict[str, Any]:
        if not self.access_token:
            raise ProviderError("Tesla Fleet API access token is required.")

        vehicle_tag = self.vin
        if not vehicle_tag:
            vehicles = self._fetch_vehicles()
            if not vehicles:
                raise ProviderError("No vehicles returned by Tesla Fleet API.")
            first = vehicles[0]
            vehicle_tag = str(first.get("id") or first.get("vin") or "")
            if not vehicle_tag:
                raise ProviderError("Unable to determine vehicle ID from Tesla Fleet API.")

        return self._fetch_vehicle_data(vehicle_tag)

    def _fetch_vehicles(self) -> list[Dict[str, Any]]:
        url = f"{self.base_url}/api/1/vehicles"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
        except requests.RequestException as e:
            logger.error("Failed contacting Tesla Fleet API: %s", e)
            raise ProviderError(f"Network error connecting to Tesla Fleet API: {e}") from e

        if resp.status_code == 401:
            raise ProviderError("Tesla Fleet API token is invalid or expired (401).")
        if not resp.ok:
            raise ProviderError(f"Tesla Fleet API error ({resp.status_code}): {resp.text}")

        data = resp.json()
        return data.get("response", []) if isinstance(data, dict) else []

    def _fetch_vehicle_data(self, vehicle_tag: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/1/vehicles/{vehicle_tag}/vehicle_data"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
        except requests.RequestException as e:
            logger.error("Failed fetching vehicle_data for %s: %s", vehicle_tag, e)
            raise ProviderError(f"Network error from Tesla Fleet API: {e}") from e

        if resp.status_code == 401:
            raise ProviderError("Tesla Fleet API token is invalid or expired (401).")
        if resp.status_code == 404:
            raise ProviderError(f"Vehicle {vehicle_tag} not found on Tesla Fleet API (404).")
        if not resp.ok:
            raise ProviderError(f"Tesla Fleet API error ({resp.status_code}): {resp.text}")

        data = resp.json()
        response_body = data.get("response", {}) if isinstance(data, dict) else {}
        return response_body
