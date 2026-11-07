// core.js already provides loadJSON(), showSpinner(), etc.
let ALL_DATA = {};  // KPI datasets loaded on demand


/* ========= Globals ========= */
let kpis = {}, countries = {}, groups = {}, fetchStatus = {};
let currentKpi = null, currentData = [], chartInstance = null;
let currentYearList = [];
let currentValueLookup = new Map();
let map = null, mapLayer = null;
let userSort = { col: null, asc: false };
let currentScale = { factor: 1, suffix: "", label: "Exact values" };
let sortingBound = false;
let sortedCountryNames = [];
let viewRequestId = 0;

function isKnownCountry(name) {
  if (!name) return false;
  if (Array.isArray(countries)) {
    return countries.some(entry => (entry?.name || entry?.country) === name);
  }
  if (countries && typeof countries === "object") {
    return Object.prototype.hasOwnProperty.call(countries, name);
  }
  return false;
}

const countryNameCollator = new Intl.Collator(undefined, { sensitivity: "base" });
const relationLookups = {
  percapita: new Map(),
  pergdp: new Map(),
  perkm2: new Map()
};

/* ========= Helpers ========= */
// chooseScaleFromValues, formatValueAuto und calcTrend kommen aus scripts/core.js
function formatWithScale(v) {
  return v == null || isNaN(v)
    ? "-"
    : (v / currentScale.factor).toFixed(2) +
        (currentScale.suffix ? " " + currentScale.suffix : "");
}
function getKpiArray() {
  return Array.isArray(kpis)
    ? kpis
    : kpis && typeof kpis === "object"
    ? Object.values(kpis)
    : [];
}

function relationKey(country, year) {
  return `${country}__${year}`;
}

function normalizeYear(year) {
  if (year == null) return null;
  const n = typeof year === "string" ? parseInt(year, 10) : year;
  return Number.isFinite(n) ? n : null;
}

function buildLookupMap(source) {
  const map = new Map();
  if (!Array.isArray(source)) return map;
  source.forEach(entry => {
    if (!entry || entry.value == null) return;
    const { country } = entry;
    const year = normalizeYear(entry.year);
    const numericValue = typeof entry.value === "string" ? parseFloat(entry.value) : entry.value;
    if (!country || !Number.isFinite(numericValue) || year == null) return;
    map.set(relationKey(country, year), numericValue);
  });
  return map;
}

async function ensureRelationData(relation) {
  const sourceByRelation = { percapita: "population", pergdp: "gdp", perkm2: "area" };
  const filename = sourceByRelation[relation];
  if (!filename || relationLookups[relation]?.size) return;
  const rows = await loadKPIData(filename);
  ALL_DATA[filename] = rows;
  relationLookups[relation] = buildLookupMap(rows);
}

function rebuildCurrentValueLookup(data) {
  currentYearList = [];
  currentValueLookup = new Map();
  if (!Array.isArray(data) || !data.length) return;

  const yearSet = new Set();

  data.forEach(entry => {
    if (!entry?.country) return;
    const year = normalizeYear(entry.year);
    if (year == null) return;
    yearSet.add(year);

    if (!currentValueLookup.has(entry.country)) {
      currentValueLookup.set(entry.country, new Map());
    }
    currentValueLookup.get(entry.country).set(year, entry);
  });

  currentYearList = Array.from(yearSet).sort((a, b) => a - b);
}

/* ========= Init ========= */
async function init() {
  try {
    await whenDocumentReady();

    if (!document.getElementById("kpiSelect")) {
      console.warn("RealityCheck: #kpiSelect not found -- skipping init.");
      return;
    }

    // === Daten laden ===
    showSpinner(true, "Loading data…"); // ✅ zentraler Loader aktivieren
	[
	  kpis,
	  countries,
	  groups,
	  fetchStatus
	] = await Promise.all([
	  loadJSON("data/meta/available_kpis.json"),
	  loadJSON("data/meta/countries.json"),
	  loadJSON("data/meta/groups.json"),
	  loadJSON("data/fetch_status.json")
	]);
	kpis = (Array.isArray(kpis) ? kpis : []).filter(kpi => kpi.publication_status !== "pending_first_fetch");
	
	    // 🔧 Root-Cause-Fix: Falls countries als String geladen wurde (Edge/Cache-Bug)
    if (typeof countries === "string") {
      try {
        const reparsed = JSON.parse(countries);
        countries = reparsed;
        console.log("🧩 RootFix: countries reparsed from string → object");
      } catch (err) {
        console.error("❌ RootFix: Failed to reparse countries.json", err);
      }
    }
    ALL_DATA = {};
        console.log(`✅ init(): loaded ${Object.keys(countries).length} countries, ${Object.keys(kpis).length} KPIs`);


    /* ---------- AUTO-FIX COUNTRIES STRUCTURE ---------- */
    if (Array.isArray(countries)) {
      console.log("🧭 Fixing countries.json structure (array → object)...");
      const fixed = {};
      for (const c of countries) {
        if (!c.name) continue;
        fixed[c.name] = c;
      }
      countries = fixed;
      console.log(`✅ Converted ${Object.keys(countries).length} countries to object map.`);
    }

    sortedCountryNames = Object.keys(countries || {}).sort((a, b) =>
      countryNameCollator.compare(a, b)
    );

    // === Dropdowns & Eventhandler ===
    await populateKpiSelect();
    populateHomeCountrySelect();
    populateCountrySelects();
    setupHomeCountryPreference();
    bindHeaderSorting();

    const el = id => document.getElementById(id);
    el("kpiSelect")?.addEventListener("change", () => {
      userSort = { col: null, asc: false };
      updateView();
    });
    el("yearSelect")?.addEventListener("change", updateTable);
    el("countrySnapshotYear")?.addEventListener("change", () => {
      updateTable();
      updateMap();
    });
    el("relationSelect")?.addEventListener("change", async () => {
      const relation = el("relationSelect").value;
      const status = el("view-status");
      if (relation !== "absolute" && !relationLookups[relation]?.size) {
        if (status) status.textContent = "Loading comparison basis…";
        await ensureRelationData(relation);
      }
      updateTable();
      updateChart();
      updateMap();
    });
    el("countrySelect")?.addEventListener("change", updateTable);
    ["country1Select", "country2Select", "country3Select"].forEach(id =>
      el(id)?.addEventListener("change", updateChart)
    );

    // === Initial KPI selection & chart setup ===
    if (sortedCountryNames.length > 0) {
      const country1Select = el("country1Select");
      if (country1Select && !country1Select.value) {
        country1Select.value = sortedCountryNames[0];
      }
    }

    // === Trigger initial view update ===
    if (el("kpiSelect") && el("kpiSelect").options.length > 1) {
      const requestedKpi = new URLSearchParams(location.search).get("kpi");
      const requestedOption = requestedKpi
        ? Array.from(el("kpiSelect").options).find(option => option.value === requestedKpi)
        : null;
      if (requestedOption) el("kpiSelect").value = requestedKpi;
      else el("kpiSelect").selectedIndex = 1;
      await updateView();
    }

  } catch (e) {
    console.error("RealityCheck init() failed:", e);
  } finally {
    // === Spinner IMMER ausschalten, egal ob Erfolg oder Fehler ===
    showSpinner(false);
  }
}

