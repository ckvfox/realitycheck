// core.js already provides loadJSON(), showSpinner(), etc.
let ALL_DATA = {};  // consolidated dataset


/* ========= Globals ========= */
let kpis = {}, countries = {}, groups = {}, fetchStatus = {};
let populationData = [], gdpData = [], areaData = [];
let currentKpi = null, currentData = [], chartInstance = null;
let map = null, mapLayer = null;
let userSort = { col: null, asc: false };
let currentScale = { factor: 1, suffix: "", label: "Exact values" };
let sortingBound = false;

/* ========= Frame Loader ========= */
function loadFrame(page) {
  const frame = document.getElementById("main-frame");
  if (frame) frame.src = page;
}

/* ========= Helpers ========= */
function chooseScaleFromValues(v) {
  const m = Math.max(0, ...v.map(x => (x == null ? 0 : Math.abs(x))));
  if (m >= 1e9) return { factor: 1e9, suffix: "B", label: "Billions" };
  if (m >= 1e6) return { factor: 1e6, suffix: "M", label: "Millions" };
  if (m >= 1e3) return { factor: 1e3, suffix: "K", label: "Thousands" };
  return { factor: 1, suffix: "", label: "Exact values" };
}
function formatValueAuto(value, scaleMode = "auto") {
  if (value === null || value === undefined || isNaN(value)) return "-";
  const abs = Math.abs(value);
  if (scaleMode === "%" || scaleMode === "none" || scaleMode === "index")
    return value.toFixed(2);
  if (scaleMode === "auto") {
    if (abs >= 1e12) return (value / 1e12).toFixed(2) + " T";
    if (abs >= 1e9) return (value / 1e9).toFixed(2) + " B";
    if (abs >= 1e6) return (value / 1e6).toFixed(2) + " M";
    if (abs >= 1e3) return (value / 1e3).toFixed(2) + " K";
    return value.toFixed(2);
  }
  return value.toFixed(2);
}
function formatWithScale(v) {
  return v == null || isNaN(v)
    ? "-"
    : (v / currentScale.factor).toFixed(2) +
        (currentScale.suffix ? " " + currentScale.suffix : "");
}
function calcTrend(a, b) {
  if (a == null || b == null) return "→";
  return a > b ? "↑" : a < b ? "↓" : "→";
}
function getKpiArray() {
  return Array.isArray(kpis)
    ? kpis
    : kpis && typeof kpis === "object"
    ? Object.values(kpis)
    : [];
}

/* ========= Init ========= */
async function init() {
  try {
    if (
      document.readyState !== "complete" &&
      document.readyState !== "interactive"
    )
      await new Promise(r =>
        document.addEventListener("DOMContentLoaded", r, { once: true })
      );
    if (!document.getElementById("kpiSelect")) {
      console.warn("RealityCheck: #kpiSelect not found -- skipping init.");
      return;
    }

    // === Daten laden ===
	showSpinner(true, "Loading data…"); // ✅ zentraler Loader aktivieren
    kpis = await loadJSON("data/meta/available_kpis.json");
    countries = await loadJSON("data/meta/countries.json");
    groups = await loadJSON("data/meta/groups.json");
    fetchStatus = await loadJSON("data/fetch_status.json");
    populationData = await loadJSON("data/population.json");
    gdpData = await loadJSON("data/gdp.json");
    areaData = await loadJSON("data/area.json");
	ALL_DATA = await loadAllKPIData(); // ✅ Consolidated dataset
	showSpinner(false); // Loader wieder ausblenden


    // === Dropdowns & Eventhandler ===
    await populateKpiSelect();
    populateHomeCountrySelect();
    populateCountrySelects();
    bindHeaderSorting();

    const el = id => document.getElementById(id);
    el("kpiSelect")?.addEventListener("change", () => {
      userSort = { col: null, asc: false };
      updateView();
    });
    el("yearSelect")?.addEventListener("change", updateTable);
    el("relationSelect")?.addEventListener("change", () => {
      updateTable();
      updateChart();
      updateMap();
    });
    el("countrySelect")?.addEventListener("change", updateTable);
    ["country1Select", "country2Select", "country3Select"].forEach(id =>
      el(id)?.addEventListener("change", updateChart)
    );

    if (!window.map) window.addEventListener("load", () => initMap());
  } catch (e) {
    console.error("RealityCheck init() failed:", e);
  }
}

