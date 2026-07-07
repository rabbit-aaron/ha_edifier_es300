"""Binary sensor platform: charging (external power) state."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from edifier_es300.typing_ import BatteryStatus

from . import ES300ConfigEntry
from .coordinator import ES300DataUpdateCoordinator
from .entity import ES300Entity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ES300ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([ES300ChargingSensor(entry.runtime_data)])


class ES300ChargingSensor(ES300Entity, BinarySensorEntity):
    """On when the speaker is running on external power.

    device_class=battery_charging makes the frontend overlay the charging bolt
    on the sibling battery sensor.
    """

    _attr_name = "Charging"
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(self, coordinator: ES300DataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.unique_id}-charging"

    @property
    def is_on(self) -> bool | None:
        battery = self.coordinator.data.battery
        if not battery:
            return None
        return battery.get("status") == BatteryStatus.CONNECTED
