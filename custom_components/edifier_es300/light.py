"""Light platform for the Edifier ES300's ambient LED strip."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from edifier_es300 import LightColor, LightEffect

from . import ES300ConfigEntry
from .coordinator import ES300DataUpdateCoordinator
from .entity import ES300Entity

# The ES300 LED is warm (yellow) or cool (white) -- a two-point color temperature.
WARM_KELVIN = 2700
COOL_KELVIN = 6500
_MID_KELVIN = (WARM_KELVIN + COOL_KELVIN) // 2

EFFECTS = {effect.name.lower(): effect for effect in LightEffect}
EFFECT_NAMES = {effect.value: name for name, effect in EFFECTS.items()}


def _ha_brightness(device_level: int) -> int:
    return round(device_level / 100 * 255)


def _device_brightness(ha_level: int) -> int:
    return round(ha_level / 255 * 100)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ES300ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([ES300Light(entry.runtime_data)])


class ES300Light(ES300Entity, LightEntity):
    """On/off, brightness, effect and warm/cool color temperature."""

    _attr_translation_key = "led"
    _attr_name = "LED"
    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = list(EFFECTS)
    _attr_min_color_temp_kelvin = WARM_KELVIN
    _attr_max_color_temp_kelvin = COOL_KELVIN

    def __init__(self, coordinator: ES300DataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.unique_id}-led"

    @property
    def _light(self) -> dict[str, Any]:
        return self.coordinator.data.light_effect

    @property
    def is_on(self) -> bool:
        return bool(self._light.get("lightSwitch"))

    @property
    def brightness(self) -> int | None:
        level = self._light.get("brightness")
        return _ha_brightness(level) if level is not None else None

    @property
    def effect(self) -> str | None:
        return EFFECT_NAMES.get(self._light.get("selectedIndex"))

    @property
    def color_temp_kelvin(self) -> int:
        color = self._light.get("color")
        if color == LightColor.WHITE.value:
            return COOL_KELVIN
        return WARM_KELVIN

    async def async_turn_on(self, **kwargs: Any) -> None:
        # The device takes one field per command; apply each requested change.
        if not self.is_on and not any(
            key in kwargs
            for key in (ATTR_BRIGHTNESS, ATTR_COLOR_TEMP_KELVIN, ATTR_EFFECT)
        ):
            await self.coordinator.async_command(
                lambda device: device.light_switch(True)
            )
            return

        if not self.is_on:
            await self.coordinator.async_command(
                lambda device: device.light_switch(True)
            )
        if (brightness := kwargs.get(ATTR_BRIGHTNESS)) is not None:
            level = _device_brightness(brightness)
            await self.coordinator.async_command(
                lambda device: device.brightness(level)
            )
        if (kelvin := kwargs.get(ATTR_COLOR_TEMP_KELVIN)) is not None:
            color = LightColor.WHITE if kelvin >= _MID_KELVIN else LightColor.YELLOW
            await self.coordinator.async_command(
                lambda device: device.light_color(color)
            )
        if (effect := kwargs.get(ATTR_EFFECT)) is not None:
            chosen = EFFECTS[effect]
            await self.coordinator.async_command(
                lambda device: device.light_effect(chosen)
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_command(lambda device: device.light_switch(False))