/* ========= KPI-Auswahl ========= */
async function populateKpiSelect() {
  const sel = document.getElementById("kpiSelect");
  const spinner = document.getElementById("overlay-spinner");
  if (!sel) return;

  if (spinner) spinner.classList.remove("hidden");
  sel.disabled = true;
  sel.innerHTML = "<option>Loading KPIs…</option>";

  const clusters = {};
  const tmp = [];

  try {
    for (const meta of getKpiArray().filter(k => k.world_kpi !== "e")) {
      const id = meta.filename;
      const cl = meta.cluster || "Other";
      if (!clusters[cl]) clusters[cl] = [];
      clusters[cl].push({ id, title: meta.title, relation: meta.relation });
    }

    for (const cl of Object.keys(clusters).sort()) {
      const g = document.createElement("optgroup");
      g.label = cl;
      for (const it of clusters[cl].sort((a, b) => a.title.localeCompare(b.title))) {
        const o = document.createElement("option");
        o.value = it.id;
        o.textContent = it.title;
        try {
          const d = await loadJSON(`data/${it.id}.json`);
          if (!Array.isArray(d) || !d.length) {
            o.style.color = "gray";
            o.style.fontStyle = "italic";
          }
        } catch {
          o.style.color = "gray";
          o.style.fontStyle = "italic";
        }
        g.appendChild(o);
      }
      tmp.push(g);
    }

    sel.innerHTML = "<option value=''>-- none --</option>";
    tmp.forEach(g => sel.appendChild(g));
  } catch (e) {
    console.error("populateKpiSelect() failed:", e);
  } finally {
    sel.classList.remove("loading");
    sel.disabled = false;
    if (spinner) spinner.classList.add("hidden");
  }
}

/* ========= Country Selects ========= */
function populateHomeCountrySelect() {
  const s = document.getElementById("countrySelect");
  if (!s) return;
  s.innerHTML = "<option value=''>-- none --</option>";
  Object.keys(countries)
    .sort()
    .forEach(n => {
      const o = document.createElement("option");
      o.value = n;
      o.textContent = n;
      s.appendChild(o);
    });
}

