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

    # Serve the JS file
    hass.http.register_static_path(_CARD_URL, str(www_path), cache_headers=False)

    # Auto-register as Lovelace resource (only once)
    await _async_register_lovelace_resource(hass, _CARD_URL)

    return True


async def _async_register_lovelace_resource(hass: HomeAssistant, url: str) -> None:
    """Add the card JS as a Lovelace resource if not already present."""
    try:
        lovelace_data = hass.data.get("lovelace")
        if lovelace_data is None:
            return
        resources = lovelace_data.get("resources")
        if resources is None:
            return
        await resources.async_load(True)
        existing_urls = [r["url"] for r in resources.async_items()]
        if url not in existing_urls:
            await resources.async_create_item({"res_type": "module", "url": url})
            _LOGGER.info("Allsvenskan card registered as Lovelace resource: %s", url)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning(
            "Could not auto-register Lovelace resource %s: %s. "
            "Add it manually in Settings → Dashboards → Resources.",
            url,
            err,
        )


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