/* ========= KPI-Auswahl ========= */
async function populateKpiSelect() {
  const sel = document.getElementById("kpiSelect");
  sel.disabled = true;
  sel.innerHTML = "<option>Loading KPIs…</option>";

  const optgroups = [];

  try {
    const grouped = groupKpisByCluster(getKpiArray(), {
      filter: k => k.world_kpi !== "e" && k.geo_type !== "region",
      mapItem: meta => ({
        id: meta.filename,
        title: meta.title || meta.filename || "Unnamed KPI"
      })
    });

    sel.innerHTML = "<option value=''>-- none --</option>";

    grouped.forEach(([clusterName, list]) => {
      const g = document.createElement("optgroup");
      g.label = clusterName;

      list.forEach(item => {
        if (!item?.id) return;
        const o = document.createElement("option");
        o.value = item.id;
        o.textContent = item.title;

        if (
          fetchStatus?.kpis && !fetchStatus.kpis[item.id]
        ) {
          o.classList.add("option-no-data");
        }

        g.appendChild(o);
      });

      optgroups.push(g);
    });

    if (!optgroups.length) {
      sel.innerHTML = "<option value=''>No KPIs available</option>";
    } else {
      optgroups.forEach(g => sel.appendChild(g));
    }
  } catch (e) {
    console.error("populateKpiSelect() failed:", e);
    sel.innerHTML = "<option value=''>Failed to load KPIs</option>";
  } finally {
    sel.classList.remove("loading");
    sel.disabled = false;
  }

}

/* ========= Country Selects ========= */
function populateHomeCountrySelect() {
  const s = document.getElementById("countrySelect");
  if (!s) return;
  s.innerHTML = "<option value=''>-- none --</option>";
  const names = sortedCountryNames.length
    ? sortedCountryNames
    : Object.keys(countries || {}).sort((a, b) => countryNameCollator.compare(a, b));
  names.forEach(n => {
    const o = document.createElement("option");
    o.value = n;
    o.textContent = n;
    s.appendChild(o);
  });
}

function setupHomeCountryPreference() {
  const select = document.getElementById("countrySelect");
  const chart = document.getElementById("country1Select");
  const panel = document.getElementById("home-country-preference");
  const remember = document.getElementById("remember-home-country");
  const forget = document.getElementById("forget-home-country");
  const status = document.getElementById("home-country-storage-status");
  const key = "rc_home_country_v1";
  const lifetime = 90 * 24 * 60 * 60 * 1000;
  let savedCountry = "";

  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      let preference;
      try { preference = JSON.parse(raw); } catch { preference = null; }
      if (Number.isFinite(preference?.expiresAt) && preference.expiresAt > Date.now()) {
        savedCountry = sortedCountryNames.find(name => countries[name]?.iso_a2 === preference.code) || "";
      }
      if (!savedCountry) localStorage.removeItem(key);
    }
  } catch {
    // The dashboard still works when the browser blocks storage.
  }
  if (savedCountry) select.value = chart.value = savedCountry;

  const update = () => {
    panel.hidden = !select.value && !savedCountry;
    remember.hidden = !countries[select.value]?.iso_a2 || select.value === savedCountry;
    forget.hidden = !savedCountry;
  };
  select.addEventListener("change", () => {
    status.textContent = "";
    update();
  });
  remember.addEventListener("click", () => {
    const country = select.value;
    const code = countries[country]?.iso_a2;
    if (!code) return;
    try {
      localStorage.setItem(key, JSON.stringify({ code, expiresAt: Date.now() + lifetime }));
      savedCountry = country;
      status.textContent = "Home country saved in this browser.";
      update();
      forget.focus();
    } catch {
      status.textContent = "This browser could not save your home country.";
    }
  });
  forget.addEventListener("click", () => {
    try {
      localStorage.removeItem(key);
      savedCountry = "";
      update();
      select.focus();
      status.textContent = "Saved home country removed.";
    } catch {
      status.textContent = "This browser could not remove the saved home country.";
    }
  });
  update();
}

function populateCountrySelects() {
  const ids = ["country1Select", "country2Select", "country3Select"];
  const names = sortedCountryNames.length
    ? sortedCountryNames
    : Object.keys(countries || {}).sort((a, b) => countryNameCollator.compare(a, b));
  ids.forEach(id => {
    const s = document.getElementById(id);
    if (!s) return;
    s.innerHTML = "<option value=''>-- none --</option>";
    names.forEach(n => {
      const o = document.createElement("option");
      o.value = n;
      o.textContent = n;
      s.appendChild(o);
    });
  });
}
// ============================================================
// 🧭 RealityCheck Enhancement: Home Country → Chart Preselect
// ============================================================

let userOverrodeChart1 = false;

function syncHomeToChart() {
  const home = document.getElementById('countrySelect')?.value;
  const c1   = document.getElementById('country1Select');
  if (!home || !c1) return;

  // Nur setzen, wenn der User #country1Select noch nicht manuell geändert hat
  if (!userOverrodeChart1 || !c1.value) {
    const opt = [...c1.options].find(o => o.value === home);
    if (opt) c1.value = home;

    // Optional sofort aktualisieren
    if (typeof updateChart === 'function') updateChart();
  }
}

// Wenn der User manuell das Vergleichsland ändert → nicht mehr automatisch überschreiben
document.addEventListener('change', e => {
  if (e.target?.id === 'country1Select') userOverrodeChart1 = true;
});

// Wenn das Home Country geändert wird → ggf. übernehmen
document.addEventListener('change', e => {
  if (e.target?.id === 'countrySelect') {
    userOverrodeChart1 = false; // neue Home-Wahl darf wieder gespiegelt werden
    syncHomeToChart();
  }
});

// Beim Init einmalig spiegeln (nachdem alle Dropdowns gefüllt sind)
setTimeout(syncHomeToChart, 0);

/* ========= Relation ========= */
const relationUnits = { percapita: "people", pergdp: "USD GDP", perkm2: "km²" };
const relationMultipliers = [
  [1, ""], [1e3, "thousand"], [1e6, "million"],
  [1e9, "billion"], [1e12, "trillion"]
];

function activeRelation(meta) {
  const relation = document.getElementById("relationSelect")?.value;
  return meta?.relation === "*" && Object.hasOwn(relationUnits, relation) ? relation : null;
}

function relationDivisor(relation, country, year) {
  return relationLookups[relation]?.get(relationKey(country, normalizeYear(year)));
}

function relationRatio(value, relation, country, year) {
  const divisor = relationDivisor(relation, country, year);
  return Number.isFinite(value) && Number.isFinite(divisor) && divisor > 0 ? value / divisor : null;
}

