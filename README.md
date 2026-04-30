# Allsvenskan – Home Assistant Integration

![version](https://img.shields.io/badge/version-1.0.7-blue) ![hacs](https://img.shields.io/badge/HACS-Custom-orange)

Home Assistant-integration som visar aktuell ligatabell för **Allsvenskan** med laglogotyper, poäng, mål och zonmarkering direkt i ditt dashboard. Data hämtas från [Sofascore](https://www.sofascore.com/) – ingen API-nyckel krävs.

---

## Funktioner

- 📋 Inbyggt **Lovelace-kort** med laglogotyper och färgkodade zoner
- 📡 Sensor med **hela ligatabellen** som attribut (`sensor.allsvenskan_tabell`)
- ⚽ En sensor **per lag** med aktuell tabellplats och detaljstatistik
- 🔄 Uppdateras automatiskt var **60:e minut**
- 🔑 Ingen API-nyckel krävs

---

## Installation via HACS

1. Gå till **HACS → Integrationer → ⋮ → Anpassade arkiv**
2. Lägg till `https://github.com/ostbergjohan/ha-allsvenskan` som **Integration**
3. Sök efter **Allsvenskan** och klicka **Ladda ned**
4. **Starta om Home Assistant**
5. Gå till **Inställningar → Enheter & tjänster → Lägg till integration → Allsvenskan**
6. Klicka **Skicka** – ingen konfiguration behövs

Lovelace-kortet registreras och laddas automatiskt – ingen manuell resurskonfiguration behövs.

---

## Lovelace-kort

Lägg till kortet på din dashboard via **Redigera dashboard → Lägg till kort → Anpassat: Allsvenskan Tabell**, eller manuellt:

```yaml
type: custom:allsvenskan-card
entity: sensor.allsvenskan_tabell
```

### Zonmarkering

| Färg | Zon |
|---|---|
| 🔵 Blå | Champions League-kval (plats 1) |
| 🟠 Orange | Europa-kval (plats 2–3) |
| 🟤 Brun | Kvalserie nedflyttning (plats 14) |
| 🔴 Röd | Direkt nedflyttning (plats 15–16) |

---

## Sensorer

### `sensor.allsvenskan_tabell`

Representerar **hela ligatabellen**.

| | |
|---|---|
| **State** | Ligaledarens namn |
| **Attribut** | `season`, `standings` |

`standings` är en lista med ett objekt per lag:

```json
{
  "position": 1,
  "team": "Malmö FF",
  "team_short": "MFF",
  "team_id": 3629,
  "team_logo": "https://api.sofascore.com/api/v1/team/3629/image",
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

### `sensor.allsvenskan_<lagnamn>`

En sensor per lag, t.ex. `sensor.allsvenskan_malmo_ff`.

| | |
|---|---|
| **State** | Tabellplacering (heltal) |
| **Enhet** | `pos` |
| **Attribut** | `team`, `points`, `played`, `won`, `draw`, `lost`, `goals_for`, `goals_against`, `goal_difference`, `crest` |

---

## Datakälla

Data hämtas från [Sofascore API](https://www.sofascore.com/) (Allsvenskan, unik turnerings-id 40). Ingen registrering eller API-nyckel krävs. Uppdatering sker var 60:e minut.

---

## Licens

MIT – se [LICENSE](LICENSE) för detaljer.
