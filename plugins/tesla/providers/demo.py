"""Demo data provider simulating a Tesla Model Y."""

from __future__ import annotations

from typing import Any, Dict
from .base import BaseTeslaProvider


class DemoProvider(BaseTeslaProvider):
    """Provides simulated realistic Tesla vehicle data."""

    def get_vehicle_data(self) -> Dict[str, Any]:
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
