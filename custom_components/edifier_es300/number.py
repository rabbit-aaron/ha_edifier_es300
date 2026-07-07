"""Number platform: 6-band custom EQ sliders and the sleep timer."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ES300ConfigEntry
from .coordinator import ES300DataUpdateCoordinator
from .entity import ES300Entity

# soundEffectDIY band order, per the device schema.
EQ_BANDS = ["62 Hz", "250 Hz", "1 kHz", "4 kHz", "8 kHz", "16 kHz"]
EQ_SLUGS = ["62hz", "250hz", "1khz", "4khz", "8khz", "16khz"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ES300ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[NumberEntity] = [
        ES300EqBand(coordinator, index) for index in range(len(EQ_BANDS))
    ]
    entities.append(ES300SleepTimer(coordinator))
    async_add_entities(entities)


class ES300EqBand(ES300Entity, NumberEntity):
    """One custom-EQ band, in dB (device stores tenths of a dB, -30..30)."""

    _attr_native_min_value = -3.0
    _attr_native_max_value = 3.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "dB"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: ES300DataUpdateCoordinator, index: int) -> None:
        super().__init__(coordinator)
        self._index = index
        self._attr_name = f"EQ {EQ_BANDS[index]}"
        self._attr_unique_id = f"{coordinator.unique_id}-eq-{EQ_SLUGS[index]}"

    @property
    def native_value(self) -> float | None:
        gains = self.coordinator.data.eq_gains
        if self._index >= len(gains):
            return None
        return gains[self._index] / 10

    async def async_set_native_value(self, value: float) -> None:
        # eq_custom takes all six band gains at once (tenths of a dB); change the
        # one band this entity owns and resend the rest unchanged.
        gains = list(self.coordinator.data.eq_gains)
        if len(gains) < 6 or self._index >= 6:
            return
        gains[self._index] = round(value * 10)
        band_gains = tuple(gains[:6])
        await self.coordinator.async_command(
            lambda device: device.eq_custom(band_gains)
        )


class ES300SleepTimer(ES300Entity, NumberEntity):
    """Sleep timer in minutes (0 = off)."""

    _attr_name = "Sleep timer"
    _attr_native_min_value = 0
    _attr_native_max_value = 1440
    _attr_native_step = 5
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: ES300DataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.unique_id}-sleep-timer"

    @property
    def native_value(self) -> int:
        timer = self.coordinator.data.timer_shutdown or {}
        return timer.get("timeShutdown", 0)

    async def async_set_native_value(self, value: float) -> None:
        minutes = int(value)
        await self.coordinator.async_command(
            lambda device: device.timer_shutdown(minutes)
        )