function relationDisplay(meta) {
  const relation = activeRelation(meta);
  if (!relation) return { relation, factor: 1, unit: (meta.unit || "").trim() };

  const magnitudes = [];
  for (const [country, observations] of currentValueLookup) {
    if (!isKnownCountry(country)) continue;
    for (const record of observations.values()) {
      const ratio = relationRatio(record.value, relation, country, record.year);
      if (ratio) magnitudes.push(Math.abs(ratio));
    }
  }
  magnitudes.sort((a, b) => a - b);
  const median = magnitudes[Math.floor(magnitudes.length / 2)];
  const [factor, prefix] = relationMultipliers.find(([factor]) => median * factor >= 0.1)
    || relationMultipliers[median ? relationMultipliers.length - 1 : 0];
  const basis = prefix ? `1 ${prefix} ` : "";
  return { relation, factor, unit: [meta.unit, `per ${basis}${relationUnits[relation]}`].filter(Boolean).join(" ") };
}

function applyRelation(value, country, year, display) {
  if (!display.relation) return value;
  const ratio = relationRatio(value, display.relation, country, year);
  return ratio === null ? null : ratio * display.factor;
}

function formatRelationValue(value) {
  if (!Number.isFinite(value)) return "–";
  if (value !== 0 && Math.abs(value) < 0.01) return Number(value.toPrecision(2)).toLocaleString("en", { maximumSignificantDigits: 2 });
  return value.toFixed(2);
}

function aggregateRelation(rows) {
  const valid = rows.filter(row => Number.isFinite(row.value) && row.relationWeight > 0);
  if (!valid.length) return null;
  return valid.reduce((sum, row) => sum + row.value * row.relationWeight, 0)
    / valid.reduce((sum, row) => sum + row.relationWeight, 0);
}

/* ========= View ========= */
function getMetaForCurrent() {
  const arr = getKpiArray();
  if (!currentKpi) return null;
  return arr.find(m => (m.filename || m.id || m.title) === currentKpi) || null;
}
/* ========= Adaptive Scaling (medianbasiert) ========= */
function determineAdaptiveScale(values) {
  const nums = values.filter(v => typeof v === "number" && !isNaN(v));
  if (!nums.length) return { divisor: 1, suffix: "" };

  const sorted = [...nums].sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)];
  const magnitude = Math.max(Math.abs(median), 1);

  if (magnitude >= 1e12) return { divisor: 1e12, suffix: "T" };
  if (magnitude >= 1e9)  return { divisor: 1e9, suffix: "B" };
  if (magnitude >= 1e6)  return { divisor: 1e6, suffix: "M" };
  if (magnitude >= 1e3)  return { divisor: 1e3, suffix: "K" };
  return { divisor: 1, suffix: "" };
}

/* ========= Sorting Header Binding ========= */
function bindHeaderSorting() {
  if (sortingBound) return;
  const thead = document.querySelector("#country-table thead");
  if (!thead) return;

  const sortableHeaders = thead.querySelectorAll("th[data-col]");
  sortableHeaders.forEach(th => {
    th.tabIndex = 0;
    th.setAttribute("role", "button");
    th.setAttribute("aria-sort", "none");
  });

  const sortFromEvent = event => {
    const th = event.target.closest("th[data-col]");
    if (!th) return;
    const col = th.dataset.col;
    if (!col) return;
    if (userSort.col === col) userSort.asc = !userSort.asc;
    else userSort = { col, asc: col === "country" || col === "rank" };
    sortableHeaders.forEach(header => header.setAttribute("aria-sort", "none"));
    th.setAttribute("aria-sort", userSort.asc ? "ascending" : "descending");
    updateTable();
  };

  thead.addEventListener("click", sortFromEvent);
  thead.addEventListener("keydown", event => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    sortFromEvent(event);
  });

  sortingBound = true;
}

/* ========= Year Select (Comparison) ========= */
function populateYearSelect() {
  const sel = document.getElementById("yearSelect");
  if (!sel) return;

  const display = relationDisplay(meta);
  const years = currentYearList.length
    ? [...currentYearList].sort((a, b) => b - a)
    : [];

  // Vorherige Auswahl merken (falls z.B. beim KPI-Wechsel vorhanden)
  const prev = sel.value;

  // Always prepend "-- none --", dann die Jahre
  sel.innerHTML = [
    `<option value="">-- none --</option>`,
    ...years.map(y => `<option value="${y}">${y}</option>`)
  ].join("");

  // Falls vorher ein Jahr gewählt war und es noch existiert → beibehalten, sonst auf none
  if (prev !== "" && years.includes(parseInt(prev))) {
    sel.value = prev;
  } else {
    sel.value = "";
  }
}

function populateCountrySnapshot(meta) {
  const control = document.getElementById("country-snapshot-control");
  const select = document.getElementById("countrySnapshotYear");
  if (!control || !select) return;
  select.replaceChildren();
  control.hidden = !meta.common_year_view;
  if (control.hidden) return;

  const counts = new Map();
  for (const [country, observations] of currentValueLookup) {
    if (!isKnownCountry(country)) continue;
    for (const [year, observation] of observations) {
      if (Number.isFinite(observation.value)) counts.set(year, (counts.get(year) || 0) + 1);
    }
  }
  const years = [...counts.keys()].sort((a, b) => b - a);
  const threshold = sortedCountryNames.length / 2;
  const preferred = years.find(year => counts.get(year) >= threshold);
  for (const year of years) {
    const count = counts.get(year);
    select.add(new Option(`${year} · ${count} ${count === 1 ? "country" : "countries"}`, String(year)));
  }
  select.add(new Option("Latest value per country", ""));
  select.value = String(preferred ?? years[0] ?? "");
}

function countrySnapshotYear(meta) {
  const selected = meta.common_year_view && document.getElementById("countrySnapshotYear")?.value;
  return selected ? Number(selected) : null;
}

