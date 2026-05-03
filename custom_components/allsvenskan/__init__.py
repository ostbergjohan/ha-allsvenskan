"""Allsvenskan HACS Integration."""
from __future__ import annotations

import logging
import pathlib

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN
from .coordinator import AllsvenskanCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [Platform.SENSOR]

_CARD_URL = f"/{DOMAIN}/allsvenskan-card.js"
_TEAM_CARD_URL = f"/{DOMAIN}/allsvenskan-team-card.js"
_CARD_VERSION = "4"  # bump this to bust browser cache after updates


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Serve the card JS as a static file and inject it via add_extra_js_url."""
    www_dir = pathlib.Path(__file__).parent / "www"
    js_path = str(www_dir / "allsvenskan-card.js")
    team_js_path = str(www_dir / "allsvenskan-team-card.js")

    # Register static paths – try modern API first, fall back to legacy
    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(_CARD_URL, js_path, False),
                StaticPathConfig(_TEAM_CARD_URL, team_js_path, False),
            ]
        )
    except (ImportError, AttributeError):
        # Older HA versions without StaticPathConfig / async_register_static_paths
        try:
            hass.http.register_static_path(_CARD_URL, js_path, False)
            hass.http.register_static_path(_TEAM_CARD_URL, team_js_path, False)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Allsvenskan: could not register static path: %s", err)
            return True
    except Exception as err:  # noqa: BLE001
        _LOGGER.error("Allsvenskan: could not register static path: %s", err)
        return True

    # Inject both card JS files
    for card_url in (_CARD_URL, _TEAM_CARD_URL):
        url = f"{card_url}?v={_CARD_VERSION}"
        add_extra_js_url(hass, url)
        _LOGGER.info("Allsvenskan: card JS registered at %s", url)
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
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
