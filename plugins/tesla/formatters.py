"""Formatting utilities for Tesla telemetry data on split-flap boards."""

from __future__ import annotations

from typing import Any


# Vestaboard split-flap color codes
COLOR_RED = "{63}"
COLOR_ORANGE = "{64}"
COLOR_YELLOW = "{65}"
COLOR_GREEN = "{66}"
COLOR_BLUE = "{67}"
COLOR_VIOLET = "{68}"
COLOR_WHITE = "{69}"
COLOR_BLACK = "{70}"
COLOR_BLANK = "{0}"


def format_battery_bar_ascii(level: int | float | None, length: int = 10) -> str:
    """Format battery percentage as an ASCII progress bar.

    Example (82% on length 10):
        [========  ]
    """
    if level is None:
        return "[" + " " * length + "]"

    pct = max(0.0, min(100.0, float(level)))
    filled = int(round((pct / 100.0) * length))
    empty = length - filled
    return "[" + ("=" * filled) + (" " * empty) + "]"


def format_battery_bar_color(
    level: int | float | None,
    slots: int = 5,
    empty_color: str = COLOR_BLACK,
) -> str:
    """Format battery percentage as a sequence of Vestaboard color tiles.

    Uses Green for high charge, Yellow for medium, Red for low.
    Example (82% on 5 slots):
        {66}{66}{66}{66}{70}
    """
    if level is None:
        return empty_color * slots

    pct = max(0.0, min(100.0, float(level)))
    filled_count = int(round((pct / 100.0) * slots))

    if pct >= 50:
        fill_color = COLOR_GREEN
    elif pct >= 20:
        fill_color = COLOR_YELLOW
    else:
        fill_color = COLOR_RED

    empty_count = max(0, slots - filled_count)
    return (fill_color * filled_count) + (empty_color * empty_count)


def format_battery_badge(
    level: int | float | None,
    is_charging: bool = False,
) -> str:
    """Format a single color tile representing battery state.

    Blue ({67}) when charging, Green ({66}) >= 50%, Yellow ({65}) >= 20%, Red ({63}) < 20%.
    """
    if is_charging:
        return COLOR_BLUE
    if level is None:
        return COLOR_BLANK

    pct = max(0.0, min(100.0, float(level)))
    if pct >= 50:
        return COLOR_GREEN
    if pct >= 20:
        return COLOR_YELLOW
    return COLOR_RED


def format_distance(
    miles: int | float | None,
    unit_system: str = "metric",
) -> str:
    """Format distance (input in miles from Tesla API) to km or miles."""
    if miles is None:
        return "--"

    if unit_system == "imperial":
        val = int(round(float(miles)))
        return f"{val:,} mi"

    km = int(round(float(miles) * 1.609344))
    return f"{km:,} km"


def format_odometer(
    miles: int | float | None,
    unit_system: str = "metric",
) -> str:
    """Format odometer reading."""
    return format_distance(miles, unit_system=unit_system)


def format_speed(
    mph: int | float | None,
    unit_system: str = "metric",
) -> str:
    """Format speed (input in mph from Tesla API)."""
    if mph is None:
        return "0 km/h" if unit_system == "metric" else "0 mph"

    val = float(mph)
    if unit_system == "imperial":
        return f"{int(round(val))} mph"

    kmh = int(round(val * 1.609344))
    return f"{kmh} km/h"


def format_temp(
    celsius: int | float | None,
    unit_system: str = "metric",
) -> str:
    """Format temperature (input in °C from Tesla API).

    Outputs C or F since split-flap character sets do not include the degree sign.
    """
    if celsius is None:
        return "--"

    c = float(celsius)
    if unit_system == "imperial":
        f = int(round((c * 9.0 / 5.0) + 32.0))
        return f"{f}F"

    return f"{int(round(c))}C"


def format_time_remaining(hours: int | float | None) -> str:
    """Format remaining charge time in hours to human readable string (e.g. 1h 25m)."""
    if hours is None or hours <= 0:
        return "--"

    total_minutes = int(round(float(hours) * 60))
    if total_minutes <= 0:
        return "--"

    h = total_minutes // 60
    m = total_minutes % 60

    if h > 0 and m > 0:
        return f"{h}h {m:02d}m"
    if h > 0:
        return f"{h}h"
    return f"{m}m"


def format_car_type(car_type: str | None, trim_badging: str | None = None) -> str:
    """Format vehicle model and trim."""
    model_names = {
        "models": "Model S",
        "model3": "Model 3",
        "modelx": "Model X",
        "modely": "Model Y",
        "cybertruck": "Cybertruck",
        "semi": "Semi",
        "roadster": "Roadster",
    }
    trim_names = {
        "longrange": "Long Range",
        "performance": "Performance",
        "plaid": "Plaid",
        "standard": "Standard",
        "rwd": "RWD",
        "awd": "AWD",
    }

    raw_model = (car_type or "").lower().strip()
    model = model_names.get(raw_model, car_type or "Tesla")

    if not trim_badging:
        return model

    raw_trim = trim_badging.lower().replace("_", "").replace("-", "").strip()
    trim = trim_names.get(raw_trim, trim_badging.title())
    return f"{model} {trim}"


def format_state(
    state: str | None,
    shift_state: str | None = None,
    is_charging: bool = False,
) -> str:
    """Format vehicle state."""
    if is_charging:
        return "Charging"
    if shift_state in ("D", "R", "N"):
        return "Driving"
    if not state:
        return "Unknown"

    s = state.strip().lower()
    if s == "asleep":
        return "Asleep"
    if s == "online":
        return "Online"
    if s == "offline":
        return "Offline"
    return state.capitalize()