/* ========= Table ========= */
function updateTable() {
  const tbody = document.querySelector("#country-table tbody");
  if (!tbody || !currentKpi) return;
  tbody.innerHTML = "";

  const compYearEl = document.getElementById("yearSelect");
  const compYear =
    compYearEl && compYearEl.value !== ""
      ? parseInt(compYearEl.value)
      : null;

  const meta = getMetaForCurrent() || {};
  const snapshotYear = countrySnapshotYear(meta);
  const display = relationDisplay(meta);
  const unit = display.unit;
  const formatDelta = value => display.relation ? formatRelationValue(value) : formatValueAuto(value, meta.scale);
  const changeUnit = unit === "%" ? "percentage points" : unit;
  const scaleMode = meta.scale || "auto";

  /* ===========================================
     1) Länder normal berechnen
     =========================================== */
  const rows = [];
  const grouped = new Map();

  currentData.forEach(entry => {
    if (!entry || !entry.country) return;
    const country = entry.country;
    const year = normalizeYear(entry.year);
    if (year == null) return;
    if (!isKnownCountry(country)) return;

    let bucket = grouped.get(country);
    if (!bucket) {
      bucket = { latest: null, byYear: new Map() };
      grouped.set(country, bucket);
    }

    const normalizedEntry = { ...entry, year };
    bucket.byYear.set(year, normalizedEntry);
    if (!bucket.latest || year > bucket.latest.year) {
      bucket.latest = normalizedEntry;
    }
  });

  grouped.forEach((bucket, country) => {
    const latest = snapshotYear === null ? bucket.latest : bucket.byYear.get(snapshotYear);
    if (!latest) return;
    const prev = bucket.byYear.get(latest.year - 1) || null;
    const comp =
      compYear != null && bucket.byYear.has(compYear)
        ? bucket.byYear.get(compYear)
        : null;

    const lv = applyRelation(latest.value, country, latest.year, display);
    const pv = prev ? applyRelation(prev.value, country, prev.year, display) : null;
    const cv = comp ? applyRelation(comp.value, country, comp.year, display) : null;

    const arrow = pv != null && lv != null ? calcTrend(lv, pv) : "→";
    const dAbs = pv != null && lv != null ? lv - pv : null;
    const dPct = meta.change_mode !== "absolute" && pv != null && pv !== 0 && lv != null ? ((lv - pv) / pv) * 100 : null;
    const dComp =
      cv != null && lv != null
        ? meta.change_mode === "absolute" ? `${formatDelta(lv - cv)} ${changeUnit}`
          : cv !== 0 ? (((lv - cv) / cv) * 100).toFixed(2) + "%" : "-"
        : "-";

    rows.push({
      country,
      value: lv,
      relationWeight: relationDivisor(display.relation, country, latest.year),
      deltaPrevArrow: arrow,
      deltaPrevAbs: dAbs,
      deltaPrevPct: dPct,
      deltaComp: dComp,
      update: latest.year,
      isGroup: false
    });
  });

  /* ===========================================
     2) Adaptive Skalierung bestimmen
     =========================================== */
  let scaleInfo = { divisor: 1, suffix: "" };
  if (meta.scale === "auto") {
    const allValues = rows.map(r => r.value).filter(v => !isNaN(v));
    scaleInfo = determineAdaptiveScale(allValues);
  }

  /* ========= WORLD CALCULATION (ALWAYS GENERATED) ========= */
  (function generateWorld() {
    if (!rows.length) return;

    const isRelative =
      (meta.unit || "").includes("%") ||
      ["index", "ratio", "none"].includes(meta.scale);

    const valid = rows.filter(r => Number.isFinite(r.value));
    if (!valid.length) return;

    const val = display.relation ? aggregateRelation(valid) : isRelative
      ? valid.reduce((a, r) => a + (r.value || 0), 0) / valid.length
      : valid.reduce((a, r) => a + (r.value || 0), 0);

    const lastYear = Math.max(...valid.map(r => r.update));

    // World wird wie ein echtes Land in rows eingefügt
    rows.push({
      country: "World",
      value: val,
      deltaPrevArrow: "-",
      deltaPrevAbs: null,
      deltaPrevPct: null,
      deltaComp: "-",
      update: lastYear,
      isGroup: false,
      isWorld: true,
      aggregationType: display.relation ? "weighted average" : isRelative ? "average" : "sum"
    });
  })();


  /* ===========================================
     3) Gruppen inkl. World berechnen
     =========================================== */
  const groupRows = [];

  for (const [gKey, gDef] of Object.entries(groups)) {
    const members = gDef.members || [];
    const title = gDef.title || gKey;

    const isRelative =
      (meta.unit || "").includes("%") ||
      ["index", "ratio", "none"].includes(meta.scale);

    /* ---------- SPEZIALFALL: WORLD ---------- */
    if (gKey === "World" || gKey === "Welt") {
      const valid = rows.filter(
        r => !r.isGroup && Number.isFinite(r.value)
      );
      if (!valid.length) continue;

      const val = display.relation ? aggregateRelation(valid) : isRelative
        ? valid.reduce((a, r) => a + (r.value || 0), 0) / valid.length
        : valid.reduce((a, r) => a + (r.value || 0), 0);

      const lastYear = Math.max(...valid.map(r => r.update));

      groupRows.push({
        country: "World",
        value: val,
        deltaPrevArrow: "-",
        deltaPrevAbs: null,
        deltaPrevPct: null,
        deltaComp: "-",
        update: lastYear,
        isGroup: false, // WICHTIG → Verhalten wie Land
        isWorld: true,  // Flag für spätere Formatierung
        aggregationType: display.relation ? "weighted average" : isRelative ? "average" : "sum"
      });

      continue;
    }

    /* ---------- Normale Gruppen ---------- */
    const mrows = rows.filter(r => members.includes(r.country));
    if (!mrows.length) continue;

    const agg = display.relation ? aggregateRelation(mrows) : isRelative
      ? mrows.reduce((a, r) => a + (r.value || 0), 0) / mrows.length
      : mrows.reduce((a, r) => a + (r.value || 0), 0);

    const lastYear = Math.max(...mrows.map(r => r.update));

    groupRows.push({
      country: title,
      value: agg,
      deltaPrevArrow: "-",
      deltaPrevAbs: null,
      deltaPrevPct: null,
      deltaComp: "-",
      update: lastYear,
      isGroup: true,
      aggregationType: display.relation ? "weighted average" : isRelative ? "average" : "sum"
    });
  }

  /* ===========================================
     4) Sortierung
     =========================================== */
  let sortedRows = [...rows];
  const sortType = (meta.sort || "higher").toLowerCase();
  const targetVal = parseFloat(meta.target_value || 0);

  if (userSort.col && userSort.col !== "rank") {
    const { col, asc } = userSort;
    sortedRows.sort((a, b) => {
      const A = a[col] ?? 0,
        B = b[col] ?? 0;
      if (A === B) return 0;
      return asc ? (A > B ? 1 : -1) : (A < B ? 1 : -1);
    });
  } else {
    if (sortType === "higher")
      sortedRows.sort((a, b) => (b.value || 0) - (a.value || 0));
    else if (sortType === "lower")
      sortedRows.sort((a, b) => (a.value || 0) - (b.value || 0));
    else if (sortType === "target") {
      sortedRows.sort((a, b) => {
        const devA = Math.abs((a.value ?? 0) - targetVal);
        const devB = Math.abs((b.value ?? 0) - targetVal);
        return devA - devB;
      });
    } else {
      sortedRows.sort((a, b) => (b.value || 0) - (a.value || 0));
    }
  }

  /* ===========================================
     5) Rangvergabe
     =========================================== */
  const rankMap = new Map();
  let rankCounter = 0;

  sortedRows.forEach(r => {
    if (["World", "Welt"].includes(r.country)) {
      rankMap.set(r.country, "🌍"); // World-Badge
    } else {
      rankCounter++;
      rankMap.set(r.country, rankCounter);
    }
  });

  /* ===========================================
     6) Länder + Gruppen kombinieren
     =========================================== */
  const final = [
    ...sortedRows.map(r => ({
      ...r,
      rank: rankMap.get(r.country)
    })),
    ...groupRows.map(r => ({
      ...r,
      rank: "–"
    }))
  ];

  /* ===========================================
     7) Home Country nach oben
     =========================================== */
  const home = document.getElementById("countrySelect")?.value;
  if (home) {
    const i = final.findIndex(r => r.country === home);
    if (i !== -1) {
      const hc = { ...final[i], highlight: true };
      final.splice(i, 1);
      final.unshift(hc);
    }
  }

  /* ===========================================
     8) Rendering der Tabelle
     =========================================== */
  final.forEach(r => {
    const tr = document.createElement("tr");

    if (r.highlight) tr.classList.add("highlight");
    if (r.isGroup) tr.classList.add("group-row");
    if (r.isWorld) tr.classList.add("world-row");

    if (r.isGroup) {
      tr.title = `Group value = ${
        r.aggregationType
      } of members`;
    }

    tr.addEventListener("click", () => {
      if (!r.isGroup) highlightOnMap(r.country);
    });

    const deltaValue = r.deltaPrevAbs != null ? formatDelta(r.deltaPrevAbs) : "";
    const deltaDetail = meta.change_mode === "absolute"
      ? `${deltaValue} ${changeUnit}`
      : `${deltaValue} (${r.deltaPrevPct != null ? r.deltaPrevPct.toFixed(2) + "%" : "n/a"})`;
    const deltaTitle = r.deltaPrevAbs != null
      ? `title="${escapeHtml(`Δ vs Prev: ${deltaDetail}`)}"`
      : `title="No previous year data"`;

    tr.innerHTML = `
      <td>${r.rank ?? ""}</td>
      <td>${r.country}</td>
      <td>${
        display.relation ? formatRelationValue(r.value) : meta.scale === "auto"
          ? (r.value / scaleInfo.divisor).toFixed(2) +
            " " +
            scaleInfo.suffix
          : formatValueAuto(r.value, meta.scale)
      }${unit ? " " + unit : ""}</td>
      <td class="trend" ${deltaTitle}>${r.deltaPrevArrow}</td>
      <td>${r.deltaComp ?? "-"}</td>
      <td>${r.update ?? "-"}</td>
    `;

    tbody.appendChild(tr);
  });

  /* ===========================================
     9) Header-Pfeile aktualisieren
     =========================================== */
  document
    .querySelectorAll("#country-table th[data-col]")
    .forEach(th => {
      const col = th.dataset.col;
      const label = th.textContent.replace(/[▲▼]/g, "").trim();
      th.textContent = label;
      th.classList.remove("active-col");
      if (userSort.col === col) {
        th.textContent = label + (userSort.asc ? " ▲" : " ▼");
        th.classList.add("active-col");
      }
    });

  /* ===========================================
     10) Sortierspalte kurz highlighten
     =========================================== */
  const activeCol = userSort.col;
  if (activeCol) {
    const colIndex = { rank: 0, country: 1, value: 2 }[activeCol];
    if (colIndex !== undefined) {
      tbody.querySelectorAll("tr").forEach(tr => {
        const cell = tr.children[colIndex];
        if (cell) {
          cell.classList.add("table-highlight");
          setTimeout(() => cell.classList.remove("table-highlight"), 300);
        }
      });
    }
  }

  /* ===========================================
     11) Legendenhinweis (Scaling)
     =========================================== */
  const roundInfo = document.getElementById("rounding-info");
  const changeNote = document.getElementById("comparison-change-note");
  if (changeNote) changeNote.textContent = meta.change_mode === "absolute"
    ? `Changes are shown in ${changeUnit || "indicator units"}.`
    : "Δ vs Comparison Year in %";
  if (roundInfo) {
    if (display.relation) {
      roundInfo.textContent = `Values shown in ${unit}. Group rates are weighted by the selected basis.`;
    } else if (scaleMode === "auto") {
      let explain =
        "Values are auto-scaled using median-based factor (K, M, B, T).";
      roundInfo.textContent = explain;
      if (scaleInfo && scaleInfo.suffix)
        roundInfo.textContent += ` (All values in ${scaleInfo.suffix})`;
    } else if (scaleMode === "none") {
      roundInfo.textContent = "Values shown as-is (no scaling).";
    } else if (scaleMode === "%") {
      roundInfo.textContent = "Values shown as percentage.";
    } else {
      roundInfo.textContent = `Values displayed in ${scaleMode}.`;
    }
  }
}


