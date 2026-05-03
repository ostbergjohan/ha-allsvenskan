# Allsvenskan – Home Assistant Integration

![version](https://img.shields.io/badge/version-1.1.2-blue) ![hacs](https://img.shields.io/badge/HACS-Custom-orange)

Home Assistant integration that displays the current **Allsvenskan** standings table with team logos, points, goals and zone highlighting directly in your dashboard. Data is fetched from [Sofascore](https://www.sofascore.com/) — no API key required.

![Allsvenskan Card](https://raw.githubusercontent.com/ostbergjohan/ha-allsvenskan/main/screentshot.png)

---

## Features

- 📋 Built-in **Lovelace card** with team logos and color-coded zones
- 📡 Sensor with the **full standings table** as attributes (`sensor.allsvenskan_tabell`)
- ⚽ One sensor **per team** with current position and detailed statistics
- 🔄 Automatically updated every **60 minutes**
- 🔑 No API key required

---

## Installation via HACS

1. Go to **HACS → Integrations → ⋮ → Custom repositories**
2. Add `https://github.com/ostbergjohan/ha-allsvenskan` as **Integration**
3. Search for **Allsvenskan** and click **Download**
4. **Restart Home Assistant**
5. Go to **Settings → Devices & Services → Add Integration → Allsvenskan**
6. Click **Submit** — no configuration needed

After restart, **add the card resource once**:

7. Go to **Settings → Dashboards → ⋮ (top right) → Resources**
8. Click **Add Resource**
9. URL: `/allsvenskan/allsvenskan-card.js`
10. Type: **JavaScript Module**
11. Click **Create** — then hard-refresh your browser (Ctrl+Shift+R)

---

## Lovelace Card

Add the card to your dashboard via **Edit Dashboard → Add Card → Custom: Allsvenskan Tabell**, or manually:

```yaml
type: custom:allsvenskan-card
entity: sensor.allsvenskan_tabell  # optional, this is the default
max_rows: 6                         # optional, default shows all 16 teams
favorite_team: Hammarby IF          # optional, highlights the matching row in yellow
```

### Zone highlighting

| Color | Zone |
|---|---|
| 🔵 Blue | Champions League qualification (position 1) |
| 🟠 Orange | European qualification (positions 2–3) |
| 🟤 Brown | Relegation playoff (position 14) |
| 🔴 Red | Direct relegation (positions 15–16) |

---

## Sensors

### `sensor.allsvenskan_tabell`

Represents the **full standings table**.

| | |
|---|---|
| **State** | Name of the current league leader |
| **Attributes** | `season`, `standings` |

`standings` is a list with one object per team:

```json
{
  "position": 1,
  "team": "Hammarby IF",
  "team_short": "HIF",
  "team_id": 3211,
  "team_logo": "https://api.sofascore.com/api/v1/team/3211/image",
  "played_games": 10,
  "won": 7,
  "draw": 2,
  "lost": 1,
  "goals_for": 22,
  "goals_against": 9,
  "goal_difference": 13,
  "points": 23
}
```

---

### `sensor.allsvenskan_<team_name>`

One sensor per team, e.g. `sensor.allsvenskan_hammarby_if`.

| | |
|---|---|
| **State** | Table position (integer) |
| **Unit** | `pos` |
| **Attributes** | `team`, `points`, `played`, `won`, `draw`, `lost`, `goals_for`, `goals_against`, `goal_difference`, `crest` |

---

## Data Source

Data is fetched from the [Sofascore API](https://www.sofascore.com/) (Allsvenskan, unique tournament id 40). No account or API key required. Updates every 60 minutes.

---

## License

MIT – see [LICENSE](LICENSE) for details.
