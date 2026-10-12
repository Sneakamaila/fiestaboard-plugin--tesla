"""Unit tests for split-flap formatting utilities."""

import pytest
from plugins.tesla.formatters import (
    COLOR_BLACK,
    COLOR_BLUE,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_YELLOW,
    format_battery_badge,
    format_battery_bar_ascii,
    format_battery_bar_color,
    format_car_type,
    format_distance,
    format_odometer,
    format_speed,
    format_state,
    format_temp,
    format_time_remaining,
)


def test_format_battery_bar_ascii():
    assert format_battery_bar_ascii(100, length=10) == "[==========]"
    assert format_battery_bar_ascii(50, length=10) == "[=====     ]"
    assert format_battery_bar_ascii(0, length=10) == "[          ]"
    assert format_battery_bar_ascii(None, length=10) == "[          ]"


def test_format_battery_bar_color():
    # 80% on 5 slots -> 4 filled slots of Green ({66}), 1 empty slot of Black ({70})
    assert format_battery_bar_color(80, slots=5) == f"{COLOR_GREEN * 4}{COLOR_BLACK * 1}"
    # 40% on 5 slots -> 2 filled slots of Yellow ({65}), 3 empty slots of Black ({70})
    assert format_battery_bar_color(40, slots=5) == f"{COLOR_YELLOW * 2}{COLOR_BLACK * 3}"
    # 15% on 5 slots -> 1 filled slot of Red ({63}), 4 empty slots of Black ({70})
    assert format_battery_bar_color(15, slots=5) == f"{COLOR_RED * 1}{COLOR_BLACK * 4}"
    # None
    assert format_battery_bar_color(None, slots=5) == COLOR_BLACK * 5


def test_format_battery_badge():
    # Charging always returns blue
    assert format_battery_badge(80, is_charging=True) == COLOR_BLUE
    assert format_battery_badge(10, is_charging=True) == COLOR_BLUE

    # Not charging
    assert format_battery_badge(85, is_charging=False) == COLOR_GREEN
    assert format_battery_badge(35, is_charging=False) == COLOR_YELLOW
    assert format_battery_badge(15, is_charging=False) == COLOR_RED


def test_format_distance():
    # 100 miles to km: 100 * 1.609344 = ~161 km
    assert format_distance(100, unit_system="metric") == "161 km"
    assert format_distance(100, unit_system="imperial") == "100 mi"
    assert format_distance(None) == "--"


def test_format_odometer():
    assert format_odometer(26315, unit_system="metric") == "42,350 km"
    assert format_odometer(26315, unit_system="imperial") == "26,315 mi"


def test_format_speed():
    assert format_speed(65, unit_system="metric") == "105 km/h"
    assert format_speed(65, unit_system="imperial") == "65 mph"
    assert format_speed(0, unit_system="metric") == "0 km/h"
    assert format_speed(None, unit_system="metric") == "0 km/h"


def test_format_temp():
    assert format_temp(21.2, unit_system="metric") == "21°C"
    # 21°C -> 69.8 -> 70°F
    assert format_temp(21.0, unit_system="imperial") == "70°F"
    assert format_temp(None) == "--"


def test_format_time_remaining():
    assert format_time_remaining(1.5) == "1h 30m"
    assert format_time_remaining(2.0) == "2h"
    assert format_time_remaining(0.75) == "45m"
    assert format_time_remaining(0) == "--"
    assert format_time_remaining(None) == "--"


def test_format_car_type():
    assert format_car_type("modely", "longrange") == "Model Y Long Range"
    assert format_car_type("model3", "performance") == "Model 3 Performance"
    assert format_car_type("cybertruck", "awd") == "Cybertruck AWD"
    assert format_car_type("models", "plaid") == "Model S Plaid"
    assert format_car_type(None) == "Tesla"


def test_format_state():
    assert format_state("asleep") == "Asleep"
    assert format_state("online") == "Online"
    assert format_state("asleep", is_charging=True) == "Charging"
    assert format_state("online", shift_state="D") == "Driving"
    assert format_state(None) == "Unknown"
