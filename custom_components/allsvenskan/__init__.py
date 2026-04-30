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


async def _ensure_lovelace_resource(hass: HomeAssistant, url: str) -> None:
    """Persist card in Lovelace resources storage (survives restarts)."""
    store = Store(hass, 1, "lovelace.resources")
    data = await store.async_load() or {"items": []}
    items = data.setdefault("items", [])
    if any(item.get("url") == url for item in items):
        _LOGGER.debug("Allsvenskan: Lovelace resource already registered")
        return
    items.append({"id": uuid.uuid4().hex, "res_type": "module", "url": url})
    await store.async_save(data)
    _LOGGER.info("Allsvenskan: registered Lovelace resource %s", url)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Serve the Lovelace card JS as a static file."""
    base = pathlib.Path(__file__).parent
    paths = [
        StaticPathConfig(_CARD_URL, str(base / "www" / "allsvenskan-card.js"), False),
    ]
    try:
        await hass.http.async_register_static_paths(paths)
        _LOGGER.debug("Allsvenskan static paths registered: %s", _CARD_URL)
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

    try:
        await _ensure_lovelace_resource(hass, _CARD_URL)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Allsvenskan: could not register Lovelace resource: %s", err)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
