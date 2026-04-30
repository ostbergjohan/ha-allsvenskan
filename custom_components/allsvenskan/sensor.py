"""Sensor platform for Allsvenskan integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AllsvenskanCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Allsvenskan sensors from a config entry."""
    coordinator: AllsvenskanCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [AllsvenskanTableSensor(coordinator, entry)]

    # Create one sensor per team in the standings
    if coordinator.data and coordinator.data.get("standings"):
        for row in coordinator.data["standings"]:
            entities.append(AllsvenskanTeamSensor(coordinator, entry, row["team"]))

    async_add_entities(entities, True)


class AllsvenskanTableSensor(CoordinatorEntity, SensorEntity):
    """Sensor that holds the full Allsvenskan standings table."""

    _attr_icon = "mdi:soccer"

    def __init__(self, coordinator: AllsvenskanCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_table"
        self._attr_name = "Allsvenskan Tabell"
        self._entry = entry

    @property
    def native_value(self) -> str | None:
        """Return the name of the current league leader."""
        if self.coordinator.data and self.coordinator.data.get("standings"):
            leader = self.coordinator.data["standings"][0]
            return leader.get("team")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the full standings table as attributes."""
        if not self.coordinator.data:
            return {}
        return {
            "season": self.coordinator.data.get("season"),
            "standings": self.coordinator.data.get("standings", []),
        }


class AllsvenskanTeamSensor(CoordinatorEntity, SensorEntity):
    """Sensor for an individual team's current standing."""

    _attr_icon = "mdi:soccer"

    def __init__(
        self,
        coordinator: AllsvenskanCoordinator,
        entry: ConfigEntry,
        team_name: str,
    ) -> None:
        super().__init__(coordinator)
        safe_name = team_name.lower().replace(" ", "_").replace("-", "_")
        self._attr_unique_id = f"{DOMAIN}_team_{safe_name}"
        self._attr_name = f"Allsvenskan {team_name}"
        self._team_name = team_name

    def _get_team_row(self) -> dict | None:
        if not self.coordinator.data:
            return None
        for row in self.coordinator.data.get("standings", []):
            if row.get("team") == self._team_name:
                return row
        return None

    @property
    def native_value(self) -> int | None:
        """Return position in the table."""
        row = self._get_team_row()
        return row.get("position") if row else None

    @property
    def native_unit_of_measurement(self) -> str:
        return "pos"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        row = self._get_team_row()
        if not row:
            return {}
        return {
            "team": row.get("team"),
            "points": row.get("points"),
            "played": row.get("played_games"),
            "won": row.get("won"),
            "draw": row.get("draw"),
            "lost": row.get("lost"),
            "goals_for": row.get("goals_for"),
            "goals_against": row.get("goals_against"),
            "goal_difference": row.get("goal_difference"),
            "crest": row.get("team_crest"),
        }
