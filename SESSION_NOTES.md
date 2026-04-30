# Session Notes – Last updated 2026-04-30

## Current version: v1.1.9

## Repo
https://github.com/ostbergjohan/ha-allsvenskan

## Status
- ✅ Integration installs via HACS
- ✅ Sofascore API working (season 2026, id=87925, all 16 teams)
- ✅ sensor.allsvenskan_tabell populates with standings
- ✅ Team sensors created (one per team)
- ✅ Persistent cache fallback when Sofascore unreachable
- ✅ Sensor stays available when using cached data
- ✅ brand/icon.png exists at correct path
- ⚠️ Icon still not showing in HA UI — needs cached 404 deleted: `/config/.storage/brands/integrations/allsvenskan/icon.png`
- ⚠️ Card (custom:allsvenskan-card) — worked once after manual resource registration, then broke again. Last fix: rewrote JS from scratch (v1.1.9) clean ASCII-only

## Card registration (manual, one-time)
Settings → Dashboards → ⋮ → Resources → Add Resource
- URL: `/allsvenskan/allsvenskan-card.js`
- Type: JavaScript Module
Then hard-refresh browser (Ctrl+Shift+R)

## Card usage
```yaml
type: custom:allsvenskan-card
```

## File structure
```
custom_components/allsvenskan/
  __init__.py         # async_setup registers static paths; async_setup_entry sets up coordinator
  coordinator.py      # fetches Sofascore, persistent Store cache fallback
  sensor.py           # AllsvenskanTableSensor + AllsvenskanTeamSensor, overrides available
  manifest.json       # v1.1.9, no after_dependencies
  const.py            # URLs, constants
  config_flow.py      # simple no-config flow
  brand/icon.png      # 256x256 integration icon
  www/allsvenskan-card.js  # Lovelace card, pure ASCII JS
```

## Key URLs
- Seasons: https://api.sofascore.com/api/v1/unique-tournament/40/seasons
- Standings: https://api.sofascore.com/api/v1/unique-tournament/40/season/{season_id}/standings/total
- Card served at: /allsvenskan/allsvenskan-card.js

## Known issues to investigate next session
1. Card "custom element not found" keeps recurring — suspect HA browser cache or static path not re-registering after reload (only registers on full restart via async_setup)
2. Icon cached 404 in /config/.storage/brands/integrations/allsvenskan/icon.png — user needs to delete manually
3. Consider packaging card separately as a HACS plugin (Dashboard category) so HACS handles resource registration automatically

## What to try if card still broken
- Open browser DevTools F12 → Console → share exact error
- Verify /allsvenskan/allsvenskan-card.js loads in browser after full HA restart
- Full pod/host restart (not just HA restart) if static path not registering