/* ========= Chart ========= */
function updateChart() {
  const ctxEl = document.getElementById("kpi-chart");
  if (!ctxEl) return;

  const meta = getMetaForCurrent() || { title: currentKpi || "Selected KPI", unit: "" };
  const years = currentYearList.length ? [...currentYearList] : [];
  const coverage = document.getElementById("data-coverage");
  if (coverage) {
    const countrySeries = [...currentValueLookup].filter(([country]) => isKnownCountry(country));
    coverage.textContent = " · No country data for this view";
    for (let index = years.length - 1; index >= 0; index--) {
      const year = years[index];
      const count = countrySeries.filter(([country, observations]) =>
        Number.isFinite(applyRelation(observations.get(year)?.value, country, year, display))
      ).length;
      if (!count) continue;
      coverage.textContent = ` · Latest country data: ${year} · ${count} ${count === 1 ? "country" : "countries"} in that year`;
      break;
    }
  }

  const datasets = [];
  const compareSelectIds = ["country1Select", "country2Select", "country3Select"];
  compareSelectIds.forEach((id, idx) => {
    const sel = document.getElementById(id);
    if (!sel || !sel.value) return;
    const country = sel.value;
    const countryLookup = currentValueLookup.get(country);
    const vals = years.map(year => {
      const record = countryLookup?.get(year);
      return record ? applyRelation(record.value, country, record.year, display) : null;
    });
    datasets.push({
      label: country,
      data: vals,
      borderWidth: 2,
      borderColor: getColorForCountry(country, idx),
      backgroundColor: getColorForCountry(country, idx),
      pointBackgroundColor: getColorForCountry(country, idx),
      pointRadius: 3,
      pointHoverRadius: 5,
      fill: false,
      tension: 0.25
    });
  });

  const fallbackLabels = years.length ? years : [0, 1, 2];

  chartInstance = renderLineChart(ctxEl, {
    labels: years,
    datasets,
    title: meta.title || "No data selected",
    unit: display.unit,
    formatValue: display.relation ? formatRelationValue : undefined,
    existingChart: chartInstance,
    fallbackDataset: {
      label: "Select countries to display data",
      data: fallbackLabels.map(() => null),
      borderColor: "rgba(200,200,200,0.3)",
      borderWidth: 1,
      fill: false
    },
    options: {
      maintainAspectRatio: false,
      aspectRatio: 2,
      layout: {
        padding: { top: 20, bottom: 10, left: 10, right: 10 }
      },
      scales: {
        y: {
          beginAtZero: true,
          ...(display.relation ? { ticks: { callback: formatRelationValue } } : {}),
          grid: { color: "rgba(255,255,255,0.05)" }
        },
        x: {
          grid: { color: "rgba(255,255,255,0.05)" }
        }
      }
    }
  });
}

