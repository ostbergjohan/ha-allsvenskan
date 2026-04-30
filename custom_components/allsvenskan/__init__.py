"""Allsvenskan HACS Integration."""
from __future__ import annotations

import logging
import pathlib

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import AllsvenskanCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

_CARD_URL = f"/{DOMAIN}/allsvenskan-card.js"
_CARD_RESOURCE_URL = f"{_CARD_URL}?v=1"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Serve the Lovelace card JS as a static file."""
    www_path = pathlib.Path(__file__).parent / "www" / "allsvenskan-card.js"
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(_CARD_URL, str(www_path), False)]
        )
        _LOGGER.debug("Allsvenskan card static path registered at %s", _CARD_URL)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Could not register Allsvenskan card static path: %s", err)
    return True


async def _async_register_lovelace_resource(hass: HomeAssistant) -> None:
    """Register the card as a Lovelace resource so it appears in the card picker."""
    try:
        from homeassistant.components.lovelace.resources import ResourceStorageCollection  # noqa: PLC0415

        resources = hass.data.get("lovelace", {}).get("resources")
        if resources is None:
            return
        if not resources.loaded:
            await resources.async_load()
            resources.loaded = True

        for item in resources.async_items():
            if item["url"].startswith(_CARD_URL):
                return  # already registered

        if getattr(resources, "async_create_item", None):
            await resources.async_create_item(
                {"res_type": "module", "url": _CARD_RESOURCE_URL}
            )
            _LOGGER.info("Allsvenskan card registered as Lovelace resource")
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Could not register Lovelace resource: %s", err)



async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Allsvenskan from a config entry."""
    coordinator = AllsvenskanCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await _async_register_lovelace_resource(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