function populateCountrySelects() {
  const ids = ["country1Select", "country2Select", "country3Select"];
  ids.forEach(id => {
    const s = document.getElementById(id);
    if (!s) return;
    s.innerHTML = "<option value=''>-- none --</option>";
    Object.keys(countries)
      .sort()
      .forEach(n => {
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
function applyRelation(v, c, y) {
  const rel = document.getElementById("relationSelect");
  const m = getMetaForCurrent();
  if (!v) return v;
  if (!m || m.relation !== "*") return v;
  if (rel?.value === "percapita") {
    const p = populationData.find(r => r.country === c && r.year === y);
    return p ? v / p.value : null;
  }
  if (rel?.value === "pergdp") {
    const g = gdpData.find(r => r.country === c && r.year === y);
    return g ? v / g.value : null;
  }
  if (rel?.value === "perkm2") {
    const a = areaData.find(r => r.country === c && r.year === y);
    return a ? v / a.value : null;
  }
  return v;
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
  const headers = document.querySelectorAll("#country-table th[data-col]");
  if (!headers.length) return;

  headers.forEach(th => th.replaceWith(th.cloneNode(true)));
  const freshHeaders = document.querySelectorAll("#country-table th[data-col]");
  freshHeaders.forEach(th => {
    th.addEventListener("click", () => {
      const col = th.dataset.col;
      if (!col) return;
      if (userSort.col === col) userSort.asc = !userSort.asc;
      else userSort = { col, asc: col === "country" || col === "rank" };
      updateTable();
    });
  });
}

/* ========= Year Select (Comparison) ========= */
function populateYearSelect() {
  const sel = document.getElementById("yearSelect");
  if (!sel) return;

  const years = Array.isArray(currentData)
    ? [...new Set(currentData.map(r => r.year))].filter(y => Number.isFinite(y)).sort((a,b) => b - a)
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


/* ========= Table ========= */
function updateTable() {
  const tbody = document.querySelector("#country-table tbody");
  if (!tbody || !currentKpi) return;
  tbody.innerHTML = "";

  const compYearEl = document.getElementById("yearSelect");
  const compYear = compYearEl && compYearEl.value !== "" ? parseInt(compYearEl.value) : null;


  const meta = getMetaForCurrent() || {};
  const unit = (meta.unit || "").trim();
  const scaleMode = meta.scale || "auto";

  // === Länderzeilen ===
  const rows = [];
  for (const c of Object.keys(countries)) {
    const vals = currentData.filter(r => r.country === c);
    if (!vals.length) continue;

    const latest = vals.sort((a, b) => b.year - a.year)[0];
    const prev   = vals.find(r => r.year === latest.year - 1);
    const comp   = compYear ? vals.find(r => r.year === compYear) : null;

    const lv = applyRelation(latest.value, c, latest.year);
    const pv = prev ? applyRelation(prev.value, c, prev.year) : null;
    const cv = comp ? applyRelation(comp.value, c, comp.year) : null;

    const arrow = pv != null ? calcTrend(lv, pv) : "→";
    const dAbs  = pv != null ? lv - pv : null;
    const dPct  = pv ? ((lv - pv) / pv) * 100 : null;
    const dComp = cv != null ? (((lv - cv) / cv) * 100).toFixed(2) + "%" : "-";

    rows.push({
      country: c,
      value: lv,
      deltaPrevArrow: arrow,
      deltaPrevAbs: dAbs,
      deltaPrevPct: dPct,
      deltaComp: dComp,
      update: latest.year,
      isGroup: false
    });
  }

  // === Adaptive Skalierung bestimmen ===
  let scaleInfo = { divisor: 1, suffix: "" };
  if (meta.scale === "auto") {
    const allValues = rows.map(r => r.value).filter(v => !isNaN(v));
    scaleInfo = determineAdaptiveScale(allValues);
  }

  // === Gruppenberechnung (Summe oder Durchschnitt) ===
  const groupRows = [];
  for (const [gKey, gDef] of Object.entries(groups)) {
    const members = gDef.members || [];
    const title = gDef.title || gKey;
    const mrows = rows.filter(r => members.includes(r.country));
    if (!mrows.length) continue;

    let agg;
    const isRelative =
      (meta.unit || "").includes("%") ||
      ["index", "ratio", "none"].includes(meta.scale);

    if (isRelative) {
      // relative Kennzahlen → Durchschnitt
      agg = mrows.reduce((a, r) => a + (r.value || 0), 0) / mrows.length;
    } else {
      // absolute Kennzahlen → Summe
      agg = mrows.reduce((a, r) => a + (r.value || 0), 0);
    }

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
      aggregationType: isRelative ? "average" : "sum"
    });
  }

  // === Sortierung bestimmen ===
  let sortedRows = [...rows];
  const sortType  = (meta.sort || "higher").toLowerCase();
  const targetVal = parseFloat(meta.target_value || 0);

  if (userSort.col && userSort.col !== "rank") {
    const { col, asc } = userSort;
    sortedRows.sort((a, b) => {
      const A = a[col] ?? 0, B = b[col] ?? 0;
      if (A === B) return 0;
      return asc ? (A > B ? 1 : -1) : (A < B ? 1 : -1);
    });
  } else {
    if (sortType === "higher") sortedRows.sort((a, b) => (b.value || 0) - (a.value || 0));
    else if (sortType === "lower") sortedRows.sort((a, b) => (a.value || 0) - (b.value || 0));
    else if (sortType === "target") {
      sortedRows.sort((a, b) => {
        const devA = Math.abs((a.value ?? 0) - targetVal);
        const devB = Math.abs((b.value ?? 0) - targetVal);
        return devA - devB;
      });
    } else sortedRows.sort((a, b) => (b.value || 0) - (a.value || 0));
  }

  // === Ränge zuweisen ===
  const rankMap = new Map();
  let rankCounter = 0;
  sortedRows.forEach(r => {
    if (["World","Welt"].includes(r.country)) rankMap.set(r.country, "🌍");
    else {
      rankCounter++;
      rankMap.set(r.country, rankCounter);
    }
  });

  const final = [
    ...sortedRows.map(r => ({ ...r, rank: rankMap.get(r.country) })),
    ...groupRows.map(r => ({ ...r, rank: "–" }))
  ];
    // === Home Country sticky/top + highlight ===
  const home = document.getElementById("countrySelect")?.value;
  if (home) {
    const i = final.findIndex(r => r.country === home);
    if (i !== -1) {
      const hc = { ...final[i], highlight: true };
      final.splice(i, 1);
      final.unshift(hc);
    }
  }

  // === Tabelle rendern ===
  final.forEach(r => {
    const tr = document.createElement("tr");
    if (r.highlight) tr.classList.add("highlight");
    if (r.isGroup) tr.classList.add("group-row");
    if (["World","Welt"].includes(r.country)) tr.classList.add("world-row");

    // 🔹 Tooltip für Gruppen: Summe oder Durchschnitt
    if (r.isGroup) {
      tr.title = `Group value = ${r.aggregationType === "average" ? "Average" : "Sum"} of members`;
    }

    tr.addEventListener("click", () => {
      if (!r.isGroup) highlightOnMap(r.country);
    });

    const deltaTitle =
      r.deltaPrevAbs != null
        ? `title="Δ vs Prev: ${formatValueAuto(r.deltaPrevAbs, meta.scale)} (${
            r.deltaPrevPct != null ? r.deltaPrevPct.toFixed(2) + "%" : "n/a"
          })"`
        : `title="No previous year data"`;

    tr.innerHTML = `
      <td>${r.rank ?? ""}</td>
      <td>${r.country}</td>
      <td>${
        meta.scale === "auto"
          ? (r.value / scaleInfo.divisor).toFixed(2) + " " + scaleInfo.suffix
          : formatValueAuto(r.value, meta.scale)
      }${unit ? " " + unit : ""}</td>
      <td class="trend" ${deltaTitle}>${r.deltaPrevArrow}</td>
      <td>${r.deltaComp ?? "-"}</td>
      <td>${r.update ?? "-"}</td>
    `;
    tbody.appendChild(tr);
  });

  // === Header-Pfeile aktualisieren ===
  document.querySelectorAll("#country-table th[data-col]").forEach(th => {
    const col = th.dataset.col;
    const label = th.textContent.replace(/[▲▼]/g, "").trim();
    th.textContent = label;
    th.classList.remove("active-col");
    if (userSort.col === col) {
      th.textContent = label + (userSort.asc ? " ▲" : " ▼");
      th.classList.add("active-col");
    }
  });

  // === Sortierspalte visuell hervorheben ===
  const activeCol = userSort.col;
  if (activeCol) {
    const colIndex = { rank: 0, country: 1, value: 2 }[activeCol];
    if (colIndex !== undefined) {
      tbody.querySelectorAll("tr").forEach(tr => {
        const cell = tr.children[colIndex];
        if (cell) {
          cell.style.transition = "background 0.3s ease";
          cell.style.background = "rgba(255,255,0,0.07)";
          setTimeout(() => (cell.style.background = ""), 300);
        }
      });
    }
  }

  // === Legenden-Hinweis aktualisieren ===
  const roundInfo = document.getElementById("rounding-info");
  if (roundInfo) {
    if (scaleMode === "auto") {
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
  const years = currentData.length
    ? [...new Set(currentData.map(r => r.year))].sort((a, b) => a - b)
    : [];

  const datasets = [];
  ["country1Select", "country2Select", "country3Select"].forEach(id => {
    const sel = document.getElementById(id);
    if (!sel || !sel.value) return;
    const country = sel.value;
    const vals = years.map(y => {
      const rec = currentData.find(r => r.country === country && r.year === y);
      return rec ? applyRelation(rec.value, country, rec.year) : null;
    });
    datasets.push({
      label: country,
      data: vals,
      borderWidth: 2,
      borderColor: getColorForCountry(country),
      pointRadius: 3,
      pointHoverRadius: 5,
      fill: false,
      tension: 0.25
    });
  });

  const ctx = ctxEl.getContext("2d");
  if (chartInstance) chartInstance.destroy();

  // 💡 Chart.js mit Tooltip, Responsive, World-Styling
  chartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: years.length ? years : [0, 1, 2],
      datasets:
        datasets.length > 0
          ? datasets
          : [
              {
                label: "Select countries to display data",
                data: [null, null, null],
                borderColor: "rgba(200,200,200,0.3)",
                borderWidth: 1,
                fill: false
              }
            ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false, // ✅ Responsive Höhe durch css
	  aspectRatio: 2, // stabilisiert Höhe-Breite-Verhältnis
      layout: {
        padding: { top: 20, bottom: 10, left: 10, right: 10 }
      },
      plugins: {
        title: { 
          display: true, 
          text: meta.title || "No data selected" 
        },
        legend: { 
          display: datasets.length > 0 
        },
        tooltip: {
          enabled: true,
          callbacks: {
            label: function(ctx) {
              const country = ctx.dataset.label || '';
              const year = ctx.label;
              const value = ctx.parsed.y;
              if (value == null || isNaN(value)) return `${country}: no data (${year})`;
              return `${country}: ${value.toLocaleString()} (${year})`;
            },
            title: function(ctx) {
              return "Year: " + (ctx[0]?.label ?? "");
            }
          }
        }
      },
      interaction: {
        mode: 'nearest',
        intersect: false
      },
      scales: {
        y: { 
          beginAtZero: true, 
          title: { display: true, text: meta.unit || "" },
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
function getColorForCountry(name) {
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
function updateView() {
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

	currentData = ALL_DATA[filename] || [];

      console.log(`✅ updateView(): ${filename} → ${currentData.length} records`);

      populateYearSelect();
      updateTable();
      updateChart();
      updateMap();

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
          sourceLink.href = "#";
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
        dateEl.textContent = date !== "---"
          ? new Date(date).toISOString().split("T")[0] // nur Datumsteil anzeigen
          : "---";
      }
  } catch (e) {
    console.error("❌ updateView() failed:", e);
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


/* ========= Map ========= */
function initMap() {
  const el = document.getElementById("map");
  if (!el) {
    console.warn("⚠️ Kein #map-Element gefunden – Map nicht initialisiert.");
    return;
  }

  // 🌍 Grundinitialisierung mit Mobile-freundlichen Optionen
  map = L.map("map", {
    scrollWheelZoom: false,   // verhindert versehentliches Scrollen im Frame
    dragging: true,           // erlaubt Verschieben auf Mobil
    tap: true                 // erlaubt Tippen auf Marker
  }).setView([20, 0], 2);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  // 🩵 Mobile Exit-Fix (verhindert, dass man im Map-Bereich „gefangen“ bleibt)
  el.style.touchAction = "pan-x pan-y";     // erlaubt normales Scrollen
  document.body.style.overscrollBehavior = "contain"; // kein Scroll-Lock im Frame
  el.addEventListener("touchmove", e => e.stopPropagation(), { passive: true });

  // 🕐 Größe nach kurzer Verzögerung korrekt berechnen
  setTimeout(() => {
    if (map && typeof map.invalidateSize === "function") {
      map.invalidateSize();
      console.log("✅ Leaflet map rendered & resized (mobile-safe)");
    }
  }, 150);
}

// === Make map initialization globally accessible ===
window.initMap = initMap;
window.updateMap = updateMap;
window.highlightOnMap = highlightOnMap;


function updateMap() {
  if (!map || !currentKpi) return;
  if (mapLayer) map.removeLayer(mapLayer);
  mapLayer = L.layerGroup().addTo(map);
}

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


/* ========= Start ========= */
document.addEventListener("DOMContentLoaded", () => init());

// =====================================================
// 🔁 loadPage() for navigation (used in index.html <nav>)
// =====================================================
function loadPage(page, link) {
  const frame = document.getElementById("main-frame");
  const loader = document.getElementById("frame-loader");

  if (!frame) {
    console.warn("⚠️ main-frame element not found!");
    return;
  }

  // Loader aktivieren
  if (loader) loader.classList.add("active");

  // Seite neu laden (mit Cache-Bypass)
  frame.src = page + "?t=" + Date.now();

  // Aktiven Menüpunkt markieren
  document.querySelectorAll("nav a").forEach(a => a.classList.remove("active"));
  if (link) link.classList.add("active");

  // Wenn Frame fertig geladen ist → Loader ausblenden
  frame.addEventListener(
    "load",
    () => loader && loader.classList.remove("active"),
    { once: true }
  );
}

// Damit onclick="loadPage(...)" im HTML funktioniert
window.loadPage = loadPage;
