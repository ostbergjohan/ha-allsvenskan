"""Allsvenskan HACS Integration."""
from __future__ import annotations

import logging
import pathlib

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import AllsvenskanCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

_CARD_URL = f"/{DOMAIN}/allsvenskan-card.js"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register static path for the Lovelace card."""
    www_path = pathlib.Path(__file__).parent / "www" / "allsvenskan-card.js"
    try:
        hass.http.register_static_path(_CARD_URL, str(www_path), cache_headers=False)
    except TypeError:
        # Newer HA versions dropped the cache_headers parameter
        try:
            hass.http.register_static_path(_CARD_URL, str(www_path))
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Could not register static path for card: %s", err)
    _LOGGER.info(
        "Allsvenskan card available at %s. "
        "Add it manually in Settings → Dashboards → Resources if needed.",
        _CARD_URL,
    )
    return True



async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Allsvenskan from a config entry."""
    coordinator = AllsvenskanCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
