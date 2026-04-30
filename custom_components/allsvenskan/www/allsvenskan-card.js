class AllsvenskanCard extends HTMLElement {
  set hass(hass) {
    if (!this.content) {
      this._build();
    }
    const entity = this.config.entity || "sensor.allsvenskan_tabell";
    const stateObj = hass.states[entity];
    if (!stateObj) {
      this.content.innerHTML = `<p class="error">Entity ${entity} not found.</p>`;
      return;
    }
    const standings = stateObj.attributes.standings || [];
    const season = stateObj.attributes.season || "";
    const maxRows = this.config.max_rows ? parseInt(this.config.max_rows) : standings.length;
    this._render(standings.slice(0, maxRows), season);
  }

  setConfig(config) {
    this.config = config;
  }

  getCardSize() {
    const rows = this.config && this.config.max_rows ? parseInt(this.config.max_rows) : 16;
    return Math.ceil(rows / 2) + 2;
  }

  _build() {
    const shadow = this.attachShadow({ mode: "open" });

    const style = document.createElement("style");
    style.textContent = `
      ha-card {
        padding: 0;
        overflow: hidden;
      }
      .header {
        background: linear-gradient(135deg, #1a6b3a 0%, #0d4a28 100%);
        color: #fff;
        padding: 14px 16px;
        font-size: 1.1em;
        font-weight: 700;
        letter-spacing: 0.04em;
        display: flex;
        align-items: center;
        gap: 10px;
      }
      .header img {
        height: 28px;
        width: auto;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.88em;
      }
      thead tr {
        background: #f4f4f4;
        color: #555;
        font-weight: 600;
        font-size: 0.78em;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
      thead th {
        padding: 6px 8px;
        text-align: center;
        white-space: nowrap;
      }
      thead th.team-col {
        text-align: left;
        padding-left: 10px;
      }
      tbody tr {
        border-bottom: 1px solid #f0f0f0;
        transition: background 0.15s;
      }
      tbody tr:hover {
        background: #f9f9f9;
      }
      tbody tr.promotion-cl { border-left: 3px solid #1565C0; }
      tbody tr.promotion-euro { border-left: 3px solid #F57F17; }
      tbody tr.relegation-playoff { border-left: 3px solid #E65100; }
      tbody tr.relegation { border-left: 3px solid #B71C1C; }
      tbody tr.favorite {
        background: #fffde7;
        font-weight: 600;
      }
      tbody tr.favorite td.team-col .team-name {
        font-weight: 700;
      }
      tbody tr.favorite:hover { background: #fff9c4; }
      td {
        padding: 7px 8px;
        text-align: center;
        vertical-align: middle;
      }
      td.team-col {
        text-align: left;
        display: flex;
        align-items: center;
        gap: 8px;
        padding-left: 10px;
      }
      td.team-col img {
        width: 22px;
        height: 22px;
        object-fit: contain;
        flex-shrink: 0;
      }
      td.team-col .team-name {
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 130px;
      }
      td.pos {
        font-weight: 700;
        color: #333;
        width: 28px;
      }
      td.pts {
        font-weight: 800;
        color: #1a6b3a;
        font-size: 0.95em;
      }
      td.gd.pos-val { color: #2e7d32; }
      td.gd.neg-val { color: #c62828; }
      .error { color: red; padding: 12px; }
    `;

    const card = document.createElement("ha-card");
    this.content = document.createElement("div");
    card.appendChild(this.content);
    shadow.appendChild(style);
    shadow.appendChild(card);
  }

  _zoneClass(position) {
    if (position === 1) return "promotion-cl";
    if (position <= 3) return "promotion-euro";
    if (position === 14) return "relegation-playoff";
    if (position >= 15) return "relegation";
    return "";
  }

  _render(standings, season) {
    const favorite = (this.config.favorite_team || "").toLowerCase();
    const rows = standings.map((t) => {
      const gd = t.goal_difference;
      const gdFormatted = gd > 0 ? `+${gd}` : `${gd}`;
      const gdClass = gd > 0 ? "pos-val" : gd < 0 ? "neg-val" : "";
      const zone = this._zoneClass(t.position);
      const isFav = favorite && (t.team || "").toLowerCase().includes(favorite);
      const logo = t.team_logo
        ? `<img src="${t.team_logo}" alt="${t.team_short || t.team}" loading="lazy" onerror="this.style.display='none'">`
        : `<img style="display:none">`;

      return `
        <tr class="${zone}${isFav ? " favorite" : ""}">
          <td class="pos">${t.position}</td>
          <td class="team-col">
            ${logo}
            <span class="team-name" title="${t.team}">${t.team_short || t.team}</span>
          </td>
          <td>${t.played_games ?? ""}</td>
          <td>${t.won ?? ""}</td>
          <td>${t.draw ?? ""}</td>
          <td>${t.lost ?? ""}</td>
          <td>${t.goals_for ?? ""}–${t.goals_against ?? ""}</td>
          <td class="gd ${gdClass}">${gdFormatted}</td>
          <td class="pts">${t.points ?? ""}</td>
        </tr>`;
    }).join("");

    this.content.innerHTML = `
      <div class="header">
        🏆 Allsvenskan ${season}
      </div>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th class="team-col">Lag</th>
            <th title="Spelade matcher">S</th>
            <th title="Vinster">V</th>
            <th title="Oavgjorda">O</th>
            <th title="Förluster">F</th>
            <th title="Mål">Mål</th>
            <th title="Målskillnad">MS</th>
            <th title="Poäng">P</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  }
}

customElements.define("allsvenskan-card", AllsvenskanCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "allsvenskan-card",
  name: "Allsvenskan Tabell",
  description: "Visar aktuell tabell för Allsvenskan med laglogotyper.",
  preview: false,
});
