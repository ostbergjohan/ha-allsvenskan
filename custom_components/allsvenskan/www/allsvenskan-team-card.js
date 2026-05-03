/* ═══════════════════════════════════════════════════════════════════
 *  Allsvenskan Team Card
 *  A hero-style card for a single team sensor.
 *
 *  Config options:
 *    entity       – sensor.allsvenskan_<team>  (required)
 *    rows         – 1 | 2 | 3 | 4              (default: 4)
 *
 *  rows levels:
 *    1 = hero (logo + name + position)
 *    2 = + points bar
 *    3 = + W / D / L grid
 *    4 = + goals section + form bar
 * ═══════════════════════════════════════════════════════════════════ */

/* ── Styles ────────────────────────────────────────────────────── */
var TEAM_CARD_STYLES = [
  ":host{display:block}",
  "ha-card{padding:0;overflow:hidden;border-radius:16px;background:var(--ha-card-background,var(--card-background-color,#2a2a2a));color:var(--primary-text-color,#fff)}",

  /* Hero */
  ".hero{background:linear-gradient(135deg,#1a6b3a 0%,#0d4a28 100%);padding:28px 24px 22px;display:flex;align-items:center;gap:18px;position:relative;overflow:hidden}",
  ".hero::after{content:'';position:absolute;right:-30px;top:-30px;width:140px;height:140px;background:rgba(255,255,255,0.04);border-radius:50%}",
  ".hero img{width:72px;height:72px;object-fit:contain;filter:drop-shadow(0 2px 8px rgba(0,0,0,0.3));flex-shrink:0}",
  ".hero-text{flex:1;min-width:0}",
  ".hero-text .team-name{font-size:1.3em;font-weight:700;line-height:1.2;color:#fff;text-shadow:0 1px 4px rgba(0,0,0,0.3)}",
  ".hero-text .subtitle{font-size:0.82em;color:rgba(255,255,255,0.7);margin-top:4px}",
  ".position-badge{position:absolute;top:14px;right:16px;background:rgba(255,255,255,0.15);backdrop-filter:blur(4px);border-radius:10px;padding:4px 12px;font-size:0.75em;font-weight:600;letter-spacing:0.5px;color:rgba(255,255,255,0.9)}",
  ".position-badge span{font-size:1.4em;font-weight:800;color:#fff}",

  /* Points bar */
  ".points-bar{display:flex;align-items:center;justify-content:center;gap:6px;padding:12px;background:linear-gradient(90deg,#145a30,#1a6b3a);font-size:0.85em;color:rgba(255,255,255,0.75)}",
  ".points-bar .pts{font-size:1.6em;font-weight:800;color:#7dff7d}",

  /* Stats grid */
  ".stats{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:#333;padding:1px}",
  ".stat{background:var(--ha-card-background,var(--card-background-color,#2a2a2a));text-align:center;padding:14px 8px}",
  ".stat .val{font-size:1.4em;font-weight:700}",
  ".stat .lbl{font-size:0.72em;color:var(--secondary-text-color,#999);text-transform:uppercase;letter-spacing:0.5px;margin-top:2px}",
  ".stat.won .val{color:#66bb6a}",
  ".stat.draw .val{color:#ffa726}",
  ".stat.lost .val{color:#ef5350}",

  /* Goals section */
  ".goals{display:flex;align-items:center;justify-content:center;gap:16px;padding:16px;border-top:1px solid rgba(255,255,255,0.08)}",
  ".goals .g-block{text-align:center}",
  ".goals .g-block .val{font-size:1.3em;font-weight:700}",
  ".goals .g-block .lbl{font-size:0.7em;color:var(--secondary-text-color,#999);text-transform:uppercase;margin-top:2px}",
  ".goals .divider{font-size:1.2em;color:var(--secondary-text-color,#555)}",
  ".goals .gd{background:rgba(102,187,106,0.15);border-radius:8px;padding:6px 14px;text-align:center}",
  ".goals .gd .val.pos{color:#66bb6a}",
  ".goals .gd .val.neg{color:#ef5350}",
  ".goals .gd .val.zero{color:var(--secondary-text-color,#999)}",

  /* Form bar */
  ".form-bar{display:flex;height:5px}",
  ".form-bar .w{background:#66bb6a}",
  ".form-bar .d{background:#ffa726}",
  ".form-bar .l{background:#ef5350}",
].join("");


/* ── Position suffix helper ────────────────────────────────────── */
function _posSuffix(pos) {
  if (pos === 1 || pos === 2) return ":a";
  return ":e";
}


