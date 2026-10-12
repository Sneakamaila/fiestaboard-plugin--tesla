"""Abstract base class and exceptions for Tesla data providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class ProviderError(Exception):
    """Exception raised when a Tesla data provider fails."""


class BaseTeslaProvider(ABC):
    """Base interface for all Tesla data providers."""

    @abstractmethod
    def get_vehicle_data(self) -> Dict[str, Any]:
        """Fetch and return normalized vehicle telemetry.

        Returns a dictionary containing:
            - vin (str)
            - display_name (str)
            - state (str)
            - charge_state (dict)
            - climate_state (dict)
            - vehicle_state (dict)
            - drive_state (dict)
            - vehicle_config (dict)
        """
