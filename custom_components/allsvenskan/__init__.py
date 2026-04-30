"""Allsvenskan HACS Integration."""
from __future__ import annotations

import logging
import pathlib

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import AllsvenskanCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

_CARD_URL = f"/{DOMAIN}/allsvenskan-card.js"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Serve the Lovelace card JS and icon as static files."""
    base = pathlib.Path(__file__).parent
    paths = [
        StaticPathConfig(_CARD_URL, str(base / "www" / "allsvenskan-card.js"), False),
        StaticPathConfig(f"/{DOMAIN}/icon.png", str(base / "icon.png"), True),
    ]
    try:
        await hass.http.async_register_static_paths(paths)
        _LOGGER.debug("Allsvenskan static paths registered")
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Could not register Allsvenskan static paths: %s", err)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Allsvenskan from a config entry."""
    coordinator = AllsvenskanCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register card as extra module — frontend is guaranteed to be set up here
    try:
        add_extra_js_url(hass, _CARD_URL)
        _LOGGER.debug("Allsvenskan card registered as extra module: %s", _CARD_URL)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Could not register Allsvenskan card as extra module: %s", err)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
