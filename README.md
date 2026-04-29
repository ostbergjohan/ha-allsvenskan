# ha-allsvenskan

Home Assistant-integration som visar aktuell ligatabell för Allsvenskan med laglogotyper, poäng, mål och zonmarkering direkt i ditt dashboard. Data hämtas från Sofascore – ingen API-nyckel krävs.

## Funktioner

- Inbyggt **Lovelace-kort** med laglogotyper och färgkodade zoner
- Sensor med **hela ligatabellen** som attribut (`sensor.allsvenskan_tabell`)
- En sensor **per lag** med aktuell tabellplats och detaljstatistik
- Uppdateras automatiskt var **60:e minut**
- Ingen API-nyckel krävs

## Installation via HACS

1. Gå till **HACS → Integrationer → ⋮ → Anpassade arkiv**
2. Lägg till `https://github.com/ostbergjohan/ha-allsvenskan` (kategori: Integration)
3. Sök efter **Allsvenskan** och installera
4. Starta om Home Assistant
5. Gå till **Inställningar → Enheter & tjänster → Lägg till integration → Allsvenskan**

Lovelace-kortet registreras automatiskt – ingen manuell resurskonfiguration behövs.

## Lovelace-kort

Lägg till kortet på din dashboard:

```yaml
type: custom:allsvenskan-card
entity: sensor.allsvenskan_tabell
```

## Sensorer

### `sensor.allsvenskan_tabell`
- **state:** Ligaledarens namn
- **attribut:** `season`, `standings` – lista med alla lag och statistik

### `sensor.allsvenskan_<lagnamn>`
- **state:** Tabellplacering
- **attribut:** poäng, matcher, vinster, oavgjorda, förluster, gjorda/insläppta mål, målskillnad, laglogotyp

## Licens

MIT
