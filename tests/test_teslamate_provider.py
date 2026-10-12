"""Unit tests for the TeslaMate provider."""

import pytest
import responses
from plugins.tesla.providers.base import ProviderError
from plugins.tesla.providers.teslamate import TeslaMateProvider


@pytest.fixture
def sample_teslamate_response():
    """Sample status response from TeslaMateApi (/api/v1/cars/1/status)."""
    return {
        "data": {
            "status": {
                "car_id": 1,
                "display_name": "Falcon 9",
                "vin": "5YJ3E1EB8NF555555",
                "state": "asleep",
                "battery_details": {
                    "battery_level": 78,
                    "rated_battery_range": 395.0,  # km
                    "charge_limit_soc": 80,
                },
                "charging_details": {
                    "charging_state": "Disconnected",
                    "charger_power": 0,
                    "charge_energy_added": 0,
                    "time_to_full_charge": 0,
                },
                "climate_details": {
                    "inside_temp": 19.0,
                    "outside_temp": 11.5,
                    "is_climate_on": False,
                },
                "drive_details": {
                    "shift_state": "P",
                    "speed": 0,
                    "heading": 270,
                },
                "vehicle_state": {
                    "locked": True,
                    "sentry_mode": False,
                    "odometer": 32000.0,  # km
                },
                "car_details": {
                    "model": "Y",
                    "trim_badging": "Long Range",
                },
            }
        }
    }


def test_teslamate_missing_base_url():
    provider = TeslaMateProvider(base_url="")
    with pytest.raises(ProviderError, match="base URL is not configured"):
        provider.get_vehicle_data()


@responses.activate
def test_teslamate_fetch_success(sample_teslamate_response):
    base_url = "http://192.168.1.50:8080"
    car_id = 1
    responses.add(
        responses.GET,
        f"{base_url}/api/v1/cars/{car_id}/status",
        json=sample_teslamate_response,
        status=200,
    )

    provider = TeslaMateProvider(base_url=base_url, car_id=car_id)
    data = provider.get_vehicle_data()

    assert data["display_name"] == "Falcon 9"
    assert data["state"] == "asleep"
    assert data["charge_state"]["battery_level"] == 78
    assert data["climate_state"]["inside_temp"] == 19.0
    assert data["vehicle_state"]["locked"] is True
    # Range km 395 converted to miles ~ 245.4
    assert 245.0 < data["charge_state"]["battery_range"] < 246.0


@responses.activate
def test_teslamate_401_auth_failed():
    base_url = "http://192.168.1.50:8080"
    responses.add(
        responses.GET,
        f"{base_url}/api/v1/cars/1/status",
        status=401,
    )

    provider = TeslaMateProvider(base_url=base_url, car_id=1)
    with pytest.raises(ProviderError, match="Authentication failed"):
        provider.get_vehicle_data()


@responses.activate
def test_teslamate_404_car_not_found():
    base_url = "http://192.168.1.50:8080"
    responses.add(
        responses.GET,
        f"{base_url}/api/v1/cars/99/status",
        status=404,
    )

    provider = TeslaMateProvider(base_url=base_url, car_id=99)
    with pytest.raises(ProviderError, match="Car ID 99 not found"):
        provider.get_vehicle_data()
