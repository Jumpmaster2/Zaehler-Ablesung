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
    previewLast: "Letztes Bild der Ablesung",
    previewHint: "Testbild nimmt ein Bild mit den gespeicherten Einstellungen auf. Erst speichern, dann ausprobieren.",
    prompt: "Anweisung an die KI anzeigen",
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
    previewLast: "Last picture of a reading",
    previewHint: "Test picture takes a picture with the saved settings. Save first, then try it.",
    prompt: "Show the instructions for the AI",
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
const COLLAPSED = new Set(["checks_section"]);

const esc = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const clone = (value) => JSON.parse(JSON.stringify(value ?? null));
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
      <div class="toast" hidden></div>`;
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
      <div class="actions small-actions"><button class="btn flat" data-edit="${esc(meter.id)}"><ha-icon icon="mdi:pencil-outline"></ha-icon>${esc(ui.edit)}</button></div>
    </div>`;
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
  }

  _editor() {
    const ui = this.ui;
    const e = this._edit;
    const title = e.id ? e.title || e.originalTitle : ui.newMeter;
    const typeSpec = { selector: "select", options: this._cfg.meter_types, translation_key: "types" };
    const groups = this._cfg.meter_sections
      .map(({ id, fields }) => {
        const [name, desc] = this.labels.sections[id] || [id, ""];
        const html = Object.entries(fields).map(([key, spec]) => this._field("edit", key, spec, e.data[key])).join("");
        const body = `${desc ? `<p class="desc">${esc(desc)}</p>` : ""}<div class="fields">${html}</div>`;
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
      <details class="prompt-box" ${e.prompt ? "open" : ""} data-action="prompt"><summary>${esc(ui.prompt)}</summary><pre class="prompt">${esc(e.prompt || "…")}</pre></details>
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
      this._edit = { id: meter.id, title: meter.title, originalTitle: meter.title, data: clone(meter.data), open: new Set(), prompt: null };
    } else {
      const type = "heat";
      this._edit = { id: null, title: "", data: { ...clone(this._cfg.type_defaults[type]) }, open: new Set(), prompt: null };
    }
  }

  async _showPrompt(details) {
    if (!details.open || this._edit.prompt) return;
    try {
      const result = await this._ws({ type: `${DOMAIN}/prompt`, data: { ...this._edit.data } });
      this._edit.prompt = result.instructions;
      const pre = details.querySelector(".prompt");
      if (pre) pre.textContent = result.instructions;
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
    const el = ev.target.closest("button, img[data-action], [data-edit], [data-tab]");
    if (!el || el.disabled) return;
    const d = el.dataset;
    if (d.tab) {
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
      case "close-edit":
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
    button.disabled = true;
    try {
      this._cfg = await this._ws({ type: `${DOMAIN}/set_reading`, subentry_id: meterId, value });
      input.blur();
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
      this._edit = null;
      this._render();
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
.entity-hint.bad, .chip.bad, .msg.bad { color:var(--error-color, #db4437); }
.toggle-row { flex-direction:row; align-items:center; justify-content:space-between; gap:12px; cursor:pointer; }
.toggle-row > span:first-child { display:flex; flex-direction:column; gap:2px; }
.switch-input { display:none; }
.switch { position:relative; flex:none; width:36px; height:20px; border-radius:10px; background:var(--switch-unchecked-track-color, #9e9e9e); transition:background .2s; }
.switch::after { content:""; position:absolute; top:2px; left:2px; width:16px; height:16px; border-radius:50%; background:#fff; transition:left .2s; }
.switch.on { background:var(--switch-checked-track-color, var(--primary-color)); }
.switch.on::after { left:18px; }
.chips { display:flex; flex-wrap:wrap; gap:6px; }
.chip { max-width:100%; overflow-wrap:anywhere; display:inline-flex; align-items:center; gap:4px; background:var(--secondary-background-color, #eee); border-radius:16px; padding:3px 4px 3px 10px; font-size:13px; }
.chip-btn { border:none; background:none; cursor:pointer; color:var(--secondary-text-color); padding:0 4px; font-size:12px; }
.actions { display:flex; align-items:center; justify-content:flex-end; gap:8px; margin-top:16px; flex-wrap:wrap; }
.msg { margin-right:auto; font-size:13px; color:var(--secondary-text-color); }
.grow { flex:1; }
.btn { display:inline-flex; align-items:center; gap:6px; font:inherit; font-weight:500; border-radius:18px; padding:8px 16px; cursor:pointer; border:1px solid var(--divider-color); background:none; color:var(--primary-color); }
.btn ha-icon { --mdc-icon-size:18px; }
.btn.primary { background:var(--primary-color); color:var(--text-primary-color, #fff); border-color:var(--primary-color); }
.btn.danger { color:var(--error-color, #db4437); border-color:var(--error-color, #db4437); }
.btn:disabled { opacity:.45; cursor:default; }
.icon-btn { background:none; border:none; color:inherit; cursor:pointer; padding:4px; display:inline-flex; }
.status { display:flex; flex-direction:column; gap:16px; }
.status-main { display:flex; align-items:center; gap:16px; }
.status-main ha-icon { --mdc-icon-size:56px; flex:none; }
.status-text { font-size:22px; font-weight:500; margin-bottom:2px; }
.segments { display:flex; flex-wrap:wrap; gap:6px; margin-top:6px; }
.segment { border:1px solid var(--divider-color); background:none; color:var(--primary-text-color); border-radius:16px; padding:6px 12px; cursor:pointer; font:inherit; font-size:14px; }
.segment.on { background:var(--primary-color); color:var(--text-primary-color, #fff); border-color:var(--primary-color); }
.segment:disabled { opacity:.45; cursor:default; }
.tiles { display:grid; grid-template-columns:repeat(auto-fill, minmax(150px, 1fr)); gap:8px; margin:8px 0; }
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
.row > .meta { flex:0 1 auto; display:flex; flex-wrap:wrap; justify-content:flex-end; align-items:center; gap:4px 6px; }
.temp { white-space:nowrap; }
.row.link { cursor:pointer; }
.row.link:hover, tbody tr:hover { background:var(--secondary-background-color, #f5f5f5); }
.warn-row ha-icon { color:var(--warning-color, #ffa600); flex:none; }
.muted { color:var(--secondary-text-color); }
.small { font-size:12px; }
.show-narrow { display:none; }
.pill { flex:none; display:inline-block; border-radius:12px; padding:2px 10px; margin:1px 0; font-size:12px; background:var(--secondary-background-color, #eee); white-space:nowrap; }
.pill.ok { background:rgba(67,160,71,.15); color:var(--success-color, #2e7d32); }
.pill.warn { background:rgba(255,166,0,.18); color:var(--warning-color, #b26a00); }
.pill.bad { background:rgba(219,68,55,.15); color:var(--error-color, #db4437); }
.pill.muted { color:var(--secondary-text-color); }
.field > .pill { align-self:flex-start; }
.badge { display:inline-block; font-size:11px; border:1px solid var(--divider-color); border-radius:10px; padding:1px 8px; margin:4px 4px 0 0; color:var(--secondary-text-color); }
.table-wrap { width:100%; overflow-x:auto; }
table { width:100%; border-collapse:collapse; font-size:14px; table-layout:fixed; }
th.c-icon { width:40px; } th.c-state { width:150px; } th.c-edit { width:32px; }
td.c-name div { overflow-wrap:anywhere; }
td.c-name div:first-child { overflow-wrap:break-word; hyphens:auto; }
td.c-state .pill { margin-right:4px; }
th { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; text-align:left; font-weight:500; color:var(--secondary-text-color); padding:6px 8px; border-bottom:1px solid var(--divider-color); }
td { padding:8px; border-bottom:1px solid var(--divider-color); vertical-align:middle; }
tbody tr { cursor:pointer; }
.learn-cards { display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:12px; align-items:start; margin-bottom:12px; }
.card.learn { padding:12px 14px; }
.learn-head { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.learn-head h2 { margin:0; font-size:16px; }
.learn-head .pill ha-icon { --mdc-icon-size:14px; margin-right:4px; vertical-align:-2px; }
.learn-grid { display:grid; grid-template-columns:1fr 1fr; gap:6px 12px; margin-top:8px; }
.learn-cell { display:flex; flex-direction:column; min-width:0; font-size:14px; }
.learn-cell .lbl { font-weight:400; color:var(--secondary-text-color); display:flex; align-items:center; gap:4px; }
.learn-cell .lbl ha-icon { --mdc-icon-size:14px; color:var(--state-icon-color, var(--primary-color)); flex:none; }
.card.learn details { margin-top:8px; }
.card.learn summary { font-size:13px; }
details { margin-top:16px; }
summary { cursor:pointer; font-weight:500; color:var(--primary-color); }
details .desc { margin-top:8px; }
.toast { position:fixed; bottom:24px; left:50%; transform:translateX(-50%); background:var(--primary-text-color); color:var(--primary-background-color); padding:10px 18px; border-radius:8px; z-index:10; }
.toast.bad { background:var(--error-color, #db4437); color:#fff; }
@media (max-width: 700px) {
  .hide-narrow { display:none; } .show-narrow { display:inline; } .content { padding:8px; } .grid { grid-template-columns:1fr; }
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
.inline { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.inline .with-unit { flex:1; min-width:160px; }
.edit-top { display:grid; grid-template-columns:minmax(0, 1fr) minmax(0, 1fr); gap:20px; align-items:start; }
.edit-top .fields { grid-template-columns:1fr; }
.preview { display:flex; flex-direction:column; gap:6px; }
.preview .actions { margin-top:4px; }
.field.wide { grid-column:1 / -1; }
textarea { font:inherit; color:var(--primary-text-color); background:var(--input-fill-color, var(--secondary-background-color, #f5f5f5)); border:1px solid var(--divider-color, #ccc); border-radius:8px; padding:8px 10px; width:100%; resize:vertical; }
textarea:focus { outline:2px solid var(--primary-color); outline-offset:-1px; }
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
