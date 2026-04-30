"""Data coordinator for Allsvenskan integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store

from .const import (
    DOMAIN,
    SOFASCORE_SEASONS_URL,
    SOFASCORE_STANDINGS_URL,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)
_STORAGE_KEY = f"{DOMAIN}.cache"
_STORAGE_VERSION = 1

# Sofascore blocks default aiohttp UA – use a browser-like one
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


class AllsvenskanCoordinator(DataUpdateCoordinator):
    """Coordinator that fetches Allsvenskan standings from Sofascore."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.session = async_get_clientsession(hass)
        self._store = Store(hass, _STORAGE_VERSION, _STORAGE_KEY)

    async def _async_update_data(self):
        """Fetch standings from Sofascore, falling back to cached data on failure."""
        timeout = aiohttp.ClientTimeout(total=15)

        try:
            # Step 1 – resolve the current season id
            async with self.session.get(
                SOFASCORE_SEASONS_URL, headers=_HEADERS, timeout=timeout
            ) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"Seasons endpoint returned HTTP {resp.status}")
                seasons_data = await resp.json()

            seasons = seasons_data.get("seasons", [])
            if not seasons:
                raise UpdateFailed("No seasons found in Sofascore response")

            # Sofascore returns seasons newest-first
            current_season = seasons[0]
            season_id = current_season["id"]
            season_year = current_season.get("year", str(current_season.get("id")))
            _LOGGER.debug("Using Sofascore season id=%s year=%s", season_id, season_year)

            # Step 2 – fetch standings for that season
            standings_url = SOFASCORE_STANDINGS_URL.format(season_id=season_id)
            async with self.session.get(
                standings_url, headers=_HEADERS, timeout=timeout
            ) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"Standings endpoint returned HTTP {resp.status}")
                standings_data = await resp.json()

        except Exception as err:  # noqa: BLE001
            # Return cached data so sensors stay available
            cached = await self._store.async_load()
            if cached:
                _LOGGER.warning(
                    "Sofascore fetch failed (%s). Using cached standings from last successful update.",
                    err,
                )
                return cached
            raise UpdateFailed(f"Error communicating with Sofascore: {err}") from err

        standings = []
        # Sofascore wraps rows inside standings[0].rows
        for group in standings_data.get("standings", []):
            for row in group.get("rows", []):
                team = row.get("team", {})
                team_id = team.get("id")
                standings.append(
                    {
                        "position": row.get("position"),
                        "team": team.get("name"),
                        "team_short": team.get("shortName"),
                        "team_id": team_id,
                        "team_logo": f"https://api.sofascore.com/api/v1/team/{team_id}/image" if team_id else None,
                        "played_games": row.get("matches"),
                        "won": row.get("wins"),
                        "draw": row.get("draws"),
                        "lost": row.get("losses"),
                        "goals_for": row.get("scoresFor"),
                        "goals_against": row.get("scoresAgainst"),
                        "goal_difference": row.get("scoresFor", 0) - row.get("scoresAgainst", 0),
                        "points": row.get("points"),
                    }
                )
            break  # only the first (total) group

        result = {
            "season": season_year,
            "season_id": season_id,
            "standings": standings,
        }

        # Persist successful result for future fallback
        await self._store.async_save(result)
        return result
