"""Tessie API client wrapper maintaining backward compatibility."""

from __future__ import annotations

from typing import Any, Dict, Optional
from .providers.base import ProviderError
from .providers.demo import DemoProvider
from .providers.tessie import TESSIE_API_BASE, TessieProvider

# Backward compatibility alias
TessieApiError = ProviderError


class TessieClient:
    """Client wrapper for Tessie."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        vin: Optional[str] = None,
        demo_mode: bool = False,
        timeout: int = 12,
    ) -> None:
        self.demo_mode = demo_mode
        if demo_mode:
            self._provider = DemoProvider()
        else:
            self._provider = TessieProvider(api_key=api_key, vin=vin, timeout=timeout)

    def get_vehicle_data(self) -> Dict[str, Any]:
        return self._provider.get_vehicle_data()


__all__ = ["TessieClient", "TessieApiError", "TESSIE_API_BASE"]
