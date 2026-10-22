// Zähler-Ablesung sidebar panel: overview of all meters, meter editor and settings.
// Plain web component without build step; uses only the hass object and the
// WebSocket commands of the integration. Field names and help texts come from
// the translation files (labels.js), types and ranges from the selectors of the
// dialogs (sent by the integration).

import { LABELS } from "./labels.js";

const DOMAIN = "zaehler_ablesung";

const UI = {
  de: {
    title: "Zähler-Ablesung",
    tabs: { overview: "Übersicht", meters: "Zähler", settings: "Einstellungen" },
    cards: {
      general: ["Allgemein", "KI-Aufgabe und Benachrichtigungen für alle Zähler."],
      meters: ["Zähler", "Jeder Zähler hat eine eigene Kamera. Die Art setzt passende Startwerte."],
    },
    save: "Speichern",
    saved: "Gespeichert",
    cancel: "Abbrechen",
    delete: "Löschen",
    add: "Zähler hinzufügen",
    edit: "Bearbeiten",
    confirmDelete: "Zähler wirklich löschen? Seine Entitäten, gespeicherten Werte und Bilder werden entfernt.",
    notFound: "nicht gefunden",
    none: "–",
    newMeter: "Neuer Zähler",
    readNow: "Jetzt ablesen",
    testPicture: "Testbild",
    running: { reading: "Liest ab …", picture: "Bild wird aufgenommen …" },
    automatic: "Automatik",
    rate: "Mittlerer Verbrauch",
    ratePower: "Mittlere Leistung",
    rateFlow: "Mittlerer Durchfluss",
    validSince: "Gültig seit",
    lastCheck: "Letzte Ablesung",
    nextCheck: "Nächste Ablesung",
    readings: "Lesungen",
    noImage: "Noch kein Bild",
    noMeters: "Noch kein Zähler angelegt.",
    setReading: "Zählerstand von Hand setzen",
    setReadingHelp: "Nach einer Fehllesung: der richtige Wert vom Display. Die nächsten Ablesungen werden gegen diesen Wert geprüft.",
    set: "Setzen",
    preview: "Bild",
    previewLive: "Aktuelles Kamerabild (ohne Licht)",
    previewLast: "Letztes Bild, so wie es die KI bekommt",
    readRejected: "Gelesen, aber verworfen",
    rejected: "Verworfene Bilder",
    noRejected: "Keine verworfenen Bilder.",
    takeValue: "Übernehmen",
    confirmTake: "Den gelesenen Wert {value} als Zählerstand übernehmen? Spätere Ablesungen werden gegen diesen Wert geprüft.",
    confirmDiscard: "Die Änderungen an diesem Zähler sind nicht gespeichert. Trotzdem verlassen?",
    previewHint: "Testbild nimmt ein Bild mit den gespeicherten Einstellungen auf. Erst speichern, dann ausprobieren.",
    prompt: "Anweisung an die KI",
    promptOwn: "eigene",
    promptStandard: "Wird automatisch aus Zählerart, Einheit, Nachkommastellen und Hinweisen erzeugt. Mit „Bearbeiten“ lässt sich die ganze Anweisung frei ändern.",
    promptCustom: "Eigene Anweisung: Die KI bekommt genau diesen Text. Einheit, Nachkommastellen und Hinweise werden nicht mehr eingesetzt. Die KI soll weiterhin nur die Zahl oder „unlesbar“ antworten.",
    promptEdit: "Bearbeiten",
    promptReset: "Standard wiederherstellen",
    confirmPromptReset: "Die eigene Anweisung verwerfen und wieder die automatisch erzeugte verwenden?",
    cropHelp: "Erst das Bild gerade drehen, dann einen Rahmen um die Anzeige ziehen (Maus oder Finger); den Rahmen verschieben oder an den Ecken anpassen. Gespeichert wird mit „Speichern“, das nächste Bild ist dann gedreht und zugeschnitten.",
    rotate: "Drehen",
    cropNoImage: "Noch kein Bild. Erst speichern und ein Testbild aufnehmen, oder das Livebild ansehen.",
    live: "Livebild",
    liveStop: "Livebild beenden",
    liveLight: "Licht an",
    liveHint: "Livebild der Kamera, gedreht wie eingestellt. Gut zum Ausrichten der Kamera; die KI bekommt später ein Einzelbild.",
    cropReset: "Ganzes Bild",
    columns: { name: "Name", type: "Art", reading: "Zählerstand", status: "Status" },
    warnings: "Hinweise",
    missing: "Eingestellte Entitäten fehlen",
    noAiTask: "Keine KI-Aufgabe eingestellt",
    errors: {
      required: "Pflichtfeld",
      invalid_value: "Ungültiger Wert",
      unknown_option: "Unbekannte Einstellung",
    },
    loadError: "Konfiguration konnte nicht geladen werden",
  },
  en: {
    title: "Zähler-Ablesung",
    tabs: { overview: "Overview", meters: "Meters", settings: "Settings" },
    cards: {
      general: ["General", "AI task and notifications for all meters."],
      meters: ["Meters", "Every meter has its own camera. The type sets suitable defaults."],
    },
    save: "Save",
    saved: "Saved",
    cancel: "Cancel",
    delete: "Delete",
    add: "Add meter",
    edit: "Edit",
    confirmDelete: "Really delete this meter? Its entities, stored values and pictures are removed.",
    notFound: "not found",
    none: "–",
    newMeter: "New meter",
    readNow: "Read now",
    testPicture: "Test picture",
    running: { reading: "Reading …", picture: "Taking a picture …" },
    automatic: "Automatic",
    rate: "Mean consumption",
    ratePower: "Mean power",
    rateFlow: "Mean flow",
    validSince: "Valid since",
    lastCheck: "Last reading",
    nextCheck: "Next reading",
    readings: "Readings",
    noImage: "No picture yet",
    noMeters: "No meter added yet.",
    setReading: "Set the meter reading by hand",
    setReadingHelp: "After a wrong reading: the correct value from the display. The next readings are checked against this value.",
    set: "Set",
    preview: "Picture",
    previewLive: "Current camera picture (without light)",
    previewLast: "Last picture, as the AI gets it",
    readRejected: "Read, but rejected",
    rejected: "Rejected pictures",
    noRejected: "No rejected pictures.",
    takeValue: "Take",
    confirmTake: "Take the read value {value} as the meter reading? Later readings are checked against this value.",
    confirmDiscard: "The changes to this meter are not saved. Leave anyway?",
    previewHint: "Test picture takes a picture with the saved settings. Save first, then try it.",
    prompt: "Instructions for the AI",
    promptOwn: "own",
    promptStandard: "Generated from meter type, unit, decimals and hints. “Edit” lets you change the whole instructions freely.",
    promptCustom: "Own instructions: the AI gets exactly this text. Unit, decimals and hints are no longer inserted. The AI should still answer only with the number or “unreadable”.",
    promptEdit: "Edit",
    promptReset: "Restore standard",
    confirmPromptReset: "Discard the own instructions and use the generated ones again?",
    cropHelp: "First turn the picture straight, then draw a frame around the display (mouse or finger); move the frame or adjust it at the corners. Saved with “Save”, the next picture is then turned and cropped.",
    rotate: "Rotate",
    cropNoImage: "No picture yet. Save first and take a test picture, or watch the live picture.",
    live: "Live picture",
    liveStop: "Stop live picture",
    liveLight: "Light on",
    liveHint: "Live picture of the camera, turned as set. Good for aligning the camera; the AI later gets a single picture.",
    cropReset: "Whole picture",
    columns: { name: "Name", type: "Type", reading: "Meter reading", status: "Status" },
    warnings: "Notes",
    missing: "Configured entities are missing",
    noAiTask: "No AI task configured",
    errors: {
      required: "Required",
      invalid_value: "Invalid value",
      unknown_option: "Unknown setting",
    },
    loadError: "Could not load the configuration",
  },
};

const TABS = [
  ["overview", "mdi:view-dashboard-outline"],
  ["meters", "mdi:counter"],
  ["settings", "mdi:cog-outline"],
];

const TYPE_ICON = {
  heat: "mdi:radiator",
  water: "mdi:water",
  gas: "mdi:fire",
  electricity: "mdi:flash",
  other: "mdi:counter",
};

const STATUS_PILL = {
  ok: "ok",
  corrected: "ok",
  manual: "muted",
  unreadable: "warn",
  smaller: "warn",
  too_large: "warn",
  error: "bad",
};

// fields that follow the meter type while a new meter is edited
const TYPE_FIELDS = ["unit", "decimals", "max_rate", "max_correction", "interval", "hints"];
// sections shown collapsed in the editor
const COLLAPSED = new Set(["checks_section", "notify_section"]);

const esc = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const clone = (value) => JSON.parse(JSON.stringify(value ?? null));
// draw the picture turned clockwise like the integration does it (grown so nothing is cut off);
// a smaller picture is enough, the crop is in percent
const drawTurned = (canvas, img, deg, maxSize = 1600) => {
  const scale = Math.min(1, maxSize / Math.max(img.naturalWidth, img.naturalHeight));
  const w = img.naturalWidth * scale;
  const h = img.naturalHeight * scale;
  const rad = (deg * Math.PI) / 180;
  const cos = Math.abs(Math.cos(rad));
  const sin = Math.abs(Math.sin(rad));
  const width = Math.round(w * cos + h * sin);
  const height = Math.round(w * sin + h * cos);
  if (canvas.width !== width) canvas.width = width;
  if (canvas.height !== height) canvas.height = height;
  const ctx = canvas.getContext("2d");
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, width, height);
  ctx.translate(width / 2, height / 2);
  ctx.rotate(rad);
  ctx.drawImage(img, -w / 2, -h / 2, w, h);
};
const domainsOf = (spec) => {
  const d = spec?.domain;
  return !d ? [] : Array.isArray(d) ? d : [d];
};

