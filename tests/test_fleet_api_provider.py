"""Unit tests for official Tesla Fleet API provider."""

import pytest
import responses
from plugins.tesla.providers.base import ProviderError
from plugins.tesla.providers.fleet_api import REGIONAL_ENDPOINTS, TeslaFleetApiProvider


def test_fleet_api_missing_token():
    provider = TeslaFleetApiProvider(access_token="")
    with pytest.raises(ProviderError, match="access token is required"):
        provider.get_vehicle_data()


@responses.activate
def test_fleet_api_fetch_success(sample_tessie_vehicle_state):
    region_url = REGIONAL_ENDPOINTS["eu"]
    vin = "5YJ3E1EB8NF123456"

    # Mock /api/1/vehicles
    responses.add(
        responses.GET,
        f"{region_url}/api/1/vehicles",
        json={"response": [{"id": 12345, "vin": vin, "display_name": "Starship"}]},
        status=200,
    )
    # Mock /api/1/vehicles/12345/vehicle_data
    responses.add(
        responses.GET,
        f"{region_url}/api/1/vehicles/12345/vehicle_data",
        json={"response": sample_tessie_vehicle_state},
        status=200,
    )

    provider = TeslaFleetApiProvider(access_token="valid_fleet_token", region="eu")
    data = provider.get_vehicle_data()

    assert data["vin"] == vin
    assert data["display_name"] == "Starship"
    assert data["charge_state"]["battery_level"] == 75


@responses.activate
def test_fleet_api_401_invalid_token():
    region_url = REGIONAL_ENDPOINTS["eu"]
    responses.add(
        responses.GET,
        f"{region_url}/api/1/vehicles",
        json={"error": "Unauthorized"},
        status=401,
    )

    provider = TeslaFleetApiProvider(access_token="invalid_token", region="eu")
    with pytest.raises(ProviderError, match="token is invalid or expired"):
        provider.get_vehicle_data()
