"""Base entity for the Edifier ES300 integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ES300DataUpdateCoordinator


class ES300Entity(CoordinatorEntity[ES300DataUpdateCoordinator]):
    """Shared device wiring for all ES300 entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ES300DataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.unique_id)},
            name=coordinator.device_name,
            manufacturer="Edifier",
            model="ES300",
        )
