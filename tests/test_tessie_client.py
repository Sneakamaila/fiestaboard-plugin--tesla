"""Unit tests for Tessie API client."""

import pytest
import responses
from plugins.tesla.tessie_client import TESSIE_API_BASE, TessieApiError, TessieClient


def test_tessie_client_demo_mode():
    client = TessieClient(demo_mode=True)
    data = client.get_vehicle_data()
    assert data["display_name"] == "Model Y"
    assert data["charge_state"]["battery_level"] == 82
    assert data["vin"] == "5YJ3E1EB8NF987654"


def test_tessie_client_missing_key_raises():
    client = TessieClient(api_key="", demo_mode=False)
    with pytest.raises(TessieApiError, match="Tessie API key is not configured"):
        client.get_vehicle_data()


@responses.activate
def test_tessie_client_fetch_by_vin_success(sample_tessie_vehicle_state):
    vin = "5YJ3E1EB8NF123456"
    responses.add(
        responses.GET,
        f"{TESSIE_API_BASE}/{vin}/state?use_cache=true",
        json=sample_tessie_vehicle_state,
        status=200,
    )

    client = TessieClient(api_key="valid_token", vin=vin)
    data = client.get_vehicle_data()
    assert data["vin"] == vin
    assert data["display_name"] == "Starship"
    assert data["charge_state"]["battery_level"] == 75


@responses.activate
def test_tessie_client_auto_detect_first_vehicle(sample_tessie_vehicle_state):
    vin = "5YJ3E1EB8NF123456"
    responses.add(
        responses.GET,
        f"{TESSIE_API_BASE}/vehicles",
        json={"results": [sample_tessie_vehicle_state]},
        status=200,
    )

    client = TessieClient(api_key="valid_token", vin="")
    data = client.get_vehicle_data()
    assert data["vin"] == vin
    assert data["display_name"] == "Starship"


@responses.activate
def test_tessie_client_401_unauthorized():
    vin = "5YJ3E1EB8NF123456"
    responses.add(
        responses.GET,
        f"{TESSIE_API_BASE}/{vin}/state?use_cache=true",
        json={"error": "Unauthorized"},
        status=401,
    )

    client = TessieClient(api_key="invalid_token", vin=vin)
    with pytest.raises(TessieApiError, match="401 Unauthorized"):
        client.get_vehicle_data()


@responses.activate
def test_tessie_client_404_not_found():
    vin = "UNKNOWN_VIN"
    responses.add(
        responses.GET,
        f"{TESSIE_API_BASE}/{vin}/state?use_cache=true",
        json={"error": "Not found"},
        status=404,
    )

    client = TessieClient(api_key="valid_token", vin=vin)
    with pytest.raises(TessieApiError, match="not found on Tessie account"):
        client.get_vehicle_data()


@responses.activate
def test_tessie_client_429_rate_limit():
    vin = "5YJ3E1EB8NF123456"
    responses.add(
        responses.GET,
        f"{TESSIE_API_BASE}/{vin}/state?use_cache=true",
        json={"error": "Too Many Requests"},
        status=429,
    )

    client = TessieClient(api_key="valid_token", vin=vin)
    with pytest.raises(TessieApiError, match="rate limit exceeded"):
        client.get_vehicle_data()
