/* ── Column registry ────────────────────────────────────────────────
 * Each entry defines one toggleable column.
 * key    – used in the YAML "columns" list
 * header – table header text
 * thCls  – optional CSS class on <th>
 * cell   – function(teamRow) → HTML string for <td>
 */
var ALLSVENSKAN_COLUMNS = [
  {
    key: "position",
    header: "#",
    thCls: "",
    cell: function (t) {
      return '<td class="pos">' + (t.position || "") + "</td>";
    },
  },
  {
    key: "team",
    header: "Lag",
    thCls: "tc",
    cell: function (t) {
      var logo = t.team_logo
        ? '<img src="' + t.team_logo + "\" loading=\"lazy\" onerror=\"this.style.display='none'\">"
        : "";
      return (
        '<td class="tc">' +
        logo +
        '<span title="' + (t.team || "") + '">' +
        (t.team_short || t.team || "") +
        "</span></td>"
      );
    },
  },
  {
    key: "played",
    header: "S",
    thCls: "",
    cell: function (t) {
      return "<td>" + (t.played_games != null ? t.played_games : "") + "</td>";
    },
  },
  {
    key: "won",
    header: "V",
    thCls: "",
    cell: function (t) {
      return "<td>" + (t.won != null ? t.won : "") + "</td>";
    },
  },
  {
    key: "draw",
    header: "O",
    thCls: "",
    cell: function (t) {
      return "<td>" + (t.draw != null ? t.draw : "") + "</td>";
    },
  },
  {
    key: "lost",
    header: "F",
    thCls: "",
    cell: function (t) {
      return "<td>" + (t.lost != null ? t.lost : "") + "</td>";
    },
  },
  {
    key: "goals",
    header: "Mal",
    thCls: "",
    cell: function (t) {
      return (
        "<td>" +
        (t.goals_for != null ? t.goals_for : "") +
        "-" +
        (t.goals_against != null ? t.goals_against : "") +
        "</td>"
      );
    },
  },
  {
    key: "goal_difference",
    header: "MS",
    thCls: "",
    cell: function (t) {
      var gd = t.goal_difference || 0;
      var gdStr = gd > 0 ? "+" + gd : "" + gd;
      var gdCls = gd > 0 ? "p" : gd < 0 ? "n" : "";
      return '<td class="gd ' + gdCls + '">' + gdStr + "</td>";
    },
  },
  {
    key: "points",
    header: "P",
    thCls: "",
    cell: function (t) {
      return '<td class="pts">' + (t.points != null ? t.points : "") + "</td>";
    },
  },
];

var ALL_COLUMN_KEYS = ALLSVENSKAN_COLUMNS.map(function (c) {
  return c.key;
});

/* ── Helper: resolve active column objects from config ────────── */
function _resolveColumns(config) {
  var keys = config && Array.isArray(config.columns) && config.columns.length
    ? config.columns
    : ALL_COLUMN_KEYS;
  var out = [];
  for (var i = 0; i < keys.length; i++) {
    for (var j = 0; j < ALLSVENSKAN_COLUMNS.length; j++) {
      if (ALLSVENSKAN_COLUMNS[j].key === keys[i]) {
        out.push(ALLSVENSKAN_COLUMNS[j]);
        break;
      }
    }
  }
  return out.length ? out : ALLSVENSKAN_COLUMNS;
}