/* ========= Hilfsfunktion: Farbzuteilung ========= */
function getColorForCountry(name, compareIndex = null) {
  const comparePalette = ["#1a355e", "#4ea64f", "#d94f4f"];
  if (typeof compareIndex === "number" && compareIndex >= 0 && compareIndex < comparePalette.length) {
    return comparePalette[compareIndex];
  }
  const palette = [
    "#1a355e", "#d94f4f", "#4ea64f", "#e5a22f", "#7c4eea", "#49b9cc"
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash % palette.length);
  return palette[index];
}


/* ========= Compatibility: updateView() ========= */
async function updateView() {
  const requestId = ++viewRequestId;
  const status = document.getElementById("view-status");
  try {
    const sel = document.getElementById("kpiSelect");
    currentKpi = sel?.value || currentKpi;

    const meta = getMetaForCurrent();
    if (!meta) {
      console.warn("⚠️ No meta found for current KPI:", currentKpi);
      return;
    }
	
	updateRelationAvailability(meta);

    const filename = meta.filename || meta.id || meta.title;

      document.getElementById("controls")?.setAttribute("aria-busy", "true");
      if (status) status.textContent = `Loading ${meta.title || filename}…`;
      const loadedData = ALL_DATA[filename] || await loadKPIData(filename);
      if (requestId !== viewRequestId) return;
      ALL_DATA[filename] = Array.isArray(loadedData) ? loadedData : [];
      currentData = ALL_DATA[filename];
      rebuildCurrentValueLookup(currentData);

      console.log(`✅ updateView(): ${filename} → ${currentData.length} records`);

      populateYearSelect();
      populateCountrySnapshot(meta);
      updateTable();
      updateChart();
      updateMap();

      const url = new URL(location.href);
      url.searchParams.set("kpi", filename);
      history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
      if (status) status.textContent = `${meta.title || filename}: ${currentData.length.toLocaleString()} observations loaded.`;

      // 🔹 KPI-Beschreibung
      const descEl = document.getElementById("kpi-description");
      if (descEl) descEl.textContent = meta.description || "";
	  
	  // 🧠 Ergänze Smart KPI Analysis
	  // 🧠 Ergänze Smart KPI Analysis (aus core.js)
	  renderKpiAnalysis(meta);



      // 🔹 Quelle & Datum
      const sourceLink = document.getElementById("data-source");
      const dateEl = document.getElementById("data-date");

      // ✅ Quelle (Domain)
      if (sourceLink) {
        if (meta.source && meta.source.startsWith("http")) {
          sourceLink.href = meta.source;
          sourceLink.textContent = new URL(meta.source).hostname.replace("www.", "");
        } else {
          sourceLink.removeAttribute("href");
          sourceLink.textContent = meta.source || "---";
        }
      }

      // ✅ Datum (korrekt aus fetch_status.json)
      if (dateEl) {
        const kpiStatus = fetchStatus?.kpis?.[filename] || {};
        const date =
          kpiStatus.last_fetch ||
          kpiStatus.last_update ||
          meta.last_fetch ||
          meta.last_update ||
          "---";
        const checkedAt = new Date(date);
        dateEl.textContent = Number.isFinite(checkedAt.getTime())
          ? checkedAt.toISOString().split("T")[0]
          : "—";
      }
  } catch (e) {
    console.error("❌ updateView() failed:", e);
    if (requestId === viewRequestId && status) status.textContent = "The selected indicator could not be loaded. Please try again.";
  } finally {
    if (requestId === viewRequestId) document.getElementById("controls")?.setAttribute("aria-busy", "false");
  }
}

/* ========= Relation Select Activation ========= */
function updateRelationAvailability(meta) {
  const relSelect = document.getElementById("relationSelect");
  if (!relSelect) return;

  // Wenn das KPI keine Relation erlaubt → absolute fixieren & ausgrauen
  if (!meta.relation || meta.relation.trim() === "" || meta.relation === "-") {
    relSelect.value = "absolute";
    relSelect.disabled = true;
  } else {
    relSelect.disabled = false;
  }
}

/* ========= MAP INITIALIZATION (ISO-based RealityCheck Version) ========= */
async function initMap() {
  const el = document.getElementById("map");
  if (!el) return;

  // 🌍 Create map using shared library
  map = window.RCMap.createMap("map", { scrollWheelZoom: false });
  map.setView([20, 0], 2);
  
  // ✅ Allow Drag & Keyboard navigation, but allow page scrolling via mousewheel
  // scrollWheelZoom is already false from createMap options

  // 📦 Load shared GeoJSON
  window._worldGeoJSON = await window.RCMap.loadGeoJSON();
  
  // 🗺️ Always show basic country outlines
  if (window._worldGeoJSON) {
    const basicLayer = L.geoJSON(window._worldGeoJSON, {
      style: () => ({
        fillColor: '#e0e0e0',
        weight: 1,
        opacity: 1,
        color: '#999',
        fillOpacity: 0.7
      })
    }).addTo(map);
    
    // Store as initial layer
    mapLayer = basicLayer;
  }
  
  // 🎨 Update with KPI data if available
  if (currentKpi) {
    await updateMap();
  }
}

