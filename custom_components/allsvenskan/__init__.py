"""Allsvenskan HACS Integration."""
from __future__ import annotations

import logging
import pathlib

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import AllsvenskanCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

_CARD_URL = f"/{DOMAIN}/allsvenskan-card.js"
_CARD_VERSION = "2"  # bump this to bust browser cache after updates


async def _register_lovelace_resource(hass: HomeAssistant) -> None:
    """Register the card JS as a Lovelace resource, mirroring browser_mod's approach."""
    url_base = _CARD_URL
    url_versioned = f"{_CARD_URL}?v={_CARD_VERSION}"

    try:
        resources = hass.data["lovelace"].resources
    except (KeyError, AttributeError):
        _LOGGER.warning("Allsvenskan: lovelace not available, card resource not registered")
        return

    if not resources.loaded:
        await resources.async_load()
        resources.loaded = True

    # Check for existing entry and update version if needed
    for item in resources.async_items():
        if item.get("url", "").startswith(url_base):
            if item["url"] != url_versioned and isinstance(resources, ResourceStorageCollection):
                await resources.async_update_item(
                    item["id"], {"res_type": "module", "url": url_versioned}
                )
                _LOGGER.info("Allsvenskan: updated Lovelace resource to %s", url_versioned)
            return

    # Not found – create it
    if isinstance(resources, ResourceStorageCollection):
        await resources.async_create_item({"res_type": "module", "url": url_versioned})
        _LOGGER.info("Allsvenskan: registered Lovelace resource %s", url_versioned)
    else:
        # YAML-mode lovelace – fall back to in-memory append
        if hasattr(resources, "data") and hasattr(resources.data, "append"):
            resources.data.append({"type": "module", "url": url_versioned})


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Serve the card JS as a static file and inject it via add_extra_js_url."""
    base = pathlib.Path(__file__).parent
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(_CARD_URL, str(base / "www" / "allsvenskan-card.js"), False)]
        )
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Allsvenskan: could not register static path: %s", err)

    # Injects the JS on every page load (effective immediately if called before frontend init)
    add_extra_js_url(hass, f"{_CARD_URL}?v={_CARD_VERSION}")
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

    # Register card in Lovelace resource storage
    await _register_lovelace_resource(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
