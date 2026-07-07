"""Media player platform for the Edifier ES300."""

from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from edifier_es300 import EqPreset, PlayerStatus, Source

from . import ES300ConfigEntry
from .coordinator import ES300DataUpdateCoordinator
from .entity import ES300Entity

# Display labels shown in the UI, mapped to the device enums. Insertion order
# is the order shown in the source / sound-mode pickers.
SOURCES: dict[str, Source] = {
    "Bluetooth": Source.BLUETOOTH,
    "AUX": Source.AUX,
    "USB": Source.USB,
    "AirPlay": Source.AIRPLAY,
}
SOURCE_NAMES = {source.value: label for label, source in SOURCES.items()}

PRESETS: dict[str, EqPreset] = {
    "Classic": EqPreset.CLASSIC,
    "Monitor": EqPreset.MONITOR,
    "Game": EqPreset.GAME,
    "Vocal": EqPreset.VOCAL,
    "Customized": EqPreset.CUSTOMIZED,
}
PRESET_NAMES = {preset.value: label for label, preset in PRESETS.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ES300ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([ES300MediaPlayer(entry.runtime_data)])


class ES300MediaPlayer(ES300Entity, MediaPlayerEntity):
    """The speaker's playback, volume, source and EQ-preset controls."""

    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER
    _attr_source_list = list(SOURCES)
    _attr_sound_mode_list = list(PRESETS)
    _attr_supported_features = (
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.SELECT_SOUND_MODE
        | MediaPlayerEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: ES300DataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.unique_id

    @property
    def state(self) -> MediaPlayerState:
        if self.coordinator.data.player_status is PlayerStatus.PLAYING:
            return MediaPlayerState.PLAYING
        return MediaPlayerState.PAUSED

    @property
    def media_content_type(self) -> MediaType:
        return MediaType.MUSIC

    @property
    def media_title(self) -> str | None:
        # The ES300's two text slots are swapped relative to their names: `lyric`
        # holds the track title and `song` holds the artist (confirmed in the
        # Edifier app across all sources).
        return self.coordinator.data.lyric or None

    @property
    def media_artist(self) -> str | None:
        return self.coordinator.data.song or None

    @property
    def volume_level(self) -> float | None:
        data = self.coordinator.data
        if not data.max_volume:
            return None
        return data.volume / data.max_volume

    @property
    def source(self) -> str | None:
        selected = self.coordinator.data.input_source.get("selectedIndex")
        return SOURCE_NAMES.get(selected)

    @property
    def sound_mode(self) -> str | None:
        return PRESET_NAMES.get(self.coordinator.data.eq_selected_index)

    async def async_set_volume_level(self, volume: float) -> None:
        level = round(volume * self.coordinator.data.max_volume)
        await self.coordinator.async_command(lambda device: device.volume(level))

    async def async_volume_up(self) -> None:
        data = self.coordinator.data
        level = min(data.max_volume, data.volume + 1)
        await self.coordinator.async_command(lambda device: device.volume(level))

    async def async_volume_down(self) -> None:
        level = max(0, self.coordinator.data.volume - 1)
        await self.coordinator.async_command(lambda device: device.volume(level))

    async def async_media_play(self) -> None:
        await self.coordinator.async_command(lambda device: device.play())

    async def async_media_pause(self) -> None:
        await self.coordinator.async_command(lambda device: device.pause())

    async def async_media_next_track(self) -> None:
        await self.coordinator.async_command(lambda device: device.next_track())

    async def async_media_previous_track(self) -> None:
        await self.coordinator.async_command(lambda device: device.previous_track())

    async def async_select_source(self, source: str) -> None:
        chosen = SOURCES[source]
        await self.coordinator.async_command(lambda device: device.input_source(chosen))

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        chosen = PRESETS[sound_mode]
        await self.coordinator.async_command(lambda device: device.eq_preset(chosen))

    async def async_turn_off(self) -> None:
        await self.coordinator.async_command(lambda device: device.shutdown())
