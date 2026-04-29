"""Constants for Allsvenskan integration."""

DOMAIN = "allsvenskan"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 3600  # seconds (1 hour)

# Sofascore – Allsvenskan unique-tournament id = 40
SOFASCORE_SEASONS_URL = "https://api.sofascore.com/api/v1/unique-tournament/40/seasons"
SOFASCORE_STANDINGS_URL = "https://api.sofascore.com/api/v1/unique-tournament/40/season/{season_id}/standings/total"

ATTR_POSITION = "position"
ATTR_TEAM = "team"
ATTR_PLAYED = "played_games"
ATTR_WON = "won"
ATTR_DRAW = "draw"
ATTR_LOST = "lost"
ATTR_GOALS_FOR = "goals_for"
ATTR_GOALS_AGAINST = "goals_against"
ATTR_GOAL_DIFFERENCE = "goal_difference"
ATTR_POINTS = "points"
ATTR_TABLE = "standings"