/* ========= KPI HEATMAP COLORING (ISO-BASED, BALANCED + OUTLIER-CONTROL, 2025-11-10 FINAL) ========= */
async function updateMap() {
  if (!map || !currentKpi || !window._worldGeoJSON) return;

  const meta = getMetaForCurrent();
  if (!meta) return;

  const data = ALL_DATA[meta.filename] || [];
  const snapshotYear = countrySnapshotYear(meta);
  if (!data.length) return;

  // === ISO-Mapping vorbereiten ===
  const isoByName = {};
  for (const [name, c] of Object.entries(countries)) {
    const iso = c.iso_a3 || c.ISO_A3 || c.iso || c.code;
    if (iso) isoByName[name.toLowerCase()] = iso.toUpperCase();
  }

  // === Aliase ergänzen ===
  if (!window._countryMappings) {
    try {
      const res = await fetch("data/meta/country_mappings.json", { cache: "no-store" });
      window._countryMappings = await res.json();
    } catch {
      window._countryMappings = {};
    }
  }
  if (meta !== getMetaForCurrent() || snapshotYear !== countrySnapshotYear(meta)) return;
  if (mapLayer) map.removeLayer(mapLayer);
  if (window._legendControl) map.removeControl(window._legendControl);
  for (const [alias, canonical] of Object.entries(window._countryMappings)) {
    const canonicalIso = isoByName[canonical.toLowerCase()];
    if (canonicalIso) isoByName[alias.toLowerCase()] = canonicalIso;
  }

  // === Letzten gültigen Wert pro Land bestimmen ===
  const latestByCountry = new Map();
  for (const d of data) {
    if (!d || !d.country || d.country === "World" || d.value == null) continue;
    if (snapshotYear !== null && normalizeYear(d.year) !== snapshotYear) continue;
    const cname = d.country.trim();
    const prev = latestByCountry.get(cname);
    if (!prev || d.year > prev.year)
      latestByCountry.set(cname, { year: d.year, value: Number(d.value) });
  }

  const display = relationDisplay(meta);

  // === ISO → Value map ===
  const mapDataByIso = {};
  for (const [rawName, rec] of latestByCountry.entries()) {
    const iso = isoByName[rawName.toLowerCase()] || null;
    const value = applyRelation(rec.value, rawName, rec.year, display);
    if (iso && Number.isFinite(value)) mapDataByIso[iso] = value;
  }

  const values = Object.values(mapDataByIso).filter(v => Number.isFinite(v));
  if (!values.length) return;

  const sortMode = (meta.sort || "higher").toLowerCase();
  const targetVal = parseFloat(meta.target_value ?? NaN);

  // 📊 Robust scaling (5.–95. Perzentil + log-Dämpfung)
  const sorted = [...values].sort((a, b) => a - b);
  const q05 = sorted[Math.floor(sorted.length * 0.05)] ?? Math.min(...values);
  const q95 = sorted[Math.floor(sorted.length * 0.95)] ?? Math.max(...values);
  let adjMin = Math.max(q05, Math.min(...values));
  let adjMax = Math.min(q95, Math.max(...values));

  const spreadRatio = adjMax / Math.max(adjMin, 1e-6);
  const useLog = adjMin > 0 && spreadRatio > 50; // Log bei sehr großer Spanne

  const normalize = v => {
    if (!Number.isFinite(v)) return 0.5;
    if (useLog && v > 0) {
      const minL = Math.log10(Math.max(adjMin, 1e-6));
      const maxL = Math.log10(Math.max(adjMax, 1e-6));
      const x = Math.log10(v);
      return (x - minL) / (maxL - minL);
    }
    return (v - adjMin) / (adjMax - adjMin);
  };

	// === Farbzuweisung (grün–gelb–rot, heller im Mittelbereich) ===
  const envScale = environmentalScale(meta, values);
	const getColor = val => {
    if (envScale) return environmentalColor(envScale, val);
		if (!Number.isFinite(val)) return "#e6e6e6";

		// 🎯 Zielmodus (Zielnähe = grün)
		if (sortMode === "target" && Number.isFinite(targetVal)) {
			const maxDev = Math.max(
				Math.abs(adjMax - targetVal),
				Math.abs(adjMin - targetVal),
				1e-6
			);
			const dev = Math.abs(val - targetVal) / maxDev;
			const hue = 120 * (1 - Math.min(dev, 1)); // 120=grün, 0=rot
			return `hsl(${hue},85%,50%)`;
		}

		// 🔁 Normalisierung 0..1
		const n = Math.max(0, Math.min(1, normalize(val)));
		if (sortMode === "neutral") return `hsl(213,65%,${92 - n * 60}%)`;

		// ✅ Korrekte Farblogik:
		// sort:"higher" → hohe Werte sind gut → grün
		// sort:"lower" → niedrige Werte sind gut → grün
		let hue;
		if (sortMode === "higher") {
			hue = 120 * n; // low=rot → high=grün
		} else if (sortMode === "lower") {
			hue = 120 * (1 - n); // low=grün → high=rot
		} else {
			// neutral oder unbekannt
			hue = 120 * n;
		}

		const sat = 85;
		const light = 40 + n * 20;
		return `hsl(${hue},${sat}%,${light}%)`;
	};


	// === Länder einfärben (mit robustem ISO-Resolver & Tooltip-Fix) ===
	mapLayer = L.geoJSON(window._worldGeoJSON, {
		style: f => {
			// 🧩 ISO-Fallbacks aus diversen GeoJSON-Feldern
			const iso = (
				f.properties.iso_a3_eh || f.properties.ISO_A3_EH ||
				f.properties.ISO_A3 || f.properties.iso_a3 ||
				f.properties.ADM0_A3 || f.properties.adm0_a3 ||
				f.properties.SOV_A3 || f.properties.sov_a3 ||
				f.properties.WB_A3 || f.properties.wb_a3 ||
				f.properties.gu_a3 || f.properties.su_a3 ||
				f.id || ""
			).toUpperCase();

			// 🧭 Versuche, Land über ISO zu finden; falls nicht vorhanden → Name-Mapping
			let val = mapDataByIso[iso];
			if (val === undefined) {
				const name = (
					f.properties.ADMIN ||
					f.properties.NAME ||
					f.properties.COUNTRY ||
					f.properties.SOVEREIGNT ||
					""
				).trim();
				if (name) {
					const canonical = window._countryMappings?.[name] || name;
					const isoFromName = isoByName[canonical.toLowerCase()];
					if (isoFromName) val = mapDataByIso[isoFromName];
				}
			}

			return {
				fillColor: getColor(val),
				fillOpacity: Number.isFinite(val) ? 0.82 : 0.15,
				color: "#555",
				weight: 0.4
			};
		},

		onEachFeature: (f, layer) => {
			// 🧩 Gleicher ISO-Resolver wie oben
			const iso = (
				f.properties.iso_a3_eh || f.properties.ISO_A3_EH ||
				f.properties.ISO_A3 || f.properties.iso_a3 ||
				f.properties.ADM0_A3 || f.properties.adm0_a3 ||
				f.properties.SOV_A3 || f.properties.sov_a3 ||
				f.properties.WB_A3 || f.properties.wb_a3 ||
				f.properties.gu_a3 || f.properties.su_a3 ||
				f.id || ""
			).toUpperCase();

			// 🧭 Fallback auf Namensauflösung
			let cname =
				Object.entries(countries).find(
					([, c]) => (c.iso_a3 || c.ISO_A3)?.toUpperCase() === iso
				)?.[0] ||
				f.properties.ADMIN ||
				f.properties.NAME ||
				f.properties.COUNTRY ||
				iso;

			// Wenn Alias existiert, auf kanonischen Namen umschreiben
			if (window._countryMappings?.[cname]) {
				cname = window._countryMappings[cname];
			}

			const canonicalIso = isoByName[cname.toLowerCase()];
			const val =
				mapDataByIso[iso] ??
				(canonicalIso ? mapDataByIso[canonicalIso] : undefined);

                        const info = countries[cname] || {};
                        const flagSrc =
                                info.flag ||
                                (info.iso_a2
                                        ? `images/flag/${String(info.iso_a2).toLowerCase()}.svg`
                                        : "images/flag/question.svg");
                        const valueUnit = display.unit ? ` ${display.unit}` : "";
                        const displayValue = Number.isFinite(val)
                                ? `${display.relation ? formatRelationValue(val) : formatValueAuto(val)}${valueUnit}`
                                : "no data";

                        const tooltip = `
                                <div class="map-tooltip">
                                        <div class="map-tooltip__header">
                                                <img class="map-tooltip__flag" src="${flagSrc}" alt="Flag of ${cname}" loading="lazy" />
                                                <div class="map-tooltip__title">${cname}</div>
                                        </div>
                                        <div class="map-tooltip__value">${displayValue}</div>
                                        <div class="map-tooltip__meta">
                                                <div class="map-tooltip__meta-row">Capital: ${info.capital || "–"}</div>
                                                <div class="map-tooltip__meta-row">Gov: ${info.government || "–"}</div>
                                                <div class="map-tooltip__meta-row">Languages: ${info.languages || "–"}</div>
                                        </div>
                                </div>
                        `;
			layer.bindTooltip(tooltip, { sticky: true });
			layer.on("tooltipopen", e => {
				const flag = e.tooltip.getElement()?.querySelector(".map-tooltip__flag");
				if (!flag) return;
				const useFallbackFlag = () => {
					flag.src = "images/flag/question.svg";
				};
				flag.addEventListener("error", useFallbackFlag, { once: true });
				if (flag.complete && flag.naturalWidth === 0) {
					useFallbackFlag();
				}
			});

			layer.on({
				mouseover: e => e.target.setStyle({ weight: 1.2, color: "#000", fillOpacity: 0.9 }),
				mouseout: e => mapLayer.resetStyle(e.target)
			});
		}
	}).addTo(map);

  // === Neue Legende ===
  const mapTitle = snapshotYear === null ? meta.title || currentKpi : `${meta.title || currentKpi} (${snapshotYear})`;
  const legendHTML = envScale
    ? `<div class="legend-box"><div class="legend-title"><strong>${escapeHtml(mapTitle)}</strong></div><div class="legend-bar legend-bar--environment"></div><div class="legend-scale"><span>Higher pressure / worse outcome</span><span>Lower pressure / better outcome</span></div><div class="legend-note">${escapeHtml(environmentalScaleNote(envScale))}</div></div>`
    : buildHeatLegendHTML({
    title: mapTitle,
    formatValue: display.relation ? formatRelationValue : formatValueAuto,
    unit: display.unit,
    min: adjMin,
    max: adjMax,
    sortMode,
    targetVal,
    useLog
  });
  const mapLegend = document.getElementById("map-legend");
  if (mapLegend) {
    // ✅ Security fix: legendHTML is built from safe template literals only
    // (no user input), so innerHTML is safe here
    mapLegend.innerHTML = legendHTML;
  }

  console.log(`🎨 Map rendered (balanced scale, log=${useLog})`);
}