class ZaehlerAblesungPanel extends HTMLElement {
  constructor() {
    super();
    this._tab = "overview";
    this._drafts = {};
    this._edit = null;
    this._cfg = null;
    this._error = null;
    this._sig = "";
    this._count = null;
    this.attachShadow({ mode: "open" });
    this.shadowRoot.addEventListener("click", (ev) => this._onClick(ev));
    this.shadowRoot.addEventListener("input", (ev) => this._onInput(ev));
    this.shadowRoot.addEventListener("change", (ev) => this._onInput(ev, true));
    for (const type of ["pointerdown", "pointermove", "pointerup", "pointercancel"]) {
      this.shadowRoot.addEventListener(type, (ev) => this._cropPointer(ev));
    }
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) {
      this._count = this._entityCount();
      this._load();
      return;
    }
    // new or removed entities (e.g. after adding a meter): load the entity ids again
    const count = this._entityCount();
    if (count !== this._count) {
      this._count = count;
      if (this._cfg) this._load(true);
    }
    this._live();
  }

  get hass() {
    return this._hass;
  }

  set narrow(value) {
    this._narrow = value;
    const btn = this.shadowRoot.querySelector(".menu");
    if (btn) btn.style.display = value ? "" : "none";
  }

  set panel(value) {
    this._panel = value;
  }

  // ------------------------------------------------------------------ texts

  get lang() {
    const language = this._hass?.locale?.language || this._hass?.language || "en";
    return language.startsWith("de") ? "de" : "en";
  }

  get ui() {
    return UI[this.lang];
  }

  get labels() {
    return LABELS[this.lang] || LABELS.en;
  }

  label(key) {
    return this.labels.fields[key] || [key, ""];
  }

  _errorText(message) {
    const [code, field] = String(message || "").split(":");
    const texts = { ...this.labels.errors, ...this.ui.errors };
    const text = texts[code] || message;
    return field ? `${this.label(field)[0]}: ${text}` : text;
  }

  // ------------------------------------------------------------------ data

  async _load(quiet = false) {
    try {
      this._cfg = await this._hass.callWS({ type: `${DOMAIN}/config` });
      this._error = null;
    } catch (err) {
      this._error = err.message || String(err);
    }
    if (quiet && this._edit) return;
    if (quiet && this.shadowRoot.querySelector(".content")) {
      this._rerenderContent();
      this._sig = this._signature();
      return;
    }
    this._render();
  }

  _entityCount() {
    return Object.values(this._hass?.entities || {}).filter((e) => e.platform === DOMAIN).length;
  }

  _ws(msg) {
    return this._hass.callWS(msg);
  }

  _state(entityId) {
    return entityId ? this._hass.states[entityId] : undefined;
  }

  _name(entityId) {
    const st = this._state(entityId);
    return st?.attributes?.friendly_name || entityId;
  }

  _ok(st) {
    return st && !["unavailable", "unknown"].includes(st.state);
  }

  _time(value) {
    const date = value ? new Date(value) : null;
    if (!date || Number.isNaN(date.getTime())) return this.ui.none;
    return date.toLocaleString(this._hass.locale?.language || this._hass.language, { dateStyle: "short", timeStyle: "short" });
  }

  _num(value, digits = 1, fixed = false) {
    const n = Number(value);
    if (value === null || value === undefined || value === "" || Number.isNaN(n)) return this.ui.none;
    const opts = fixed ? { minimumFractionDigits: digits, maximumFractionDigits: digits } : { maximumFractionDigits: digits };
    return n.toLocaleString(this._hass.locale?.language || this._hass.language, opts);
  }

  _typeName(type) {
    return this.labels.types[type] || type;
  }

  // ------------------------------------------------------------------ rendering

  _render() {
    const ui = this.ui;
    this.shadowRoot.innerHTML = `
      <style>${STYLE}</style>
      <div class="toolbar">
        <button class="menu icon-btn" data-action="menu" style="${this._narrow ? "" : "display:none"}"><ha-icon icon="mdi:menu"></ha-icon></button>
        <div class="title"><ha-icon icon="mdi:counter"></ha-icon>${esc(ui.title)}</div>
      </div>
      <div class="tabs">
        ${TABS.map(
          ([id, icon]) =>
            `<button class="tab ${this._tab === id ? "active" : ""}" data-tab="${id}"><ha-icon icon="${icon}"></ha-icon><span>${esc(ui.tabs[id])}</span></button>`,
        ).join("")}
      </div>
      <div class="content">${this._content()}</div>
      <div class="datalists">${this._datalists()}</div>
      <div class="toast" hidden></div>
      <button class="zoom" data-action="zoom-close" hidden><img alt=""></button>`;
    this._sig = this._signature();
  }

  _content() {
    if (this._error) return `<div class="card error">${esc(this.ui.loadError)}: ${esc(this._error)}</div>`;
    if (!this._cfg) return `<div class="card">…</div>`;
    if (this._edit) return this._editor();
    if (this._tab === "overview") return this._overview();
    if (this._tab === "meters") return this._metersTab();
    return this._settingsTab();
  }

  _allSpecs() {
    const specs = { ...(this._cfg?.option_specs || {}) };
    for (const sec of this._cfg?.meter_sections || []) Object.assign(specs, sec.fields);
    return specs;
  }

  _datalists() {
    if (!this._hass || !this._cfg) return "";
    const option = (id) => `<option value="${esc(id)}">${esc(this._name(id))}</option>`;
    const all = Object.keys(this._hass.states).sort();
    let html = `<datalist id="dl-all">${all.map(option).join("")}</datalist>`;
    const sets = new Set();
    for (const [key, spec] of Object.entries(this._allSpecs())) {
      const domains = domainsOf(spec);
      if (spec.selector === "entity" && domains.length) sets.add(domains.join(","));
      if (spec.selector === "select" && spec.custom_value) {
        html += `<datalist id="dl-opt-${esc(key)}">${(spec.options || []).map((o) => `<option value="${esc(typeof o === "object" ? o.value : o)}"></option>`).join("")}</datalist>`;
      }
    }
    for (const set of sets) {
      const domains = set.split(",");
      const ids = all.filter((id) => domains.includes(id.split(".")[0]));
      html += `<datalist id="dl-${esc(set.replace(/,/g, "-"))}">${ids.map(option).join("")}</datalist>`;
    }
    return html;
  }

  _listId(spec) {
    const domains = domainsOf(spec);
    return domains.length ? `dl-${domains.join("-")}` : "dl-all";
  }

  // ------------------------------------------------------------------ live updates

  _signature() {
    if (!this._hass || !this._cfg) return "";
    const ids = this._cfg.meters.flatMap((m) => [...Object.values(m.entities || {}), m.data.camera]);
    return ids
      .map((id) => {
        const st = this._state(id);
        if (!st) return `${id}=-`;
        const a = st.attributes;
        return `${id}=${st.state}|${a.running ?? ""}|${a.entity_picture ?? ""}|${(a.readings || []).join(",")}`;
      })
      .join(";");
  }

  _live() {
    const sig = this._signature();
    if (sig === this._sig) return;
    this._sig = sig;
    if (this._edit) {
      this._updatePreview();
      return;
    }
    if (["overview", "meters"].includes(this._tab)) this._rerenderContent();
  }

  // ------------------------------------------------------------------ overview

  _status(meter) {
    const st = this._state(meter.entities.status);
    const running = st?.attributes?.running;
    if (running) return [this.ui.running[running] || running, "run"];
    if (!this._ok(st)) return ["", ""];
    return [this.labels.status[st.state] || st.state, STATUS_PILL[st.state] || "muted"];
  }

  _reading(meter) {
    const st = this._state(meter.entities.reading);
    if (!this._ok(st)) return this.ui.none;
    const unit = st.attributes.unit_of_measurement || meter.data.unit || "";
    return `${this._num(st.state, meter.data.decimals, true)} ${unit}`.trim();
  }

  _rateLabel(meter) {
    if (meter.rate_unit === "kW") return this.ui.ratePower;
    if (meter.rate_unit === "L/h") return this.ui.rateFlow;
    return this.ui.rate;
  }

  _image(entityId, cls = "", hasImage = true) {
    const st = this._state(entityId);
    const pic = hasImage ? st?.attributes?.entity_picture : null;
    if (!pic) return `<div class="img-empty ${cls}"><ha-icon icon="mdi:image-off-outline"></ha-icon><span>${esc(this.ui.noImage)}</span></div>`;
    return `<img class="${cls}" src="${esc(pic)}" alt="" data-action="more-info" data-entity="${esc(entityId)}">`;
  }

  _meterCard(meter) {
    const ui = this.ui;
    const e = meter.entities;
    const [statusText, statusCls] = this._status(meter);
    const reading = this._state(e.reading);
    const rate = this._state(e.rate);
    const status = this._state(e.status);
    const last = this._state(e.last_check);
    const next = this._state(e.next_check);
    const auto = this._state(e.automatic);
    const autoOn = auto?.state === "on";
    const running = !!status?.attributes?.running;
    const readings = status?.attributes?.readings || [];
    const rateText = this._ok(rate) ? `${this._num(rate.state, 2)} ${rate.attributes.unit_of_measurement || ""}`.trim() : ui.none;
    return `<div class="card meter">
      <div class="meter-head">
        <h2><ha-icon icon="${TYPE_ICON[meter.data.meter_type] || "mdi:counter"}"></ha-icon>${esc(meter.title)}</h2>
        ${statusText ? `<span class="pill ${statusCls}">${esc(statusText)}</span>` : ""}
      </div>
      <div class="meter-body">
        <div class="meter-img">${this._image(e.last_image, "", !!status?.attributes?.image_time)}</div>
        <div class="meter-info">
          <button class="big link" data-action="more-info" data-entity="${esc(e.reading || "")}">${esc(this._reading(meter))}</button>
          <div class="rows">
            <div class="row"><ha-icon icon="${meter.rate_unit === "L/h" ? "mdi:water-pump" : "mdi:speedometer"}"></ha-icon><span class="grow">${esc(this._rateLabel(meter))}</span><span class="muted">${esc(rateText)}</span></div>
            <div class="row"><ha-icon icon="mdi:check-decagram-outline"></ha-icon><span class="grow">${esc(ui.validSince)}</span><span class="muted">${esc(this._time(reading?.attributes?.last_valid_reading))}</span></div>
            <div class="row"><ha-icon icon="mdi:history"></ha-icon><span class="grow">${esc(ui.lastCheck)}</span><span class="muted">${esc(this._ok(last) ? this._time(last.state) : ui.none)}</span></div>
            ${this._rejectedRow(meter, status)}
            ${readings.length ? `<div class="row"><ha-icon icon="mdi:format-list-numbered"></ha-icon><span class="grow">${esc(ui.readings)}</span><span class="muted">${esc(readings.map((r) => this.labels.status[r] || r).join(" / "))}</span></div>` : ""}
            <div class="row"><ha-icon icon="mdi:clock-outline"></ha-icon><span class="grow">${esc(ui.nextCheck)}</span><span class="muted">${esc(this._ok(next) ? this._time(next.state) : ui.none)}</span></div>
          </div>
        </div>
      </div>
      <div class="actions">
        ${e.automatic ? `<button class="tile ${autoOn ? "on" : ""}" data-action="toggle" data-entity="${esc(e.automatic)}" ${this._ok(auto) ? "" : "disabled"}>
          <ha-icon icon="mdi:timer-cog-outline"></ha-icon><span>${esc(ui.automatic)}</span><span class="switch ${autoOn ? "on" : ""}"></span></button>` : ""}
        <span class="grow"></span>
        <button class="btn" data-action="press" data-entity="${esc(e.test_picture || "")}" ${running || !e.test_picture ? "disabled" : ""}><ha-icon icon="mdi:camera"></ha-icon>${esc(ui.testPicture)}</button>
        <button class="btn primary" data-action="press" data-entity="${esc(e.read_now || "")}" ${running || !e.read_now ? "disabled" : ""}><ha-icon icon="mdi:camera-iris"></ha-icon>${esc(ui.readNow)}</button>
      </div>
      <details data-keep="set-${esc(meter.id)}" ${this._openDetails?.has(`set-${meter.id}`) ? "open" : ""}><summary>${esc(ui.setReading)}</summary>
        <p class="desc">${esc(ui.setReadingHelp)}</p>
        <div class="inline"><span class="with-unit"><input type="number" step="any" min="0" data-set-value="${esc(meter.id)}" value="${esc(this._ok(reading) ? reading.state : "")}"><span class="unit">${esc(meter.data.unit || "")}</span></span>
        <button class="btn" data-action="set-reading" data-meter="${esc(meter.id)}">${esc(ui.set)}</button></div>
      </details>
      <details data-keep="rej-${esc(meter.id)}" data-rejected="${esc(meter.id)}" ${this._openDetails?.has(`rej-${meter.id}`) ? "open" : ""}><summary>${esc(ui.rejected)}</summary>
        <div class="rej-box">${this._rejectedHtml(meter)}</div></details>
      <div class="actions small-actions"><button class="btn flat" data-edit="${esc(meter.id)}"><ha-icon icon="mdi:pencil-outline"></ha-icon>${esc(ui.edit)}</button></div>
    </div>`;
  }

  // a value that was read reliably but rejected by the plausibility check can be taken by hand
  _rejectedRow(meter, status) {
    const value = status?.attributes?.read_value;
    if (!["smaller", "too_large"].includes(status?.state) || value === null || value === undefined) return "";
    const text = `${this._num(value, meter.data.decimals, true)} ${meter.data.unit || ""}`.trim();
    return `<div class="row"><ha-icon icon="mdi:eye-check-outline"></ha-icon><span class="grow">${esc(this.ui.readRejected)}</span>
      <span class="muted">${esc(text)}</span>
      <button class="btn small-btn" data-action="take-value" data-meter="${esc(meter.id)}" data-value="${esc(value)}" data-text="${esc(text)}">${esc(this.ui.takeValue)}</button></div>`;
  }

  // ------------------------------------------------------------------ rejected pictures

  _rejectedKey(meter) {
    return this._state(meter.entities.last_check)?.state || "";
  }

  _rejectedHtml(meter) {
    const cache = this._rejectedPics?.[meter.id];
    if (this._openDetails?.has(`rej-${meter.id}`) && cache?.key !== this._rejectedKey(meter)) {
      setTimeout(() => this._loadRejected(meter.id), 0);
    }
    if (!cache) return `<div class="muted small">…</div>`;
    if (!cache.pictures.length) return `<div class="muted small">${esc(this.ui.noRejected)}</div>`;
    return `<div class="rej-grid">${cache.pictures
      .map((pic) => {
        const m = /^(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})$/.exec(pic.stamp || "");
        const when = m ? this._time(new Date(m[1], m[2] - 1, m[3], m[4], m[5], m[6]).toISOString()) : pic.stamp;
        const status = pic.status ? this.labels.status[pic.status] || pic.status : "";
        return `<figure class="rej"><img src="data:image/jpeg;base64,${pic.image}" alt="" data-action="zoom">
          <figcaption class="small muted">${esc(when)}${status ? ` · ${esc(status)}` : ""}</figcaption></figure>`;
      })
      .join("")}</div>`;
  }

  async _loadRejected(meterId) {
    const meter = this._cfg?.meters.find((m) => m.id === meterId);
    if (!meter || this._rejectedLoading?.has(meterId)) return;
    this._rejectedLoading = this._rejectedLoading || new Set();
    this._rejectedLoading.add(meterId);
    try {
      const key = this._rejectedKey(meter);
      const result = await this._ws({ type: `${DOMAIN}/rejected`, subentry_id: meterId });
      this._rejectedPics = this._rejectedPics || {};
      this._rejectedPics[meterId] = { key, pictures: result.pictures };
      const box = this.shadowRoot.querySelector(`details[data-rejected="${meterId}"] .rej-box`);
      if (box) box.innerHTML = this._rejectedHtml(meter);
    } catch (err) {
      this._toast(err.message || String(err), true);
    } finally {
      this._rejectedLoading.delete(meterId);
    }
  }

  _overview() {
    const ui = this.ui;
    const warnings = [];
    if (!this._cfg.options.ai_task_entity) warnings.push(ui.noAiTask);
    const missing = this._missingEntities();
    if (missing.length) warnings.push(`${ui.missing}: ${missing.join(", ")}`);
    const notes = warnings.length
      ? `<div class="card">${warnings.map((w) => `<div class="row warn-row"><ha-icon icon="mdi:alert-outline"></ha-icon><span>${esc(w)}</span></div>`).join("")}</div>`
      : "";
    const cards = this._cfg.meters.map((m) => this._meterCard(m)).join("");
    const empty = `<div class="card"><div class="muted">${esc(ui.noMeters)}</div>
      <div class="actions"><button class="btn primary" data-new="meter"><ha-icon icon="mdi:plus"></ha-icon>${esc(ui.add)}</button></div></div>`;
    return `${notes}<div class="grid">${cards || empty}</div>`;
  }

  _missingEntities() {
    const missing = new Set();
    const check = (specs, values) => {
      for (const [key, spec] of Object.entries(specs || {})) {
        if (spec.selector !== "entity") continue;
        const id = values[key];
        if (id && !this._state(id)) missing.add(id);
      }
    };
    check(this._cfg.option_specs, this._cfg.options);
    for (const meter of this._cfg.meters) for (const sec of this._cfg.meter_sections) check(sec.fields, meter.data);
    return [...missing];
  }

  // ------------------------------------------------------------------ meters

  _metersTab() {
    const ui = this.ui;
    const [title, desc] = ui.cards.meters;
    const rows = this._cfg.meters
      .map((meter) => {
        const [statusText, statusCls] = this._status(meter);
        return `<tr data-edit="${esc(meter.id)}">
          <td class="c-icon"><ha-icon icon="${TYPE_ICON[meter.data.meter_type] || "mdi:counter"}"></ha-icon></td>
          <td class="c-name"><div>${esc(meter.title)}</div><div class="muted small entity-id">${esc(meter.data.camera)}</div></td>
          <td class="hide-narrow">${esc(this._typeName(meter.data.meter_type))}</td>
          <td class="c-reading">${esc(this._reading(meter))}</td>
          <td class="c-state">${statusText ? `<span class="pill ${statusCls}">${esc(statusText)}</span>` : ""}</td>
          <td class="c-edit hide-narrow"><ha-icon icon="mdi:pencil-outline" class="muted"></ha-icon></td>
        </tr>`;
      })
      .join("");
    return `<div class="card">
      <h2><ha-icon icon="mdi:counter"></ha-icon>${esc(title)}</h2><p class="desc">${esc(desc)}</p>
      ${this._cfg.meters.length
        ? `<div class="table-wrap"><table><thead><tr><th class="c-icon"></th><th class="c-name">${esc(ui.columns.name)}</th><th class="hide-narrow">${esc(ui.columns.type)}</th><th class="c-reading">${esc(ui.columns.reading)}</th><th class="c-state">${esc(ui.columns.status)}</th><th class="c-edit hide-narrow"></th></tr></thead><tbody>${rows}</tbody></table></div>`
        : `<div class="muted">${esc(ui.noMeters)}</div>`}
      <div class="actions"><button class="btn primary" data-new="meter"><ha-icon icon="mdi:plus"></ha-icon>${esc(ui.add)}</button></div>
    </div>`;
  }

  _previewHtml() {
    const ui = this.ui;
    const e = this._edit;
    const meter = e.id ? this._cfg.meters.find((m) => m.id === e.id) : null;
    const lastImage = meter?.entities?.last_image;
    const status = meter ? this._state(meter.entities.status) : null;
    const running = !!status?.attributes?.running;
    const source = lastImage && status?.attributes?.image_time ? lastImage : e.data.camera;
    const caption = source === lastImage ? ui.previewLast : ui.previewLive;
    return `<div class="preview-img">${source ? this._image(source) : this._image(null)}</div>
      <div class="muted small">${esc(caption)}</div>
      ${meter?.entities?.test_picture
        ? `<div class="actions"><span class="msg small">${esc(ui.previewHint)}</span>
            <button class="btn" data-action="press" data-entity="${esc(meter.entities.test_picture)}" ${running ? "disabled" : ""}><ha-icon icon="mdi:camera"></ha-icon>${esc(running ? ui.running[status.attributes.running] : ui.testPicture)}</button></div>`
        : ""}`;
  }

  _updatePreview() {
    const box = this.shadowRoot.querySelector(".preview");
    if (box) box.innerHTML = this._previewHtml();
    // a new picture: load the uncropped one again for the crop editor
    const e = this._edit;
    const meter = e?.id ? this._cfg.meters.find((m) => m.id === e.id) : null;
    const time = meter ? this._state(meter.entities.status)?.attributes?.image_time : null;
    if (e && time && time !== e.originalTime) this._loadOriginal();
  }

  async _loadOriginal(attempt = 0) {
    const e = this._edit;
    if (!e?.id) return;
    const meter = this._cfg.meters.find((m) => m.id === e.id);
    e.originalTime = this._state(meter?.entities?.status)?.attributes?.image_time || null;
    try {
      const result = await this._ws({ type: `${DOMAIN}/original`, subentry_id: e.id });
      if (this._edit !== e) return;
      e.original = result.image ? `data:image/jpeg;base64,${result.image}` : null;
      e.originalImg = null;
      e.turned = null;
      const box = this.shadowRoot.querySelector(".crop-box");
      if (box && !e.live) box.outerHTML = this._cropHtml();
      this._turnPreview();
    } catch (err) {
      // right after saving the integration is reloaded and does not know the meter for a moment
      if (err?.code === "not_found" && attempt < 10) {
        setTimeout(() => this._edit === e && this._loadOriginal(attempt + 1), 1000);
        return;
      }
      this._toast(err.message || String(err), true);
    }
  }

  _cropRect() {
    const d = this._edit.data;
    const n = (k, def) => (d[k] === null || d[k] === undefined || d[k] === "" ? def : Number(d[k]));
    const l = Math.min(n("crop_left", 0), n("crop_right", 100));
    const r = Math.max(n("crop_left", 0), n("crop_right", 100));
    const t = Math.min(n("crop_top", 0), n("crop_bottom", 100));
    const b = Math.max(n("crop_top", 0), n("crop_bottom", 100));
    return { l, t, r, b };
  }

  // the exposure is a plain brightness factor, the browser can show it the same way
  _exposureFilter() {
    const v = Number(this._edit.data.exposure);
    return Number.isFinite(v) && v > 0 ? `brightness(${v / 100})` : "none";
  }

  _rotation() {
    const v = Number(this._edit.data.rotate);
    if (!Number.isFinite(v)) return 0;
    const d = ((v % 360) + 360) % 360;
    return d > 180 ? d - 360 : d;
  }

  // the picture turned like the integration does it (clockwise, grown so nothing is cut off);
  // the crop is drawn on this one
  _turnPreview() {
    const e = this._edit;
    if (!e?.original || this._turning) return;
    this._turning = requestAnimationFrame(() => {
      this._turning = null;
      if (this._edit !== e) return;
      if (!e.originalImg) {
        e.originalImg = new Image();
        e.originalImg.onload = () => this._turnPreview();
        e.originalImg.src = e.original;
        return;
      }
      if (!e.originalImg.complete || !e.originalImg.naturalWidth) return;
      const deg = this._rotation();
      if (e.turned?.deg === deg) return;
      let src = e.original;
      if (deg) {
        const canvas = document.createElement("canvas");
        drawTurned(canvas, e.originalImg, deg);
        src = canvas.toDataURL("image/jpeg", 0.85);
      }
      e.turned = { deg, src };
      const shown = this.shadowRoot.querySelector(".crop-wrap img.pic");
      if (shown) shown.src = src;
    });
  }

  // ------------------------------------------------------------------ live picture

  _streamUrl() {
    const camera = this._edit?.data?.camera;
    const token = this._state(camera)?.attributes?.access_token;
    return camera && token ? `/api/camera_proxy_stream/${encodeURIComponent(camera)}?token=${encodeURIComponent(token)}` : "";
  }

  _liveHtml() {
    const ui = this.ui;
    const e = this._edit;
    if (!e.data.camera) return "";
    const light = e.data.light
      ? `<label class="live-light"><input type="checkbox" data-live-light ${e.liveLight ? "checked" : ""}>${esc(ui.liveLight)}</label>`
      : "";
    return `<div class="live-row">
      <button class="btn ${e.live ? "primary" : ""}" data-action="live"><ha-icon icon="${e.live ? "mdi:stop" : "mdi:video"}"></ha-icon>${esc(e.live ? ui.liveStop : ui.live)}</button>
      ${e.live ? light : ""}${e.live ? `<span class="msg small">${esc(ui.liveHint)}</span>` : ""}</div>`;
  }

  async _startLive() {
    const e = this._edit;
    if (!e || e.live) return;
    e.live = true;
    e.liveLight = !!e.data.light;
    this._renderCrop();
    await this._liveLightSwitch();
    // the frames of the stream are drawn turned onto the canvas until the editor closes
    this._liveTimer = setInterval(() => {
      if (this._edit !== e || !e.live || !this.isConnected) {
        this._stopLive(e);
        return;
      }
      const src = this.shadowRoot.querySelector(".crop-wrap img.live-src");
      const canvas = this.shadowRoot.querySelector(".crop-wrap canvas.pic");
      if (src?.complete && src.naturalWidth && canvas) drawTurned(canvas, src, this._rotation(), 1280);
    }, 150);
  }

  _stopLive(e = this._edit) {
    clearInterval(this._liveTimer);
    this._liveTimer = null;
    // an empty source closes the stream
    const src = this.shadowRoot.querySelector(".crop-wrap img.live-src");
    if (src) src.src = "";
    if (!e?.live) return;
    e.live = false;
    if (e.lightOn) this._call("light", "turn_off", { entity_id: e.lightOn });
    e.lightOn = null;
    if (this._edit === e) this._renderCrop();
  }

  async _liveLightSwitch() {
    const e = this._edit;
    if (!e) return;
    const want = e.live && e.liveLight && e.data.light ? e.data.light : null;
    if (e.lightOn && e.lightOn !== want) {
      await this._call("light", "turn_off", { entity_id: e.lightOn });
      e.lightOn = null;
    }
    if (want) {
      const brightness = Number(e.data.light_brightness);
      await this._call("light", "turn_on", { entity_id: want, ...(brightness > 0 ? { brightness_pct: brightness } : {}) });
      e.lightOn = want;
    }
  }

  _renderCrop() {
    const box = this.shadowRoot.querySelector(".crop-box");
    if (box) box.outerHTML = this._cropHtml();
  }

  disconnectedCallback() {
    if (this._edit?.live) this._stopLive(this._edit);
  }

  _cropHtml() {
    const ui = this.ui;
    const e = this._edit;
    const live = e.live ? this._streamUrl() : "";
    if (!e.original && !live) {
      return `<div class="crop-box">${this._liveHtml()}<div class="muted small">${esc(e.id ? ui.cropNoImage : ui.previewHint)}</div></div>`;
    }
    const { l, t, r, b } = this._cropRect();
    const deg = this._rotation();
    const src = e.turned?.deg === deg ? e.turned.src : deg ? "" : e.original;
    if (!src && !live) this._turnPreview();
    const filter = `filter:${this._exposureFilter()}`;
    const picture = live
      ? `<canvas class="pic" style="${filter}"></canvas><img class="live-src" src="${esc(live)}" alt="">`
      : `<img class="pic" src="${src}" alt="" draggable="false" style="${filter}">`;
    return `<div class="crop-box">${this._liveHtml()}
      <div class="rotate-row"><span class="lbl">${esc(ui.rotate)}</span>
        <button class="btn" data-action="rotate-step" data-step="-90" title="-90°">↺ 90°</button>
        <input type="range" data-card-id="edit" data-k="rotate" data-type="number" min="-180" max="180" step="0.5" value="${deg}">
        <button class="btn" data-action="rotate-step" data-step="90" title="+90°">↻ 90°</button></div>
      <div class="crop-wrap" data-crop="1">${picture}
        <div class="crop-rect" style="left:${l}%;top:${t}%;width:${r - l}%;height:${b - t}%"><i class="h tl"></i><i class="h tr"></i><i class="h bl"></i><i class="h br"></i></div></div>
      <div class="actions"><span class="msg small">${esc(ui.cropHelp)}</span><button class="btn" data-action="crop-reset">${esc(ui.cropReset)}</button></div>
    </div>`;
  }

  _setRotation(deg, source) {
    const e = this._edit;
    e.data.rotate = deg;
    for (const input of this.shadowRoot.querySelectorAll('input[data-card-id="edit"][data-k="rotate"]')) {
      if (input !== source) input.value = deg;
    }
    this._turnPreview();
  }

  _setCrop(l, t, r, b) {
    const round = (v) => Math.round(Math.max(0, Math.min(100, v)) * 2) / 2;
    const values = { crop_left: round(l), crop_top: round(t), crop_right: round(r), crop_bottom: round(b) };
    for (const [k, v] of Object.entries(values)) {
      this._edit.data[k] = v;
      const input = this.shadowRoot.querySelector(`input[data-card-id="edit"][data-k="${k}"]`);
      if (input) input.value = v;
    }
    const rect = this.shadowRoot.querySelector(".crop-rect");
    if (rect) Object.assign(rect.style, { left: `${values.crop_left}%`, top: `${values.crop_top}%`, width: `${values.crop_right - values.crop_left}%`, height: `${values.crop_bottom - values.crop_top}%` });
  }

  // what a pointer at x/y (percent) does with the frame: a corner resizes it, inside moves it,
  // outside draws a new one
  _cropHit(wrap, x, y) {
    const rect = this._cropRect();
    const box = wrap.getBoundingClientRect();
    const tx = (14 / box.width) * 100;
    const ty = (14 / box.height) * 100;
    const whole = rect.l <= 0 && rect.t <= 0 && rect.r >= 100 && rect.b >= 100;
    if (!whole) {
      for (const [mode, cx, cy] of [["tl", rect.l, rect.t], ["tr", rect.r, rect.t], ["bl", rect.l, rect.b], ["br", rect.r, rect.b]]) {
        if (Math.abs(x - cx) <= tx && Math.abs(y - cy) <= ty) return mode;
      }
      if (x > rect.l && x < rect.r && y > rect.t && y < rect.b) return "move";
    }
    return "new";
  }

  _cropPointer(ev) {
    const wrap = ev.target.closest?.("[data-crop]");
    const pos = (el) => {
      const box = el.getBoundingClientRect();
      return [((ev.clientX - box.left) / box.width) * 100, ((ev.clientY - box.top) / box.height) * 100];
    };
    if (ev.type === "pointerdown") {
      if (!wrap) return;
      ev.preventDefault();
      wrap.setPointerCapture(ev.pointerId);
      const [x, y] = pos(wrap);
      this._drag = { wrap, x, y, mode: this._cropHit(wrap, x, y), rect: this._cropRect() };
      return;
    }
    if (!this._drag) {
      // show what dragging would do
      if (ev.type === "pointermove" && wrap) {
        const [x, y] = pos(wrap);
        const mode = this._cropHit(wrap, x, y);
        wrap.style.cursor = { move: "move", tl: "nwse-resize", br: "nwse-resize", tr: "nesw-resize", bl: "nesw-resize" }[mode] || "crosshair";
      }
      return;
    }
    const [x, y] = pos(this._drag.wrap);
    const { x: x0, y: y0, mode, rect } = this._drag;
    if (mode === "move") {
      const w = rect.r - rect.l;
      const h = rect.b - rect.t;
      const l = Math.max(0, Math.min(100 - w, rect.l + x - x0));
      const t = Math.max(0, Math.min(100 - h, rect.t + y - y0));
      this._setCrop(l, t, l + w, t + h);
    } else if (mode === "new") {
      if (Math.abs(x - x0) > 0.5 && Math.abs(y - y0) > 0.5) this._setCrop(Math.min(x0, x), Math.min(y0, y), Math.max(x0, x), Math.max(y0, y));
    } else {
      const edges = { ...rect };
      edges[mode[1] === "l" ? "l" : "r"] = x;
      edges[mode[0] === "t" ? "t" : "b"] = y;
      this._setCrop(Math.min(edges.l, edges.r), Math.min(edges.t, edges.b), Math.max(edges.l, edges.r), Math.max(edges.t, edges.b));
    }
    if (ev.type === "pointerup" || ev.type === "pointercancel") this._drag = null;
  }

  _editor() {
    const ui = this.ui;
    const e = this._edit;
    const title = e.id ? e.title || e.originalTitle : ui.newMeter;
    const typeSpec = { selector: "select", options: this._cfg.meter_types, translation_key: "types" };
    const groups = this._cfg.meter_sections
      .map(({ id, fields }) => {
        const [name, desc] = this.labels.sections[id] || [id, ""];
        const html = Object.entries(fields)
          .filter(([key]) => key !== "prompt")
          .map(([key, spec]) => this._field("edit", key, spec, e.data[key]))
          .join("");
        const crop = id === "image_section" ? this._cropHtml() : "";
        const body = `${desc ? `<p class="desc">${esc(desc)}</p>` : ""}${crop}<div class="fields">${html}</div>`;
        if (!COLLAPSED.has(id)) return `<h3>${esc(name)}</h3>${body}`;
        return `<details data-section="${id}" ${e.open.has(id) ? "open" : ""}><summary>${esc(name)}</summary>${body}</details>`;
      })
      .join("");
    return `<div class="card" data-card="edit">
      <h2><button class="icon-btn" data-action="close-edit"><ha-icon icon="mdi:arrow-left"></ha-icon></button>
        <ha-icon icon="${TYPE_ICON[e.data.meter_type] || "mdi:counter"}"></ha-icon>${esc(title)}</h2>
      <div class="edit-top">
        <div class="fields">${this._field("edit", "name", { selector: "text" }, e.title)}${this._field("edit", "meter_type", typeSpec, e.data.meter_type)}</div>
        <div class="preview">${this._previewHtml()}</div>
      </div>
      ${groups}
      <details class="prompt-box" ${e.prompt || this._customPrompt() ? "open" : ""} data-action="prompt"><summary>${esc(ui.prompt)}</summary><div class="prompt-body">${this._promptHtml()}</div></details>
      <div class="actions"><span class="msg"></span>
        ${e.id ? `<button class="btn danger" data-action="delete-meter">${esc(ui.delete)}</button>` : ""}
        <span class="grow"></span>
        <button class="btn" data-action="close-edit">${esc(ui.cancel)}</button>
        <button class="btn primary" data-action="save-meter">${esc(ui.save)}</button></div>
    </div>`;
  }

  // ------------------------------------------------------------------ settings

  _settingsTab() {
    const [title, desc] = this.ui.cards.general;
    const specs = this._cfg.option_specs;
    const fields = Object.keys(specs).map((key) => this._field("general", key, specs[key], this._value("general", key))).join("");
    return `<div class="card" data-card="general"><h2><ha-icon icon="mdi:cog-outline"></ha-icon>${esc(title)}</h2><p class="desc">${esc(desc)}</p>
      <div class="fields">${fields}</div>${this._actions("general")}</div>`;
  }

  _value(cardId, key) {
    const draft = this._drafts[cardId];
    if (draft && key in draft) return draft[key];
    return this._cfg.options[key];
  }

  _actions(cardId) {
    const dirty = !!this._drafts[cardId];
    return `<div class="actions"><span class="msg"></span>
      ${dirty ? `<button class="btn" data-cancel="${cardId}">${esc(this.ui.cancel)}</button>` : ""}
      <button class="btn primary" data-save="${cardId}" ${dirty ? "" : "disabled"}>${esc(this.ui.save)}</button></div>`;
  }

  _toggle(cardId, key, name, help, on) {
    return `<label class="field toggle-row"><span><span class="lbl">${esc(name)}</span>${help ? `<small>${esc(help)}</small>` : ""}</span>
      <input type="checkbox" class="switch-input" data-card-id="${cardId}" data-k="${key}" data-type="bool" ${on ? "checked" : ""}><span class="switch ${on ? "on" : ""}"></span></label>`;
  }

  _field(cardId, key, spec, value) {
    const ui = this.ui;
    const [name, help] = this.label(key);
    const kind = spec?.selector || "text";
    const helpHtml = help ? `<small>${esc(help)}</small>` : "";
    const attrs = (type) => `data-card-id="${cardId}" data-k="${key}" data-type="${type}"`;
    switch (kind) {
      case "boolean":
        return this._toggle(cardId, key, name, help, !!value);
      case "number": {
        const unit = spec.unit_of_measurement || (["max_rate", "max_correction"].includes(key) ? this._edit?.data?.unit : "");
        return `<label class="field"><span class="lbl">${esc(name)}</span><span class="with-unit">
          <input type="number" ${attrs("number")} value="${esc(value ?? "")}" min="${spec.min ?? ""}" max="${spec.max ?? ""}" step="${spec.step ?? "any"}">
          ${unit ? `<span class="unit">${esc(unit)}</span>` : ""}</span>${helpHtml}</label>`;
      }
      case "select": {
        const options = (spec.options || []).map((o) => (typeof o === "object" ? o.value : o));
        const texts = spec.translation_key ? this.labels[spec.translation_key] || {} : {};
        if (spec.custom_value) {
          return `<label class="field"><span class="lbl">${esc(name)}</span><input type="text" list="dl-opt-${esc(key)}" ${attrs("text")} value="${esc(value ?? "")}" autocomplete="off">${helpHtml}</label>`;
        }
        return `<label class="field"><span class="lbl">${esc(name)}</span><select ${attrs("text")}>
          ${options.map((opt) => `<option value="${esc(opt)}" ${opt === value ? "selected" : ""}>${esc(texts[opt] || opt)}</option>`).join("")}
          </select>${helpHtml}</label>`;
      }
      case "entity": {
        const st = value ? this._state(value) : null;
        const hint = value ? (st ? this._name(value) : `⚠ ${ui.notFound}`) : "";
        return `<label class="field"><span class="lbl">${esc(name)}</span>
          <input type="text" list="${this._listId(spec)}" ${attrs("entity")} value="${esc(value ?? "")}" placeholder="${esc(domainsOf(spec)[0] || "entity")}.…" autocomplete="off">
          <span class="entity-hint ${value && !st ? "bad" : ""}">${esc(hint)}</span>${helpHtml}</label>`;
      }
      case "text":
        if (spec.multiline) {
          return `<label class="field wide"><span class="lbl">${esc(name)}</span><textarea rows="4" ${attrs("text")}>${esc(value ?? "")}</textarea>${helpHtml}</label>`;
        }
        return `<label class="field"><span class="lbl">${esc(name)}</span><input type="text" ${attrs("text")} value="${esc(value ?? "")}">${helpHtml}</label>`;
      default:
        return `<label class="field"><span class="lbl">${esc(name)}</span><input type="text" ${attrs("text")} value="${esc(value ?? "")}">${helpHtml}</label>`;
    }
  }

  // ------------------------------------------------------------------ events

  _setValue(cardId, key, value) {
    if (cardId === "edit") {
      if (key === "name") this._edit.title = value;
      else this._edit.data[key] = value;
      if (key === "meter_type") this._typeChanged(value);
      else if (["unit", "decimals", "hints"].includes(key)) this._edit.prompt = null;
      return;
    }
    this._drafts[cardId] = this._drafts[cardId] || {};
    this._drafts[cardId][key] = value;
    const save = this.shadowRoot.querySelector(`[data-save="${cardId}"]`);
    if (save) save.disabled = false;
  }

  _typeChanged(type) {
    const e = this._edit;
    // a new meter takes the defaults of the type; an existing one keeps its values
    if (!e.id) {
      const defaults = this._cfg.type_defaults[type] || {};
      for (const key of TYPE_FIELDS) if (key in defaults) e.data[key] = defaults[key];
    }
    e.prompt = null;
    this._rerenderContent();
  }

  _onInput(ev, isChange = false) {
    const el = ev.target;
    if (el.dataset.liveLight !== undefined && isChange && this._edit) {
      this._edit.liveLight = el.checked;
      this._liveLightSwitch();
      return;
    }
    const cardId = el.dataset.cardId;
    const key = el.dataset.k;
    if (!cardId || !key) return;
    const type = el.dataset.type;
    if (key === "meter_type" && !isChange) return;
    let value;
    if (type === "bool" || el.type === "checkbox") {
      value = el.checked;
      const sw = el.nextElementSibling;
      if (sw?.classList.contains("switch")) sw.classList.toggle("on", value);
    } else if (type === "number") {
      value = el.value === "" ? null : Number(el.value);
    } else {
      value = el.value;
    }
    if (type === "entity") {
      const hint = el.parentElement.querySelector(".entity-hint");
      if (hint) {
        const st = value ? this._state(value) : null;
        hint.textContent = value ? (st ? this._name(value) : `⚠ ${this.ui.notFound}`) : "";
        hint.classList.toggle("bad", !!value && !st);
      }
    }
    this._setValue(cardId, key, value);
    if (cardId === "edit" && key === "camera" && isChange) this._updatePreview();
    if (cardId === "edit" && key.startsWith("crop_")) {
      const { l, t, r, b } = this._cropRect();
      const rect = this.shadowRoot.querySelector(".crop-rect");
      if (rect) Object.assign(rect.style, { left: `${l}%`, top: `${t}%`, width: `${r - l}%`, height: `${b - t}%` });
    }
    if (cardId === "edit" && key === "rotate" && value !== null) this._setRotation(value, el);
    if (cardId === "edit" && key === "exposure") {
      const pic = this.shadowRoot.querySelector(".crop-wrap .pic");
      if (pic) pic.style.filter = this._exposureFilter();
    }
    if (cardId === "edit" && this._edit.live && isChange) {
      if (key === "camera") this._renderCrop();
      if (["light", "light_brightness"].includes(key)) this._liveLightSwitch();
    }
    if (cardId === "edit" && key === "unit" && isChange) this._rerenderContent();
  }

  _rerenderContent(focusSelector) {
    const content = this.shadowRoot.querySelector(".content");
    if (!content) return;
    if (this._edit) {
      for (const details of content.querySelectorAll("details[data-section]")) {
        if (details.open) this._edit.open.add(details.dataset.section);
        else this._edit.open.delete(details.dataset.section);
      }
    }
    this._openDetails = this._openDetails || new Set();
    for (const details of content.querySelectorAll("details[data-keep]")) {
      if (details.open) this._openDetails.add(details.dataset.keep);
      else this._openDetails.delete(details.dataset.keep);
    }
    // keep values typed into the manual reading fields
    const typed = {};
    for (const input of content.querySelectorAll("[data-set-value]")) {
      if (input === this.shadowRoot.activeElement) typed[input.dataset.setValue] = input.value;
    }
    const scroll = content.scrollTop;
    content.innerHTML = this._content();
    content.scrollTop = scroll;
    for (const [id, value] of Object.entries(typed)) {
      const input = content.querySelector(`[data-set-value="${id}"]`);
      if (input) {
        input.value = value;
        input.focus();
      }
    }
    if (focusSelector) content.querySelector(focusSelector)?.focus();
  }

  _openEditor(meter) {
    if (meter) {
      this._edit = { id: meter.id, title: meter.title, originalTitle: meter.title, data: clone(meter.data), open: new Set(), prompt: null, original: null };
      this._loadOriginal();
    } else {
      const type = "heat";
      this._edit = { id: null, title: "", data: { ...clone(this._cfg.type_defaults[type]) }, open: new Set(), prompt: null };
    }
    this._edit.saved = this._editSnapshot();
  }

  _editSnapshot() {
    const e = this._edit;
    return JSON.stringify({ title: e.title, data: e.data });
  }

  // leaving the editor: ask when there are unsaved changes
  _leaveEdit() {
    if (!this._edit || this._editSnapshot() === this._edit.saved) return true;
    return confirm(this.ui.confirmDiscard);
  }

  _customPrompt() {
    const text = this._edit?.data?.prompt;
    return typeof text === "string" && text.trim() !== "";
  }

  // the generated instructions as text, or the own ones in a text field
  _promptHtml() {
    const ui = this.ui;
    const e = this._edit;
    if (this._customPrompt() || e.promptEditing) {
      return `<p class="desc"><span class="pill warn">${esc(ui.promptOwn)}</span> ${esc(ui.promptCustom)}</p>
        <textarea class="prompt-edit" rows="14" data-card-id="edit" data-k="prompt" data-type="text">${esc(e.data.prompt || "")}</textarea>
        <div class="actions"><button class="btn" data-action="prompt-reset">${esc(ui.promptReset)}</button></div>`;
    }
    return `<p class="desc">${esc(ui.promptStandard)}</p><pre class="prompt">${esc(e.prompt || "…")}</pre>
      <div class="actions"><button class="btn" data-action="prompt-edit" ${e.prompt ? "" : "disabled"}><ha-icon icon="mdi:pencil-outline"></ha-icon>${esc(ui.promptEdit)}</button></div>`;
  }

  _renderPrompt() {
    const body = this.shadowRoot.querySelector(".prompt-box .prompt-body");
    if (body) body.innerHTML = this._promptHtml();
  }

  async _showPrompt(details) {
    if (!details.open || this._edit.prompt) return;
    const e = this._edit;
    try {
      const result = await this._ws({ type: `${DOMAIN}/prompt`, data: { ...e.data } });
      if (this._edit !== e) return;
      e.prompt = result.standard;
      if (!this._customPrompt()) this._renderPrompt();
    } catch (err) {
      this._toast(err.message || String(err), true);
    }
  }

  async _onClick(ev) {
    const summary = ev.target.closest("summary");
    if (summary && summary.parentElement?.dataset.action === "prompt") {
      const details = summary.parentElement;
      setTimeout(() => this._showPrompt(details), 0);
      return;
    }
    if (summary && summary.parentElement?.dataset.rejected) {
      const details = summary.parentElement;
      setTimeout(() => {
        const key = `rej-${details.dataset.rejected}`;
        this._openDetails = this._openDetails || new Set();
        if (details.open) {
          this._openDetails.add(key);
          this._loadRejected(details.dataset.rejected);
        } else this._openDetails.delete(key);
      }, 0);
      return;
    }
    const el = ev.target.closest("button, img[data-action], [data-edit], [data-tab]");
    if (!el || el.disabled) return;
    const d = el.dataset;
    if (d.tab) {
      if (!this._leaveEdit()) return;
      this._tab = d.tab;
      this._edit = null;
      this._render();
      return;
    }
    if (d.save) return this._saveCard(d.save, el);
    if (d.cancel) {
      delete this._drafts[d.cancel];
      this._rerenderContent();
      return;
    }
    if (d.new) {
      this._openEditor(null);
      this._rerenderContent();
      return;
    }
    if (d.edit) {
      const meter = this._cfg.meters.find((m) => m.id === d.edit);
      if (meter) {
        this._openEditor(meter);
        this._rerenderContent();
      }
      return;
    }
    switch (d.action) {
      case "menu":
        this.dispatchEvent(new Event("hass-toggle-menu", { bubbles: true, composed: true }));
        break;
      case "toggle": {
        const st = this._state(d.entity);
        await this._call("switch", st?.state === "on" ? "turn_off" : "turn_on", { entity_id: d.entity });
        break;
      }
      case "press":
        if (d.entity) await this._call("button", "press", { entity_id: d.entity });
        break;
      case "more-info":
        if (d.entity) this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId: d.entity }, bubbles: true, composed: true }));
        break;
      case "set-reading":
        await this._setReading(d.meter, el);
        break;
      case "take-value":
        if (confirm(this.ui.confirmTake.replace("{value}", d.text))) await this._writeReading(d.meter, Number(d.value), el);
        break;
      case "zoom": {
        const zoom = this.shadowRoot.querySelector(".zoom");
        if (zoom) {
          zoom.querySelector("img").src = el.src;
          zoom.hidden = false;
        }
        break;
      }
      case "zoom-close":
        el.hidden = true;
        break;
      case "prompt-edit": {
        const e = this._edit;
        if (!e?.prompt) break;
        e.data.prompt = e.prompt;
        e.promptEditing = true;
        this._renderPrompt();
        this.shadowRoot.querySelector(".prompt-edit")?.focus();
        break;
      }
      case "prompt-reset":
        if (!this._customPrompt() || confirm(this.ui.confirmPromptReset)) {
          this._edit.data.prompt = "";
          this._edit.promptEditing = false;
          this._renderPrompt();
          // the generated text may not be loaded yet
          const details = this.shadowRoot.querySelector(".prompt-box");
          if (details) this._showPrompt(details);
        }
        break;
      case "crop-reset":
        this._setCrop(0, 0, 100, 100);
        break;
      case "live":
        if (this._edit?.live) this._stopLive();
        else await this._startLive();
        break;
      case "rotate-step": {
        const deg = ((((this._rotation() + Number(d.step)) % 360) + 540) % 360) - 180;
        this._setRotation(deg === -180 ? 180 : deg);
        break;
      }
      case "close-edit":
        if (!this._leaveEdit()) break;
        this._edit = null;
        this._rerenderContent();
        break;
      case "save-meter":
        await this._saveMeter(el);
        break;
      case "delete-meter":
        if (confirm(this.ui.confirmDelete)) {
          try {
            this._cfg = await this._ws({ type: `${DOMAIN}/delete_meter`, subentry_id: this._edit.id });
            this._edit = null;
            this._render();
            this._toast(this.ui.saved);
          } catch (err) {
            this._cardMessage(el, err.message || String(err), true);
          }
        }
        break;
      default:
        break;
    }
  }

  async _call(domain, service, data) {
    try {
      await this._hass.callService(domain, service, data);
    } catch (err) {
      this._toast(err.message || String(err), true);
    }
  }

  async _setReading(meterId, button) {
    const input = this.shadowRoot.querySelector(`[data-set-value="${meterId}"]`);
    const value = Number(input?.value);
    if (!input || input.value === "" || Number.isNaN(value) || value < 0) {
      this._toast(this.ui.errors.invalid_value, true);
      return;
    }
    input.blur();
    await this._writeReading(meterId, value, button);
  }

  async _writeReading(meterId, value, button) {
    button.disabled = true;
    try {
      this._cfg = await this._ws({ type: `${DOMAIN}/set_reading`, subentry_id: meterId, value });
      this._rerenderContent();
      this._toast(this.ui.saved);
    } catch (err) {
      button.disabled = false;
      this._toast(err.message || String(err), true);
    }
  }

  async _saveCard(cardId, button) {
    const draft = this._drafts[cardId];
    if (!draft) return;
    button.disabled = true;
    try {
      this._cfg = await this._ws({ type: `${DOMAIN}/save_options`, options: { ...draft } });
      delete this._drafts[cardId];
      this._rerenderContent();
      this._toast(this.ui.saved);
    } catch (err) {
      button.disabled = false;
      this._cardMessage(button, this._errorText(err.message || String(err)), true);
    }
  }

  async _saveMeter(button) {
    const e = this._edit;
    const msg = { type: `${DOMAIN}/save_meter`, title: e.title || "", data: { ...e.data } };
    if (e.id) msg.subentry_id = e.id;
    button.disabled = true;
    try {
      const result = await this._ws(msg);
      this._cfg = result.config;
      // stay in the editor: take a test picture, adjust the crop, save again
      if (this._edit === e) {
        e.id = result.subentry_id;
        e.originalTitle = e.title;
        const meter = this._cfg.meters.find((m) => m.id === e.id);
        if (meter) e.data = clone(meter.data);
        e.saved = this._editSnapshot();
        e.prompt = null;
        e.promptEditing = this._customPrompt();
        this._rerenderContent();
        this._loadOriginal();
      }
      this._toast(this.ui.saved);
    } catch (err) {
      button.disabled = false;
      this._cardMessage(button, this._errorText(err.message || String(err)), true);
    }
  }

  _cardMessage(el, text, bad = false) {
    const msg = el.closest(".card")?.querySelector(".actions .msg");
    if (msg) {
      msg.textContent = text;
      msg.classList.toggle("bad", bad);
    }
  }

  _toast(text, bad = false) {
    const toast = this.shadowRoot.querySelector(".toast");
    if (!toast) return;
    toast.textContent = text;
    toast.classList.toggle("bad", bad);
    toast.hidden = false;
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => (toast.hidden = true), 2500);
  }
}

