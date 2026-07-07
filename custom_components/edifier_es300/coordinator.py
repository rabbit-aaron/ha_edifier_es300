"""Coordinator for the Edifier ES300 integration.

The speaker keeps a single long-lived TCP session. Once it's open the
``edifier_es300`` library's background reader dispatches every inbound frame,
and the speaker pushes ``heart_beat`` and ``status_query`` frames on its own --
so state changes (volume, track, source) reach Home Assistant in real time via
a ``status_callback``, with no polling.

We keep one connection per config entry. Rather than pinging to keep it alive,
we let the speaker's own heartbeats do that and run a passive watchdog: if no
frame (heartbeat or status) arrives within HEARTBEAT_TIMEOUT, we drop the
connection and the next watchdog tick reconnects.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from edifier_es300 import ES300, CommandFailed, EndOfStream, Status
from edifier_es300.typing_ import FrameData

from .const import (
    COMMAND_TIMEOUT,
    DEFAULT_PORT,
    DOMAIN,
    HEARTBEAT_TIMEOUT,
    WATCHDOG_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

type Action = Callable[[ES300], Awaitable[Any]]

# Failures that mean the connection is gone and we should reconnect.
_CONNECTION_ERRORS = (EndOfStream, OSError, TimeoutError)


class ES300DataUpdateCoordinator(DataUpdateCoordinator[Status]):
    """Owns the persistent connection, pushes status, and serialises commands."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.host: str = entry.data[CONF_HOST]
        self.port: int = entry.data.get(CONF_PORT, DEFAULT_PORT)
        self.device_name: str = entry.data.get(CONF_NAME) or self.host
        self.unique_id: str = entry.unique_id or f"{self.host}:{self.port}"
        self._device: ES300 | None = None
        self._last_frame: float = 0.0
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {self.device_name}",
            update_interval=WATCHDOG_INTERVAL,
            # Status is a dataclass (has __eq__), so let the refresh path skip
            # notifying listeners when a watchdog tick yields unchanged data.
            always_update=False,
        )

    # --- push handlers (fired from the library's background reader) ---
    async def _handle_status(self, status: Status) -> None:
        self._last_frame = self.hass.loop.time()
        if status.raw.get("name"):
            self.device_name = status.raw["name"]
        self.async_set_updated_data(status)

    async def _handle_heartbeat(self, _frame: FrameData) -> None:
        self._last_frame = self.hass.loop.time()

    # --- connection lifecycle ---
    async def _connect(self) -> Status:
        device = ES300(self.host, self.port, name=self.device_name)
        try:
            async with asyncio.timeout(COMMAND_TIMEOUT):
                await device.open()
            # edifier_es300<=1.0.3 types these callbacks as returning None, but
            # awaits them -- so they must be async. Drop the ignores once the
            # library annotates them as Awaitable[None].
            device.status_callback(self._handle_status)  # ty: ignore[invalid-argument-type]
            device.heartbeat_callback(self._handle_heartbeat)  # ty: ignore[invalid-argument-type]
            # Seed initial state; the device won't push a full status until
            # something changes, so ask once right after connecting.
            async with asyncio.timeout(COMMAND_TIMEOUT):
                status = await device.status()
        except _CONNECTION_ERRORS as err:
            await self._safe_close(device)
            raise UpdateFailed(
                f"cannot connect to {self.host}:{self.port}: {err}"
            ) from err
        if status is None:
            await self._safe_close(device)
            raise UpdateFailed("no status returned on connect")
        self._device = device
        self._last_frame = self.hass.loop.time()
        return status

    async def _safe_close(self, device: ES300) -> None:
        device.remove_status_callback(self._handle_status)  # ty: ignore[invalid-argument-type]
        device.remove_heartbeat_callback(self._handle_heartbeat)  # ty: ignore[invalid-argument-type]
        try:
            async with asyncio.timeout(COMMAND_TIMEOUT):
                await device.close()
        except (Exception, asyncio.CancelledError):  # noqa: BLE001 - best-effort close
            _LOGGER.debug("error while closing connection", exc_info=True)

    async def async_disconnect(self) -> None:
        """Tear down the connection (on error or unload)."""
        device, self._device = self._device, None
        if device is not None:
            await self._safe_close(device)

    # --- watchdog tick (no device I/O while healthy) ---
    async def _async_update_data(self) -> Status:
        if self._device is None:
            return await self._connect()
        silent_for = self.hass.loop.time() - self._last_frame
        if silent_for > HEARTBEAT_TIMEOUT:
            await self.async_disconnect()
            raise UpdateFailed(
                f"no frames from {self.host} for {silent_for:.0f}s; reconnecting"
            )
        # Healthy: pushes keep self.data fresh between ticks.
        return self.data

    # --- commands ---
    async def async_command(self, action: Action) -> None:
        """Run one command on the live connection.

        The device answers with a status_query push, so our status_callback
        updates state -- no explicit refresh needed.
        """
        if self._device is None:
            raise HomeAssistantError(f"{self.device_name} is not connected")
        try:
            async with asyncio.timeout(COMMAND_TIMEOUT):
                await action(self._device)
        except CommandFailed as err:
            raise HomeAssistantError(f"command rejected by device: {err}") from err
        except _CONNECTION_ERRORS as err:
            await self.async_disconnect()
            raise HomeAssistantError(f"lost connection to {self.host}: {err}") from err