/* === Hilfsfunktion: HTML-Farbskala für Heatmap (inkl. Log-Hinweis, 2025-11-13 FIXED) === */
// Simple HTML escaping to prevent XSS when interpolating dynamic values into innerHTML
function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
    .replace(/\//g, "&#x2F;");
}

function buildHeatLegendHTML({
  title, unit, min, max,
  sortMode = "higher",
  targetVal = NaN,
  formatValue = formatValueAuto,
  useLog = false
}) {
  // ✅ Richtige Richtung: Grün = besser
  const sortVariant = String(sortMode).toLowerCase();
  let variant = "higher";
  let modeText = "Higher values = greener";

  switch (sortVariant) {
    case "lower":
      variant = "lower";
      modeText = "Lower values = greener";
      break;
    case "target":
      variant = "target";
      modeText = `Closer to target (${formatValueAuto(targetVal)} ${unit}) = greener`;
      break;
    case "higher":
      variant = "higher";
      modeText = "Higher values = greener";
      break;
    case "neutral":
      variant = "neutral";
      modeText = "Darker blue = higher values";
      break;
    default:
      variant = "higher";
      modeText = "Quantitative scale (higher = greener)";
  }

  const minLabelRaw = typeof min === "number" ? formatValue(min) : String(min ?? "");
  const maxLabelRaw = typeof max === "number" ? formatValue(max) : String(max ?? "");
  const safeTitle = escapeHtml(title);
  const safeUnit = escapeHtml(unit);
  const safeMinLabel = escapeHtml(minLabelRaw);
  const safeMaxLabel = escapeHtml(maxLabelRaw);
  const safeModeText = escapeHtml(modeText);

  const logInfo = useLog
    ? `<div class="legend-note">⚙️ log-scaled (extreme values damped)</div>`
    : "";

  return `
  <div class="legend-box">
    <div class="legend-title"><strong>${safeTitle}</strong></div>
    <div class="legend-bar legend-bar--${variant}"></div>
    <div class="legend-scale">
      <span>${safeMinLabel} ${safeUnit}</span>
      <span>${safeMaxLabel} ${safeUnit}</span>
    </div>
    <div class="legend-mode legend-mode--${variant}">${safeModeText}</div>
    ${logInfo}
  </div>`;
}


/* ========= Map Highlight (bestehend, unverändert) ========= */
function highlightOnMap(country) {
  if (!countries[country]) return;
  const info = countries[country];
  if (!info.lat || !info.lon) return;

  map.flyTo([info.lat, info.lon], 5);
  L.popup()
    .setLatLng([info.lat, info.lon])
    .setContent(
      `${country}<br>Capital: ${info.capital || "–"}<br>Gov: ${info.government || "–"}`
    )
    .openOn(map);
}

// === Globale Registrierung beibehalten ===
window.initMap = initMap;
window.updateMap = updateMap;
window.highlightOnMap = highlightOnMap;

/* ========= MAP AUTO-INIT (Retry Logic for Leaflet) ========= */
const runWhenReady =
  typeof onDocumentReady === "function"
    ? onDocumentReady
    : handler => {
        if (typeof handler !== "function") return;
        if (document.readyState === "loading") {
          document.addEventListener("DOMContentLoaded", handler, { once: true });
        } else {
          handler();
        }
      };

runWhenReady(async () => {
  for (let tries = 1; tries <= 5; tries++) {
    const mapEl = document.getElementById("map");
    if (mapEl && mapEl.offsetHeight > 0 && typeof L !== "undefined") {
      console.log("➡️ initMap() after", tries, "tries");
      await initMap();
      setTimeout(() => window.map?.invalidateSize?.(), 800);
      
      // ✅ Fix: Enable page scrolling via mousewheel (even over the map)
      document.addEventListener("wheel", e => {
        // Allow normal scroll behavior
        window.scrollBy(0, e.deltaY * 0.5);
      }, { capture: true, passive: true });
      
      return;
    }
    await new Promise(r => setTimeout(r, 300));
  }
  console.warn("⚠️ Map initialization failed after 5 retries");
});


/* ========= Start ========= */
runWhenReady(() => init());

