# Edifier ES300 — Home Assistant integration

A local-push/poll custom integration to control an **Edifier ES300** speaker over
its Wi-Fi control channel, built on the [`edifier-es300`](https://pypi.org/project/edifier-es300/)
PyPI package.

## Features

- **Media player** — playback state + now-playing title, play/pause, next/previous,
  volume slider, input source select (Bluetooth / AUX / USB / AirPlay), and EQ
  preset via sound mode (Classic / Monitor / Game / Vocal / Customized).
- **Light** — the ambient LED strip: on/off, brightness, effect
  (static / breathing / waterflow) and warm/cool color temperature.
- **Numbers** — the 6-band custom EQ as dB sliders (62 Hz / 250 Hz / 1 kHz /
  4 kHz / 8 kHz / 16 kHz) plus a sleep-timer (minutes).
- **Sensor** — battery level.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open this repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=rabbit-aaron&repository=ha_edifier_es300&category=integration)

Click the button above to add this repository to [HACS](https://hacs.xyz), then
install **Edifier ES300** and restart Home Assistant.

### Manual

Copy `custom_components/edifier_es300` into your Home Assistant `config/custom_components`
directory and restart Home Assistant.

### Add the integration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=edifier_es300)

Or add it manually from **Settings → Devices & Services → Add Integration → Edifier ES300**.

## Setup

- Enter the speaker's **host** (and optionally port, default `8080`), **or**
- Leave the host blank to **auto-discover** speakers on your LAN. Discovered
  speakers' host/port are cached in the config entry.

## Development

This is a `uv`-managed project pinned to Python 3.13:

```sh
uv sync
```
