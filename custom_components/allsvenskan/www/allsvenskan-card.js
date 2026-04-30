class AllsvenskanCard extends HTMLElement {
  setConfig(config) {
    this.config = config;
  }

  getCardSize() {
    return 10;
  }

  set hass(hass) {
    if (!this._initialized) {
      this._init();
    }
    const entity = (this.config && this.config.entity) || "sensor.allsvenskan_tabell";
    const stateObj = hass.states[entity];
    if (!stateObj) {
      this._content.innerHTML = '<p style="color:red;padding:12px">Entity ' + entity + ' not found.</p>';
      return;
    }
    const standings = stateObj.attributes.standings || [];
    const season = stateObj.attributes.season || "";
    this._render(standings, season);
  }

  _init() {
    this._initialized = true;
    const shadow = this.attachShadow({ mode: "open" });
    const style = document.createElement("style");
    style.textContent = [
      "ha-card{padding:0;overflow:hidden}",
      ".header{background:linear-gradient(135deg,#1a6b3a,#0d4a28);color:#fff;padding:14px 16px;font-size:1.1em;font-weight:700}",
      "table{width:100%;border-collapse:collapse;font-size:0.88em}",
      "thead tr{background:#f4f4f4;color:#555;font-size:0.78em;text-transform:uppercase}",
      "th{padding:6px 8px;text-align:center;white-space:nowrap}",
      "th.tc{text-align:left;padding-left:10px}",
      "tbody tr{border-bottom:1px solid #f0f0f0}",
      "tbody tr:hover{background:#f9f9f9}",
      "tbody tr.cl{border-left:3px solid #1565C0}",
      "tbody tr.eu{border-left:3px solid #F57F17}",
      "tbody tr.rp{border-left:3px solid #E65100}",
      "tbody tr.re{border-left:3px solid #B71C1C}",
      "td{padding:7px 8px;text-align:center;vertical-align:middle}",
      "td.tc{text-align:left;padding-left:10px;display:flex;align-items:center;gap:8px}",
      "td.tc img{width:22px;height:22px;object-fit:contain;flex-shrink:0}",
      "td.tc span{font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:130px}",
      "td.pos{font-weight:700;color:#333;width:28px}",
      "td.pts{font-weight:800;color:#1a6b3a}",
      "td.gd.p{color:#2e7d32}",
      "td.gd.n{color:#c62828}"
    ].join("");
    const card = document.createElement("ha-card");
    this._content = document.createElement("div");
    card.appendChild(this._content);
    shadow.appendChild(style);
    shadow.appendChild(card);
  }

  _render(standings, season) {
    var rows = standings.map(function(t) {
      var gd = t.goal_difference || 0;
      var gdStr = gd > 0 ? "+" + gd : "" + gd;
      var gdCls = gd > 0 ? "p" : gd < 0 ? "n" : "";
      var zone = (function(pos) {
        if (pos === 1) return "cl";
        if (pos <= 3) return "eu";
        if (pos === 14) return "rp";
        if (pos >= 15) return "re";
        return "";
      })(t.position);
      var logo = t.team_logo
        ? '<img src="' + t.team_logo + '" loading="lazy" onerror="this.style.display=\'none\'">'
        : '';
      return '<tr class="' + zone + '">'
        + '<td class="pos">' + (t.position || "") + '</td>'
        + '<td class="tc">' + logo + '<span title="' + (t.team || "") + '">' + (t.team_short || t.team || "") + '</span></td>'
        + '<td>' + (t.played_games != null ? t.played_games : "") + '</td>'
        + '<td>' + (t.won != null ? t.won : "") + '</td>'
        + '<td>' + (t.draw != null ? t.draw : "") + '</td>'
        + '<td>' + (t.lost != null ? t.lost : "") + '</td>'
        + '<td>' + (t.goals_for != null ? t.goals_for : "") + '-' + (t.goals_against != null ? t.goals_against : "") + '</td>'
        + '<td class="gd ' + gdCls + '">' + gdStr + '</td>'
        + '<td class="pts">' + (t.points != null ? t.points : "") + '</td>'
        + '</tr>';
    }).join("");

    this._content.innerHTML = '<div class="header">Allsvenskan ' + season + '</div>'
      + '<table><thead><tr>'
      + '<th>#</th><th class="tc">Lag</th><th>S</th><th>V</th><th>O</th><th>F</th><th>Mal</th><th>MS</th><th>P</th>'
      + '</tr></thead><tbody>' + rows + '</tbody></table>';
  }
}

if (!customElements.get("allsvenskan-card")) {
  customElements.define("allsvenskan-card", AllsvenskanCard);
  console.info("%c ALLSVENSKAN-CARD %c loaded", "color:white;background:#1a6b3a;font-weight:700;padding:2px 6px", "");
}

window.customCards = window.customCards || [];
if (!window.customCards.some(function(c) { return c.type === "allsvenskan-card"; })) {
  window.customCards.push({
    type: "allsvenskan-card",
    name: "Allsvenskan Tabell",
    description: "Allsvenskan standings table with team logos.",
    preview: false
  });
}