/* ── Main card ─────────────────────────────────────────────────── */
class AllsvenskanCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("allsvenskan-card-editor");
  }

  static getStubConfig() {
    return { entity: "sensor.allsvenskan_tabell" };
  }

  setConfig(config) {
    this.config = config;
    // Re-render if already initialised (config changed in editor)
    if (this._initialized && this._hass) {
      this.hass = this._hass;
    }
  }

  getCardSize() {
    return 10;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) {
      this._init();
    }
    var entity = (this.config && this.config.entity) || "sensor.allsvenskan_tabell";
    var stateObj = hass.states[entity];
    if (!stateObj) {
      this._content.innerHTML =
        '<p style="color:red;padding:12px">Entity ' + entity + " not found.</p>";
      return;
    }
    var standings = stateObj.attributes.standings || [];
    var maxRows = this.config && this.config.max_rows;
    var limited = maxRows ? standings.slice(0, maxRows) : standings;
    var season = stateObj.attributes.season || "";
    this._render(limited, season);
  }

  _init() {
    this._initialized = true;
    var shadow = this.attachShadow({ mode: "open" });
    var style = document.createElement("style");
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
      "tbody tr.fav{background:#FFF9C4}",
      "tbody tr.fav:hover{background:#FFF176}",
      "td{padding:7px 8px;text-align:center;vertical-align:middle}",
      "td.tc{text-align:left;padding-left:10px;display:flex;align-items:center;gap:8px}",
      "td.tc img{width:22px;height:22px;object-fit:contain;flex-shrink:0}",
      "td.tc span{font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:130px}",
      "td.pos{font-weight:700;color:#333;width:28px}",
      "td.pts{font-weight:800;color:#1a6b3a}",
      "td.gd.p{color:#2e7d32}",
      "td.gd.n{color:#c62828}",
    ].join("");
    var card = document.createElement("ha-card");
    this._content = document.createElement("div");
    card.appendChild(this._content);
    shadow.appendChild(style);
    shadow.appendChild(card);
  }

  _render(standings, season) {
    var cols = _resolveColumns(this.config);
    var fav = ((this.config && this.config.favorite_team) || "").toLowerCase();

    // Build header
    var ths = cols
      .map(function (c) {
        return "<th" + (c.thCls ? ' class="' + c.thCls + '"' : "") + ">" + c.header + "</th>";
      })
      .join("");

    // Build body
    var rows = standings
      .map(function (t) {
        var zone = (function (pos) {
          if (pos === 1) return "cl";
          if (pos <= 3) return "eu";
          if (pos === 14) return "rp";
          if (pos >= 15) return "re";
          return "";
        })(t.position);
        var isFav =
          fav &&
          ((t.team || "").toLowerCase().indexOf(fav) !== -1 ||
            (t.team_short || "").toLowerCase().indexOf(fav) !== -1 ||
            fav.indexOf((t.team || "").toLowerCase()) !== -1);
        var tds = cols
          .map(function (c) {
            return c.cell(t);
          })
          .join("");
        return '<tr class="' + zone + (isFav ? " fav" : "") + '">' + tds + "</tr>";
      })
      .join("");

    this._content.innerHTML =
      '<div class="header">Allsvenskan ' +
      season +
      "</div>" +
      "<table><thead><tr>" +
      ths +
      "</tr></thead><tbody>" +
      rows +
      "</tbody></table>";
  }
}

