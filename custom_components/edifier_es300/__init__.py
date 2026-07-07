"""The Edifier ES300 integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import ES300DataUpdateCoordinator

type ES300ConfigEntry = ConfigEntry[ES300DataUpdateCoordinator]

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ES300ConfigEntry) -> bool:
    """Set up Edifier ES300 from a config entry."""
    coordinator = ES300DataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ES300ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_disconnect()
    return unloaded
