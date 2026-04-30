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


async def _register_lovelace_resource(hass: HomeAssistant, url: str) -> None:
    """Register the card JS as a Lovelace resource using HA's internal resource collection."""
    try:
        resources = hass.data["lovelace"]["resources"]
    except KeyError:
        _LOGGER.warning("Allsvenskan: lovelace resources not available yet, skipping resource registration")
        return

    # Ensure the collection is loaded
    if not resources.loaded:
        await resources.async_load()
        resources.loaded = True

    # Check if already registered
    for item in resources.async_items():
        if item.get("url", "").startswith(url):
            _LOGGER.debug("Allsvenskan: Lovelace resource already registered")
            return

    # Register it
    await resources.async_create_item({"res_type": "module", "url": url})
    _LOGGER.info("Allsvenskan: registered Lovelace resource %s", url)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Serve the Lovelace card JS as a static file."""
    base = pathlib.Path(__file__).parent
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(_CARD_URL, str(base / "www" / "allsvenskan-card.js"), False)]
        )
        _LOGGER.debug("Allsvenskan: static path registered %s", _CARD_URL)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Allsvenskan: could not register static path: %s", err)

    # add_extra_js_url injects the JS on every page load (works if called before frontend loads)
    add_extra_js_url(hass, _CARD_URL)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Allsvenskan from a config entry."""
    coordinator = AllsvenskanCoordinator(hass)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:  # noqa: BLE001
        _LOGGER.warning("Allsvenskan: initial fetch failed, will retry on schedule.")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register via Lovelace resource storage (visible under Settings → Dashboards → Resources)
    await _register_lovelace_resource(hass, _CARD_URL)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
