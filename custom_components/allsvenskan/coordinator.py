"""Data coordinator for Allsvenskan integration."""
from __future__ import annotations

import asyncio
import base64
import logging
from datetime import datetime, timedelta, timezone

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

_IMAGE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "image/png,image/svg+xml,image/*,*/*",
    "Referer": "https://www.sofascore.com/",
}

_LOGO_HOSTS = (
    "api.sofascore.com",
    "www.sofascore.com",
    "img.sofascore.com",
)
_LOGO_RETRY_COOLDOWN = timedelta(hours=5)


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
        # In-memory logo cache: team_id (int) → base64 data URL string.
        # Populated from the persistent store on first successful standings fetch
        # and refreshed whenever new team IDs are seen.
        self._logo_cache: dict[int, str] = {}
        # When logo fetch fails/challenges, wait before trying again per team.
        self._logo_retry_after: dict[int, datetime] = {}

    async def _fetch_logo(self, team_id: int) -> str | None:
        """Fetch a team logo from Sofascore and return it as a base64 data URL.

        Results are kept in *_logo_cache* so each team is fetched at most once
        per HA process lifetime.  Failures are silently ignored (returns None).
        """
        if team_id in self._logo_cache:
            return self._logo_cache[team_id]
        now = datetime.now(timezone.utc)
        retry_after = self._logo_retry_after.get(team_id)
        if retry_after and now < retry_after:
            return None
        timeout = aiohttp.ClientTimeout(total=10)
        for host in _LOGO_HOSTS:
            url = f"https://{host}/api/v1/team/{team_id}/image"
            try:
                async with self.session.get(
                    url, headers=_IMAGE_HEADERS, timeout=timeout
                ) as resp:
                    if resp.status != 200:
                        _LOGGER.debug(
                            "Logo fetch for team %s via %s returned HTTP %s",
                            team_id,
                            host,
                            resp.status,
                        )
                        continue
                    content_type = resp.headers.get("Content-Type", "image/png")
                    # Ignore challenge pages served as HTML.
                    if not content_type.lower().startswith("image/"):
                        _LOGGER.debug(
                            "Logo fetch for team %s via %s returned non-image content type: %s",
                            team_id,
                            host,
                            content_type,
                        )
                        continue
                    # Strip charset / boundary directives
                    if ";" in content_type:
                        content_type = content_type.split(";")[0].strip()
                    data = await resp.read()
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Logo fetch for team %s via %s failed: %s", team_id, host, err)
                continue

            data_url = "data:" + content_type + ";base64," + base64.b64encode(data).decode("ascii")
            self._logo_cache[team_id] = data_url
            self._logo_retry_after.pop(team_id, None)
            return data_url

        self._logo_retry_after[team_id] = now + _LOGO_RETRY_COOLDOWN
        return None

    @staticmethod
    def _fallback_logo_url(team_id: int) -> str:
        """Return a direct URL fallback for environments where base64 fetch fails."""
        return f"https://img.sofascore.com/api/v1/team/{team_id}/image"

    @staticmethod
    def _generated_logo_data_url(
        team_name: str | None,
        team_short: str | None,
        primary_color: str | None,
        text_color: str | None,
    ) -> str:
        """Generate a simple SVG badge so cards always have a local image fallback."""
        label_src = (team_short or team_name or "?").strip()
        initials = "".join(ch for ch in label_src if ch.isalnum())[:3].upper() or "?"
        bg = primary_color or "#1f6f43"
        fg = text_color or "#ffffff"
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 72 72'>"
            f"<rect width='72' height='72' rx='14' fill='{bg}'/>"
            f"<text x='36' y='46' text-anchor='middle' font-size='24' "
            f"font-family='Arial, sans-serif' font-weight='700' fill='{fg}'>{initials}</text>"
            "</svg>"
        )
        return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")

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
                # Restore logo cache so team sensors still show crests
                for row in cached.get("standings", []):
                    tid = row.get("team_id")
                    logo = row.get("team_logo", "")
                    if tid and logo.startswith("data:"):
                        self._logo_cache[tid] = logo
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
                        "team_primary_color": team.get("teamColors", {}).get("primary"),
                        "team_text_color": team.get("teamColors", {}).get("text"),
                        "team_id": team_id,
                        "team_logo": None,  # filled in below after logo fetch
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

        # Fetch logos as base64 data URLs so they are CSP-safe and not subject
        # to Sofascore hotlink protection when rendered in the browser.
        team_ids = [r["team_id"] for r in standings if r.get("team_id")]
        logo_results = await asyncio.gather(
            *[self._fetch_logo(tid) for tid in team_ids],
        )
        logo_map: dict[int, str] = {
            tid: url
            for tid, url in zip(team_ids, logo_results)
            if url is not None
        }
        for row in standings:
            tid = row.get("team_id")
            if tid:
                row["team_logo"] = (
                    logo_map.get(tid)
                    or self._generated_logo_data_url(
                        row.get("team"),
                        row.get("team_short"),
                        row.get("team_primary_color"),
                        row.get("team_text_color"),
                    )
                    or self._fallback_logo_url(tid)
                )

        result = {
            "season": season_year,
            "season_id": season_id,
            "standings": standings,
        }

        # Persist successful result (including base64 logos) for future fallback
        await self._store.async_save(result)
        return result
