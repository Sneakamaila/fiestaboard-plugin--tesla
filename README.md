# FiestaBoard Tesla Plugin 🚗⚡

[![FiestaBoard](https://img.shields.io/badge/FiestaBoard-Plugin-blue.svg)](https://fiestaboard.app)
[![Python](https://img.shields.io/badge/Python-3.9+-brightgreen.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-31%20passed-success.svg)](tests/)

Display real-time Tesla vehicle status and telemetry on your **Vestaboard** or split-flap display using [FiestaBoard](https://fiestaboard.app).

Supports multiple data providers: **Tessie API**, self-hosted **TeslaMate**, and the official **Tesla Fleet API**!

---

## 🔌 Supported Data Providers

| Provider | Type | Cost | Best For | Car Wake-Up? |
|---|---|---|---|---|
| **Tessie API** | Cloud REST | Subscription | Easiest cloud setup, zero maintenance | ❌ No (cached) |
| **TeslaMate** | Self-Hosted / Local | **100% Free** | Tech enthusiasts, Raspberry Pi, Docker, Home Assistant | ❌ No (local DB/MQTT) |
| **Tesla Fleet API** | Official Tesla Cloud | Developer Account | Direct Tesla integration | ⚠️ Depending on polling |
| **Demo Mode** | Simulation | Free | Testing board layouts without a car | ❌ No |

---

## ✨ Features

- 🔋 **Battery & Range**: Live battery percentage, estimated remaining range, and charge limits.
- 🎨 **Visual Split-Flap Color Bar**: Dynamic battery progress bar using Vestaboard color tiles (`{66}` Green, `{65}` Yellow, `{63}` Red, `{67}` Blue, `{70}` Black).
- ⚡ **Charging Telemetry**: Charging status, charging power in kW, charge speed, and time to full charge.
- ❄️ **Climate & Doors**: Interior and exterior temperatures, climate HVAC state, lock status, and Sentry mode.
- 🏎️ **Drive & Vehicle**: Odometer, vehicle name, car model/trim (e.g., *Model Y Long Range*), speed, and gear state.
- 🔔 **Event Triggers**: Built-in trigger alerts for **Low Battery (< 20%)** and **Charging Complete**.
- 🧪 **Instant Demo Mode**: Test and preview board layouts immediately without credentials.
- 🌍 **Metric & Imperial**: Full support for both `metric` (km, °C) and `imperial` (miles, °F).

---

## 📐 Board Layout Examples

### Vestaboard Flagship (22 × 6)

#### Standard Overview
```text
MODEL Y     82% {66}{66}{66}{66}{70}
Range: 412 km (Lim 80%)
Status: Asleep / Locked
Climate: OFF (In: 21°C)
Odometer: 42,350 km
Updated: 22:30
```

#### Active Charging Mode
```text
MODEL Y   {67} CHARGING
Battery:  65% -> 80%
Power:    11.0 kW (65 km/h)
Time:     1h 15m to full
Range:    320 km
Updated:  22:35
```

### Vestaboard Note (15 × 3)

```text
{66} MODEL Y 82%
412 KM RANGE
ASLEEP / LOCKED
```

---

## ⚙️ Configuration Guide

In the FiestaBoard Web UI under **Integrations > Tesla**, configure the options for your chosen provider:

### 1. General Settings
| Setting | Type | Default | Description |
|---|---|---|---|
| `enabled` | boolean | `true` | Enable or disable the plugin |
| `provider` | string | `"tessie"` | Choose `"tessie"`, `"teslamate"`, `"fleet_api"`, or `"demo"` |
| `unit_system`| string | `"metric"` | Choose `"metric"` (km, °C) or `"imperial"` (mi, °F) |
| `refresh_seconds` | integer | `300` | Polling interval in seconds (minimum 60) |
| `demo_mode` | boolean | `false` | Enable simulated Tesla telemetry |

### 2. Provider-Specific Settings

#### When using Tessie (`provider: "tessie"`)
- **`api_key`**: Personal Access Token from [dash.tessie.com/settings/api](https://dash.tessie.com/settings/api).
- **`vin`**: *(Optional)* Specific VIN if multiple vehicles exist.

#### When using TeslaMate (`provider: "teslamate"`)
Works with the popular [TeslaMateApi](https://github.com/tobiasehlert/teslamateapi) container.
- **`teslamate_url`**: Base URL of your TeslaMateApi instance (e.g. `http://192.168.1.100:8080` or `http://homeassistant.local:8080`).
- **`teslamate_api_key`**: *(Optional)* Bearer token if API authentication is enabled.
- **`car_id`**: Car ID in your TeslaMate database (default: `1`).

#### When using Tesla Fleet API (`provider: "fleet_api"`)
- **`api_key`**: Official Tesla Fleet API Bearer access token.
- **`fleet_region`**: `"eu"` (Europe), `"na"` (North America), or `"cn"` (China).
- **`vin`**: *(Optional)* Vehicle VIN.

---

## 📋 Available Template Variables

All variables are available in templates with the `tesla.` prefix (e.g. `{{tesla.battery_pct}}`):

### 🚗 Vehicle (`vehicle`)
| Variable | Description | Example |
|---|---|---|
| `tesla.vehicle_name` | Vehicle display name | `Model Y` / `Starship` |
| `tesla.vin` | Vehicle Identification Number | `5YJ3E1EB8NF123456` |
| `tesla.car_type` | Model and trim | `Model Y Long Range` |
| `tesla.state` | State (*Online*, *Asleep*, *Charging*, *Driving*) | `Asleep` |
| `tesla.locked` | Door lock state | `Locked` / `Unlocked` |
| `tesla.sentry_mode` | Sentry Mode status | `ON` / `OFF` |
| `tesla.odometer` | Total mileage with unit | `42,350 km` |

### 🔋 Battery & Energy (`battery`)
| Variable | Description | Example |
|---|---|---|
| `tesla.battery_level` | Battery SOC integer (0–100) | `82` |
| `tesla.battery_pct` | Battery percentage with `%` | `82%` |
| `tesla.battery_range` | Estimated remaining range | `412 km` / `256 mi` |
| `tesla.battery_bar_ascii` | Standard ASCII progress bar | `[========  ]` |
| `tesla.battery_bar_color` | Vestaboard color tiles progress bar | `{66}{66}{66}{66}{70}` |
| `tesla.battery_badge` | Single color tile (Green/Yellow/Red/Blue) | `{66}` |

### ⚡ Charging (`charging`)
| Variable | Description | Example |
|---|---|---|
| `tesla.is_charging` | Whether vehicle is actively charging | `YES` / `NO` |
| `tesla.charging_state` | Detailed charge state | `Charging` / `Complete` / `Disconnected` |
| `tesla.charger_power` | Charging power in kW | `11.0 kW` |
| `tesla.charge_rate` | Charging speed | `65 km/h` / `40 mph` |
| `tesla.time_to_full` | Estimated time remaining until full | `1h 15m` |
| `tesla.charge_limit` | Configured charge limit | `80%` |
| `tesla.charging_summary` | Summary line | `11.0 kW (1h 15m to 80%)` |

### 🌡️ Climate (`climate`)
| Variable | Description | Example |
|---|---|---|
| `tesla.inside_temp` | Cabin interior temperature | `21°C` / `70°F` |
| `tesla.outside_temp` | Ambient exterior temperature | `16°C` / `61°F` |
| `tesla.climate_on` | HVAC status | `ON` / `OFF` |

### 🧭 Drive & Motion (`drive`)
| Variable | Description | Example |
|---|---|---|
| `tesla.speed` | Current vehicle speed | `0 km/h` |
| `tesla.shift_state` | Gear position | `P` / `D` / `R` / `N` |

### 🕒 System (`system`)
| Variable | Description | Example |
|---|---|---|
| `tesla.last_updated` | Timestamp of latest telemetry update | `22:30` |

---

## 🚀 Installation into FiestaBoard

1. **Web UI Git Import (Recommended)**:
   - Open your FiestaBoard dashboard (default: `http://localhost:4420`).
   - Go to **Integrations** > **Add Plugin**.
   - Paste the repository URL: `https://github.com/Sneakamaila/fiestaboard-plugin--tesla`.

2. **Local Directory Mount**:
   - Copy or clone this folder into your FiestaBoard `plugins/` directory:
     ```bash
     cp -r fiestaboard-plugin--tesla /path/to/FiestaBoard/plugins/tesla
     ```
   - Restart or reload FiestaBoard.

---

## 🛠️ Testing & Development

Run the test suite locally:

```bash
# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Run pytest
pytest tests -v --cov=plugins/tesla
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
