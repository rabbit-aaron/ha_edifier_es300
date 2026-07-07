"""Sensor platform: battery level."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ES300ConfigEntry
from .coordinator import ES300DataUpdateCoordinator
from .entity import ES300Entity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ES300ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([ES300BatterySensor(entry.runtime_data)])


class ES300BatterySensor(ES300Entity, SensorEntity):
    """Battery charge percentage."""

    _attr_name = "Battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: ES300DataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.unique_id}-battery"

    @property
    def native_value(self) -> int | None:
        battery = self.coordinator.data.battery
        if not battery:
            return None
        return battery.get("box")