/* ── Visual card editor ────────────────────────────────────────── */
class AllsvenskanCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = Object.assign({}, config);
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
  }

  _render() {
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }
    var cfg = this._config || {};
    var active = Array.isArray(cfg.columns) && cfg.columns.length ? cfg.columns : ALL_COLUMN_KEYS;

    var html = '<style>'
      + ':host{display:block;padding:16px}'
      + '.row{display:flex;align-items:center;margin-bottom:12px;gap:8px}'
      + 'label{min-width:120px;font-weight:500}'
      + 'input[type=text]{flex:1;padding:6px 8px;border:1px solid #ccc;border-radius:4px}'
      + 'input[type=number]{width:80px;padding:6px 8px;border:1px solid #ccc;border-radius:4px}'
      + '.col-section{margin-top:12px}'
      + '.col-section h3{margin:0 0 8px;font-size:0.95em;color:#555}'
      + '.col-grid{display:flex;flex-wrap:wrap;gap:6px}'
      + '.col-chip{display:flex;align-items:center;gap:4px;padding:4px 10px;border:1px solid #ccc;border-radius:16px;cursor:pointer;user-select:none;font-size:0.85em;transition:all .15s}'
      + '.col-chip.active{background:#1a6b3a;color:#fff;border-color:#1a6b3a}'
      + '.col-chip:hover{opacity:0.85}'
      + '</style>';

    html += '<div class="row"><label>Entity</label>'
      + '<input type="text" id="entity" value="' + (cfg.entity || "sensor.allsvenskan_tabell") + '"></div>';
    html += '<div class="row"><label>Favorite team</label>'
      + '<input type="text" id="fav" value="' + (cfg.favorite_team || "") + '"></div>';
    html += '<div class="row"><label>Max rows</label>'
      + '<input type="number" id="maxrows" min="0" value="' + (cfg.max_rows || "") + '" placeholder="all"></div>';

    html += '<div class="col-section"><h3>Columns (click to toggle, default = all)</h3><div class="col-grid">';
    for (var i = 0; i < ALLSVENSKAN_COLUMNS.length; i++) {
      var c = ALLSVENSKAN_COLUMNS[i];
      var isActive = active.indexOf(c.key) !== -1;
      html += '<div class="col-chip' + (isActive ? ' active' : '') + '" data-key="' + c.key + '">'
        + c.header + ' <small>(' + c.key + ')</small></div>';
    }
    html += '</div></div>';

    this.shadowRoot.innerHTML = html;

    // Bind events
    var self = this;
    this.shadowRoot.getElementById("entity").addEventListener("change", function (e) {
      self._update("entity", e.target.value);
    });
    this.shadowRoot.getElementById("fav").addEventListener("change", function (e) {
      self._update("favorite_team", e.target.value);
    });
    this.shadowRoot.getElementById("maxrows").addEventListener("change", function (e) {
      var v = parseInt(e.target.value, 10);
      self._update("max_rows", v > 0 ? v : undefined);
    });
    var chips = this.shadowRoot.querySelectorAll(".col-chip");
    for (var j = 0; j < chips.length; j++) {
      chips[j].addEventListener("click", function () {
        self._toggleColumn(this.getAttribute("data-key"));
      });
    }
  }

  _toggleColumn(key) {
    var cfg = this._config || {};
    var cols = Array.isArray(cfg.columns) && cfg.columns.length
      ? cfg.columns.slice()
      : ALL_COLUMN_KEYS.slice();
    var idx = cols.indexOf(key);
    if (idx !== -1) {
      // Don't allow removing ALL columns
      if (cols.length <= 1) return;
      cols.splice(idx, 1);
    } else {
      // Insert at the canonical position
      var insertIdx = 0;
      for (var i = 0; i < ALL_COLUMN_KEYS.length; i++) {
        if (ALL_COLUMN_KEYS[i] === key) break;
        if (cols.indexOf(ALL_COLUMN_KEYS[i]) !== -1) insertIdx++;
      }
      cols.splice(insertIdx, 0, key);
    }
    // If all columns are selected, store undefined (= default all)
    if (cols.length === ALL_COLUMN_KEYS.length) {
      this._update("columns", undefined);
    } else {
      this._update("columns", cols);
    }
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
if (!customElements.get("allsvenskan-card-editor")) {
  customElements.define("allsvenskan-card-editor", AllsvenskanCardEditor);
}
if (!customElements.get("allsvenskan-card")) {
  customElements.define("allsvenskan-card", AllsvenskanCard);
  console.info(
    "%c ALLSVENSKAN-CARD %c loaded",
    "color:white;background:#1a6b3a;font-weight:700;padding:2px 6px",
    ""
  );
}

window.customCards = window.customCards || [];
if (!window.customCards.some(function (c) { return c.type === "allsvenskan-card"; })) {
  window.customCards.push({
    type: "allsvenskan-card",
    name: "Allsvenskan Tabell",
    description: "Allsvenskan standings table with team logos and configurable columns.",
    preview: false,
  });
}