/* ── Main card ─────────────────────────────────────────────────── */
class AllsvenskanTeamCard extends HTMLElement {

  static getConfigElement() {
    return document.createElement("allsvenskan-team-card-editor");
  }

  static getStubConfig() {
    return { entity: "", rows: 4 };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Please define an entity (e.g. sensor.allsvenskan_hammarby_if)");
    }
    this.config = config;
    if (this._initialized && this._hass) {
      this.hass = this._hass;
    }
  }

  getCardSize() {
    var r = (this.config && this.config.rows) || 4;
    if (r <= 1) return 3;
    if (r === 2) return 4;
    if (r === 3) return 6;
    return 8;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) this._init();
    var entity = this.config.entity;
    var stateObj = hass.states[entity];
    if (!stateObj) {
      this._content.innerHTML =
        '<p style="color:red;padding:12px">Entity <b>' + entity + "</b> not found.</p>";
      return;
    }
    this._renderCard(stateObj);
  }

  _init() {
    this._initialized = true;
    var shadow = this.attachShadow({ mode: "open" });
    var style = document.createElement("style");
    style.textContent = TEAM_CARD_STYLES;
    var card = document.createElement("ha-card");
    this._content = document.createElement("div");
    card.appendChild(this._content);
    shadow.appendChild(style);
    shadow.appendChild(card);
  }

  _renderCard(stateObj) {
    var a = stateObj.attributes;
    var rows = Math.min(4, Math.max(1, parseInt(this.config.rows, 10) || 4));

    var teamName = a.team || stateObj.attributes.friendly_name || "";
    var crest = a.crest || "";
    var position = stateObj.state;
    var points = a.points;
    var played = a.played;
    var won = a.won;
    var draw = a.draw;
    var lost = a.lost;
    var goalsFor = a.goals_for;
    var goalsAgainst = a.goals_against;
    var goalDiff = a.goal_difference;

    var html = "";

    /* ── Row 1: Hero ──────────────────────────── */
    var imgTag = crest
      ? '<img src="' + crest + "\" alt=\"\" loading=\"lazy\" onerror=\"this.style.display='none'\">"
      : "";
    var posNum = parseInt(position, 10);
    var posBadge = !isNaN(posNum)
      ? '<div class="position-badge"><span>' + posNum + "</span>" + _posSuffix(posNum) + "</div>"
      : "";
    html +=
      '<div class="hero">' +
        imgTag +
        '<div class="hero-text">' +
          '<div class="team-name">' + teamName + "</div>" +
          '<div class="subtitle">Allsvenskan</div>' +
        "</div>" +
        posBadge +
      "</div>";

    /* ── Row 2: Points bar ────────────────────── */
    if (rows >= 2) {
      var ptsStr = points != null ? points : "–";
      var playedStr = played != null ? played : "–";
      html +=
        '<div class="points-bar">' +
          '<span class="pts">' + ptsStr + "</span> poäng" +
          " &nbsp;·&nbsp; " + playedStr + " spelade" +
        "</div>";
    }

    /* ── Row 3: W / D / L ─────────────────────── */
    if (rows >= 3) {
      html +=
        '<div class="stats">' +
          '<div class="stat won"><div class="val">' + (won != null ? won : "–") + '</div><div class="lbl">Vinster</div></div>' +
          '<div class="stat draw"><div class="val">' + (draw != null ? draw : "–") + '</div><div class="lbl">Oavgjort</div></div>' +
          '<div class="stat lost"><div class="val">' + (lost != null ? lost : "–") + '</div><div class="lbl">Förluster</div></div>' +
        "</div>";
    }

    /* ── Row 4: Goals + form bar ──────────────── */
    if (rows >= 4) {
      var gd = goalDiff != null ? parseInt(goalDiff, 10) : null;
      var gdStr = gd != null ? (gd > 0 ? "+" + gd : "" + gd) : "–";
      var gdCls = gd != null ? (gd > 0 ? "pos" : gd < 0 ? "neg" : "zero") : "zero";

      html +=
        '<div class="goals">' +
          '<div class="g-block"><div class="val">' + (goalsFor != null ? goalsFor : "–") + '</div><div class="lbl">Gjorda</div></div>' +
          '<div class="divider">–</div>' +
          '<div class="g-block"><div class="val">' + (goalsAgainst != null ? goalsAgainst : "–") + '</div><div class="lbl">Insläppta</div></div>' +
          '<div class="gd"><div class="val ' + gdCls + '">' + gdStr + '</div><div class="lbl">Målskillnad</div></div>' +
        "</div>";

      // Form bar – visual ratio of W/D/L
      var w = parseInt(won, 10) || 0;
      var d = parseInt(draw, 10) || 0;
      var l = parseInt(lost, 10) || 0;
      if (w + d + l > 0) {
        html +=
          '<div class="form-bar">' +
            '<div class="w" style="flex:' + w + '"></div>' +
            '<div class="d" style="flex:' + d + '"></div>' +
            '<div class="l" style="flex:' + l + '"></div>' +
          "</div>";
      }
    }

    this._content.innerHTML = html;
  }
}


