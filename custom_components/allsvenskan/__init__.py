"""Allsvenskan HACS Integration."""
from __future__ import annotations

import logging
import pathlib
import uuid

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .coordinator import AllsvenskanCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

_CARD_URL = f"/{DOMAIN}/allsvenskan-card.js"
_LOVELACE_RESOURCES_KEY = "lovelace_resources"


async def _ensure_lovelace_resource(hass: HomeAssistant, url: str) -> None:
    """Add the card URL to Lovelace resources storage if not already present."""
    store = Store(hass, 1, _LOVELACE_RESOURCES_KEY)
    data = await store.async_load() or {"items": []}
    items = data.setdefault("items", [])
    if any(item.get("url") == url for item in items):
        return
    items.append({"id": uuid.uuid4().hex, "type": "module", "url": url})
    await store.async_save(data)
    _LOGGER.debug("Allsvenskan: added Lovelace resource %s", url)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Serve the Lovelace card JS and icon as static files."""
    base = pathlib.Path(__file__).parent
    paths = [
        StaticPathConfig(_CARD_URL, str(base / "www" / "allsvenskan-card.js"), False),
        StaticPathConfig(f"/{DOMAIN}/icon.png", str(base / "brand" / "icon.png"), True),
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
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:  # noqa: BLE001
        _LOGGER.warning("Allsvenskan: initial fetch failed, will retry on schedule.")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Persist card in Lovelace resources so it survives restarts
    try:
        await _ensure_lovelace_resource(hass, _CARD_URL)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Could not register Allsvenskan Lovelace resource: %s", err)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
