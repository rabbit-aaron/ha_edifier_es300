"""Config flow for the Edifier ES300 integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT

from edifier_es300.discovery import DiscoveredDevice, discover

from .const import DEFAULT_PORT, DOMAIN


def _unique_id(device: DiscoveredDevice) -> str:
    """Stable id for a discovered speaker (uuid/MAC preferred, host as fallback)."""
    return str(device.uuid or device.wifi_mac or device.host)


class ES300ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Edifier ES300."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered: dict[str, DiscoveredDevice] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manual host/port entry, or blank host to auto-discover."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = (user_input.get(CONF_HOST) or "").strip()
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            if host:
                return await self._create(host, port, name=None, unique_id=None)

            # No host: broadcast-discover speakers on the LAN and cache them.
            found = await discover()
            configured = self._async_current_ids()
            available = {
                _unique_id(device): device
                for device in found
                if _unique_id(device) not in configured
            }
            if not found:
                errors["base"] = "no_devices_found"
            elif not available:
                return self.async_abort(reason="already_configured")
            else:
                self._discovered = available
                if len(available) == 1:
                    device = next(iter(available.values()))
                    return await self._create(
                        device.host or device.address,
                        device.port or DEFAULT_PORT,
                        name=device.name,
                        unique_id=_unique_id(device),
                    )
                return await self.async_step_pick()

        schema = vol.Schema(
            {
                vol.Optional(CONF_HOST, default=""): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_pick(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose which discovered speaker to add when several were found."""
        if user_input is not None:
            device = self._discovered[user_input["device"]]
            return await self._create(
                device.host or device.address,
                device.port or DEFAULT_PORT,
                name=device.name,
                unique_id=user_input["device"],
            )

        choices = {
            unique_id: f"{device.name or 'ES300'} ({device.host or device.address})"
            for unique_id, device in self._discovered.items()
        }
        schema = vol.Schema({vol.Required("device"): vol.In(choices)})
        return self.async_show_form(step_id="pick", data_schema=schema)

    async def _create(
        self, host: str, port: int, name: str | None, unique_id: str | None
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(unique_id or f"{host}:{port}")
        self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})
        title = name or host
        return self.async_create_entry(
            title=title,
            data={CONF_HOST: host, CONF_PORT: port, CONF_NAME: title},
        )