const STYLE = `
:host { display:block; min-height:100vh; overflow-x:hidden; background:var(--primary-background-color); color:var(--primary-text-color); font-family:var(--paper-font-body1_-_font-family, Roboto, sans-serif); }
* { box-sizing:border-box; }
.toolbar { display:flex; align-items:center; height:56px; padding:0 12px; background:var(--app-header-background-color, var(--primary-color)); color:var(--app-header-text-color, #fff); gap:8px; }
.title { display:flex; align-items:center; gap:10px; font-size:20px; font-weight:400; }
.tabs { display:flex; overflow-x:auto; background:var(--app-header-background-color, var(--primary-color)); padding:0 8px; scrollbar-width:none; }
.tab { display:flex; align-items:center; gap:6px; background:none; border:none; color:var(--app-header-text-color, #fff); opacity:.75; padding:10px 14px; cursor:pointer; border-bottom:2px solid transparent; font-size:14px; white-space:nowrap; }
.tab.active { opacity:1; border-bottom-color:var(--app-header-text-color, #fff); }
.tab ha-icon { --mdc-icon-size:20px; }
.content { padding:16px; max-width:1200px; margin:0 auto; }
.grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(340px, 1fr)); gap:16px; align-items:start; }
.content > .card { margin-bottom:16px; }
.card { min-width:0; overflow-wrap:anywhere; background:var(--ha-card-background, var(--card-background-color, #fff)); border-radius:var(--ha-card-border-radius, 12px); border:1px solid var(--divider-color, #e0e0e0); padding:16px; box-shadow:var(--ha-card-box-shadow, none); }
.card.error { color:var(--error-color); }
h2 { display:flex; align-items:center; gap:10px; margin:0 0 4px; font-size:18px; font-weight:500; }
h2 ha-icon { color:var(--state-icon-color, var(--primary-color)); }
h3 { margin:20px 0 4px; font-size:15px; font-weight:500; }
.desc { margin:0 0 12px; color:var(--secondary-text-color); font-size:14px; }
.fields { display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:12px 20px; margin-top:8px; }
.field { display:flex; flex-direction:column; gap:4px; font-size:14px; }
.lbl { font-weight:500; }
small { color:var(--secondary-text-color); font-size:12px; line-height:1.3; }
input[type=text], input[type=number], input[type=time], input[type=password], select {
  font:inherit; color:var(--primary-text-color); background:var(--input-fill-color, var(--secondary-background-color, #f5f5f5));
  border:1px solid var(--divider-color, #ccc); border-radius:8px; padding:8px 10px; width:100%; }
input:focus, select:focus { outline:2px solid var(--primary-color); outline-offset:-1px; }
.with-unit { display:flex; align-items:center; gap:6px; }
.unit { color:var(--secondary-text-color); min-width:24px; white-space:nowrap; }
.entity-hint { font-size:12px; color:var(--secondary-text-color); min-height:14px; }
.entity-hint.bad, .msg.bad { color:var(--error-color, #db4437); }
.toggle-row { flex-direction:row; align-items:center; justify-content:space-between; gap:12px; cursor:pointer; }
.toggle-row > span:first-child { display:flex; flex-direction:column; gap:2px; }
.switch-input { display:none; }
.switch { position:relative; flex:none; width:36px; height:20px; border-radius:10px; background:var(--switch-unchecked-track-color, #9e9e9e); transition:background .2s; }
.switch::after { content:""; position:absolute; top:2px; left:2px; width:16px; height:16px; border-radius:50%; background:#fff; transition:left .2s; }
.switch.on { background:var(--switch-checked-track-color, var(--primary-color)); }
.switch.on::after { left:18px; }
.actions { display:flex; align-items:center; justify-content:flex-end; gap:8px; margin-top:16px; flex-wrap:wrap; }
.msg { margin-right:auto; font-size:13px; color:var(--secondary-text-color); }
.grow { flex:1; }
.btn { display:inline-flex; align-items:center; gap:6px; font:inherit; font-weight:500; border-radius:18px; padding:8px 16px; cursor:pointer; border:1px solid var(--divider-color); background:none; color:var(--primary-color); }
.btn ha-icon { --mdc-icon-size:18px; }
.btn.primary { background:var(--primary-color); color:var(--text-primary-color, #fff); border-color:var(--primary-color); }
.btn.danger { color:var(--error-color, #db4437); border-color:var(--error-color, #db4437); }
.btn:disabled { opacity:.45; cursor:default; }
.icon-btn { background:none; border:none; color:inherit; cursor:pointer; padding:4px; display:inline-flex; }
.tile { display:flex; align-items:center; gap:8px; padding:10px; border-radius:10px; border:1px solid var(--divider-color); background:none; color:var(--primary-text-color); cursor:pointer; text-align:left; font:inherit; font-size:14px; }
.tile span:nth-child(2) { flex:1; }
.tile.on { border-color:var(--primary-color); }
.tile.on ha-icon { color:var(--primary-color); }
.tile:disabled { opacity:.45; cursor:default; }
.rows { display:flex; flex-direction:column; }
.row { display:flex; align-items:center; gap:10px; padding:8px 4px; border-bottom:1px solid var(--divider-color); font:inherit; font-size:14px; color:var(--primary-text-color); background:none; border-left:none; border-right:none; border-top:none; text-align:left; width:100%; }
.row:last-child { border-bottom:none; }
.row > span { min-width:0; overflow-wrap:anywhere; }
.row > span.grow { flex:1 1 40%; min-width:7em; overflow-wrap:normal; }
.row > span.muted { flex:0 1 auto; text-align:right; }
tbody tr:hover { background:var(--secondary-background-color, #f5f5f5); }
.warn-row ha-icon { color:var(--warning-color, #ffa600); flex:none; }
.muted { color:var(--secondary-text-color); }
.small { font-size:12px; }
.pill { flex:none; display:inline-block; border-radius:12px; padding:2px 10px; margin:1px 0; font-size:12px; background:var(--secondary-background-color, #eee); white-space:nowrap; }
.pill.ok { background:rgba(67,160,71,.15); color:var(--success-color, #2e7d32); }
.pill.warn { background:rgba(255,166,0,.18); color:var(--warning-color, #b26a00); }
.pill.bad { background:rgba(219,68,55,.15); color:var(--error-color, #db4437); }
.pill.muted { color:var(--secondary-text-color); }
.table-wrap { width:100%; overflow-x:auto; }
table { width:100%; border-collapse:collapse; font-size:14px; table-layout:fixed; }
th.c-icon { width:40px; } th.c-state { width:150px; } th.c-edit { width:32px; }
td.c-name div { overflow-wrap:anywhere; }
td.c-name div:first-child { overflow-wrap:break-word; hyphens:auto; }
td.c-state .pill { margin-right:4px; }
th { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; text-align:left; font-weight:500; color:var(--secondary-text-color); padding:6px 8px; border-bottom:1px solid var(--divider-color); }
td { padding:8px; border-bottom:1px solid var(--divider-color); vertical-align:middle; }
tbody tr { cursor:pointer; }
details { margin-top:16px; }
summary { cursor:pointer; font-weight:500; color:var(--primary-color); }
details .desc { margin-top:8px; }
.toast { position:fixed; bottom:24px; left:50%; transform:translateX(-50%); background:var(--primary-text-color); color:var(--primary-background-color); padding:10px 18px; border-radius:8px; z-index:10; }
.toast.bad { background:var(--error-color, #db4437); color:#fff; }
@media (max-width: 700px) {
  .hide-narrow { display:none; } .content { padding:8px; } .grid { grid-template-columns:1fr; }
  .tab span { display:none; } .tab.active span { display:inline; } .tab { padding:10px 12px; }
  .fields { grid-template-columns:1fr; }
  th.c-icon { width:32px; } th.c-state { width:110px; }
  td { padding:8px 4px; } .entity-id { font-size:11px; }
  .card { padding:12px; }
}
.meter-head { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.meter-head h2 { margin:0; }
.meter-body { display:grid; grid-template-columns:minmax(0, 5fr) minmax(0, 6fr); gap:16px; margin-top:12px; align-items:start; }
.meter-img img, .preview-img img { width:100%; border-radius:8px; display:block; cursor:pointer; background:#000; }
.img-empty { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:6px; aspect-ratio:4/3; border-radius:8px; border:1px dashed var(--divider-color); color:var(--secondary-text-color); font-size:13px; }
.big { font:inherit; font-size:28px; font-weight:500; background:none; border:none; padding:0 4px 8px; color:var(--primary-text-color); text-align:left; cursor:pointer; }
.pill.run { background:rgba(3,169,244,.15); color:var(--info-color, #0288d1); }
.actions .tile { margin-right:auto; }
.small-actions { margin-top:8px; }
.btn.flat { border:none; padding:6px 8px; }
.btn.small-btn { padding:4px 12px; font-size:13px; }
.rej-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(120px, 1fr)); gap:8px; margin-top:8px; }
.rej { margin:0; display:flex; flex-direction:column; gap:2px; }
.rej img { width:100%; border-radius:6px; cursor:zoom-in; background:#000; display:block; }
.zoom { position:fixed; inset:0; z-index:20; border:none; padding:16px; background:rgba(0,0,0,.85); display:flex; align-items:center; justify-content:center; cursor:zoom-out; }
.zoom[hidden] { display:none; }
.zoom img { max-width:100%; max-height:100%; border-radius:8px; }
.inline { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.inline .with-unit { flex:1; min-width:160px; }
.edit-top { display:grid; grid-template-columns:minmax(0, 1fr) minmax(0, 1fr); gap:20px; align-items:start; }
.edit-top .fields { grid-template-columns:1fr; }
.preview { display:flex; flex-direction:column; gap:6px; }
.preview .actions { margin-top:4px; }
.field.wide { grid-column:1 / -1; }
.crop-box { margin:8px 0; }
.rotate-row { display:flex; align-items:center; gap:8px; margin-bottom:8px; flex-wrap:wrap; }
.rotate-row input[type=range] { flex:1; min-width:140px; }
.crop-wrap { position:relative; display:inline-block; max-width:100%; touch-action:none; cursor:crosshair; user-select:none; line-height:0; overflow:hidden; border-radius:8px; }
.crop-wrap img, .crop-wrap canvas { max-width:100%; max-height:420px; border-radius:8px; display:block; pointer-events:none; }
.crop-wrap img.live-src { position:absolute; width:1px; height:1px; opacity:0; }
.live-row { display:flex; align-items:center; gap:8px; margin-bottom:8px; flex-wrap:wrap; }
.live-light { display:flex; align-items:center; gap:4px; }
.crop-rect .h { position:absolute; width:12px; height:12px; background:var(--primary-color); border:2px solid #fff; border-radius:50%; }
.crop-rect .tl { left:-7px; top:-7px; } .crop-rect .tr { right:-7px; top:-7px; } .crop-rect .bl { left:-7px; bottom:-7px; } .crop-rect .br { right:-7px; bottom:-7px; }
.crop-rect { position:absolute; border:2px solid var(--primary-color); box-shadow:0 0 0 9999px rgba(0,0,0,.45); border-radius:2px; pointer-events:none; }
textarea { font:inherit; color:var(--primary-text-color); background:var(--input-fill-color, var(--secondary-background-color, #f5f5f5)); border:1px solid var(--divider-color, #ccc); border-radius:8px; padding:8px 10px; width:100%; resize:vertical; }
textarea:focus { outline:2px solid var(--primary-color); outline-offset:-1px; }
textarea.prompt-edit { font-family:var(--code-font-family, monospace); font-size:13px; }
.prompt-body .desc { margin-top:8px; }
pre.prompt { white-space:pre-wrap; font-size:13px; background:var(--secondary-background-color, #f5f5f5); border-radius:8px; padding:10px; margin:8px 0 0; }
th.c-reading { width:150px; }
@media (max-width: 700px) {
  .meter-body, .edit-top { grid-template-columns:1fr; }
  th.c-reading { width:100px; }
}
`;

if (!customElements.get("zaehler-ablesung-panel")) {
  customElements.define("zaehler-ablesung-panel", ZaehlerAblesungPanel);
}