/* ── Visual card editor ────────────────────────────────────────── */
class AllsvenskanTeamCardEditor extends HTMLElement {

  setConfig(config) {
    this._config = Object.assign({}, config);
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    // Re-render to populate entity dropdown
    if (this._rendered) this._render();
  }

  _render() {
    this._rendered = true;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });

    var cfg = this._config || {};
    var currentEntity = cfg.entity || "";
    var currentRows = cfg.rows || 4;

    // Collect team sensor entities
    var teamEntities = [];
    if (this._hass) {
      var states = this._hass.states;
      for (var sid in states) {
        if (sid.indexOf("sensor.allsvenskan_") === 0 && sid !== "sensor.allsvenskan_tabell") {
          teamEntities.push(sid);
        }
      }
      teamEntities.sort();
    }

    var html =
      "<style>" +
        ":host{display:block;padding:16px}" +
        ".row{display:flex;align-items:center;margin-bottom:12px;gap:8px}" +
        "label{min-width:90px;font-weight:500}" +
        "select{flex:1;padding:6px 8px;border:1px solid #ccc;border-radius:4px;font-size:0.9em}" +
        ".desc{font-size:0.78em;color:#888;margin:-4px 0 8px 98px}" +
      "</style>";

    /* Entity dropdown */
    html += '<div class="row"><label>Lag</label><select id="entity">';
    if (!currentEntity) html += '<option value="">-- välj lag --</option>';
    for (var i = 0; i < teamEntities.length; i++) {
      var eid = teamEntities[i];
      var friendly = this._hass.states[eid].attributes.friendly_name || eid;
      var sel = eid === currentEntity ? " selected" : "";
      html += '<option value="' + eid + '"' + sel + ">" + friendly + "</option>";
    }
    html += "</select></div>";

    /* Rows selector */
    html += '<div class="row"><label>Rader</label><select id="rows">';
    var rowLabels = [
      "1 – Logo + position",
      "2 – + poäng",
      "3 – + V/O/F",
      "4 – + mål & målskillnad",
    ];
    for (var r = 1; r <= 4; r++) {
      var selR = r === currentRows ? " selected" : "";
      html += '<option value="' + r + '"' + selR + ">" + rowLabels[r - 1] + "</option>";
    }
    html += "</select></div>";
    html += '<div class="desc">Bestämmer hur mycket statistik som visas på kortet.</div>';

    this.shadowRoot.innerHTML = html;

    // Bind events
    var self = this;
    this.shadowRoot.getElementById("entity").addEventListener("change", function (e) {
      self._update("entity", e.target.value);
    });
    this.shadowRoot.getElementById("rows").addEventListener("change", function (e) {
      self._update("rows", parseInt(e.target.value, 10));
    });
  }

  _update(key, value) {
    if (value === undefined || value === "") {
      delete this._config[key];
    } else {
      this._config[key] = value;
    }
    var ev = new CustomEvent("config-changed", { detail: { config: this._config } });
    this.dispatchEvent(ev);
    this._render();
  }
}


/* ── Register elements ─────────────────────────────────────────── */
if (!customElements.get("allsvenskan-team-card-editor")) {
  customElements.define("allsvenskan-team-card-editor", AllsvenskanTeamCardEditor);
}
if (!customElements.get("allsvenskan-team-card")) {
  customElements.define("allsvenskan-team-card", AllsvenskanTeamCard);
  console.info(
    "%c ALLSVENSKAN-TEAM-CARD %c loaded",
    "color:white;background:#1a6b3a;font-weight:700;padding:2px 6px",
    ""
  );
}

window.customCards = window.customCards || [];
if (!window.customCards.some(function (c) { return c.type === "allsvenskan-team-card"; })) {
  window.customCards.push({
    type: "allsvenskan-team-card",
    name: "Allsvenskan Lag",
    description: "Hero-style card for a single Allsvenskan team with configurable detail rows.",
    preview: false,
  });
}
