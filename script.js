/* ========= Fetch helper ========= */
async function loadJSON(path) {
  try {
    const res = await fetch(path, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const txt = await res.text();
    return txt ? JSON.parse(txt) : [];
  } catch (e) {
    console.error("❌ loadJSON", path, e);
    return [];
  }
}

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
      console.warn(
        "RealityCheck: #kpiSelect not found -- skipping init (likely main frame)."
      );
      return;
    }

    // === Daten laden ===
    kpis = await loadJSON("data/meta/available_kpis.json");
    countries = await loadJSON("data/meta/countries.json");
    groups = await loadJSON("data/meta/groups.json");
    fetchStatus = await loadJSON("data/fetch_status.json");
    populationData = await loadJSON("data/population.json");
    gdpData = await loadJSON("data/gdp.json");
    areaData = await loadJSON("data/area.json");

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

    window.addEventListener("load", () => initMap());
  } catch (e) {
    console.error("RealityCheck init() failed:", e);
  }
}

/* ========= Populate KPI ========= */
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
    // === KPIs thematisch clustern ===
    for (const meta of getKpiArray().filter(k => k.world_kpi !== "e")) {
      const id = meta.filename; // 🔹 normalizeName entfernt
      const cl = meta.cluster || "Other";
      if (!clusters[cl]) clusters[cl] = [];
      clusters[cl].push({ id, title: meta.title, relation: meta.relation });
    }

    // === Dropdowns nach Cluster & Alphabet sortieren ===
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

/* ========= Relation ========= */
function applyRelation(v, c, y) {
  const rel = document.getElementById("relationSelect");
  const m = getMetaForCurrent();
  if (!v) return v;
  if (m && m.relation === "*") return v;
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
  // 🔹 normalizeName entfernt: direkter Vergleich über filename
  return arr.find(m => (m.filename || m.id || m.title) === currentKpi) || null;
}

/* ========= Sorting ========= */
function bindHeaderSorting() {
  const headers = document.querySelectorAll("#country-table th[data-col]");
  if (!headers.length) return;

  headers.forEach(th => {
    th.replaceWith(th.cloneNode(true));
  });

  const freshHeaders = document.querySelectorAll("#country-table th[data-col]");
  freshHeaders.forEach(th => {
    th.addEventListener("click", () => {
      const col = th.dataset.col;
      if (!col) return;
      if (userSort.col === col) {
        userSort.asc = !userSort.asc;
      } else {
        userSort = { col, asc: col === "country" || col === "rank" };
      }
      updateTable();
    });
  });
}

function determineCommonScale(values) {
  const maxVal = Math.max(...values.map(v => Math.abs(v || 0)));
  if (maxVal >= 1e12) return { divisor: 1e12, suffix: "T" };
  if (maxVal >= 1e9) return { divisor: 1e9, suffix: "B" };
  if (maxVal >= 1e6) return { divisor: 1e6, suffix: "M" };
  if (maxVal >= 1e3) return { divisor: 1e3, suffix: "K" };
  return { divisor: 1, suffix: "" };
}

/* ========= Table ========= */
function updateTable() {
  const tbody = document.querySelector("#country-table tbody");
  if (!tbody || !currentKpi) return;
  tbody.innerHTML = "";

  const compYearEl = document.getElementById("yearSelect");
  const compYear = compYearEl ? parseInt(compYearEl.value) || null : null;

  const meta = getMetaForCurrent() || {};
  const unit = (meta.unit || "").trim();
  const scaleMode = meta.scale || "auto";

  const rows = [];
  for (const c of Object.keys(countries)) {
    const vals = currentData.filter(r => r.country === c);
    if (!vals.length) continue;

    const latest = vals.sort((a, b) => b.year - a.year)[0];
    const prev = vals.find(r => r.year === latest.year - 1);
    const comp = compYear ? vals.find(r => r.year === compYear) : null;

    const lv = applyRelation(latest.value, c, latest.year);
    const pv = prev ? applyRelation(prev.value, c, prev.year) : null;
    const cv = comp ? applyRelation(comp.value, c, comp.year) : null;

    const arrow = pv != null ? calcTrend(lv, pv) : "→";
    const dAbs = pv != null ? lv - pv : null;
    const dPct = pv ? ((lv - pv) / pv) * 100 : null;
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

  let scaleInfo = { divisor: 1, suffix: "" };
  if (meta.scale === "auto") {
    const allValues = rows.map(r => r.value).filter(v => !isNaN(v));
    scaleInfo = determineCommonScale(allValues);
  }

  const groupRows = [];
  for (const [gKey, gDef] of Object.entries(groups)) {
    const members = gDef.members || [];
    const title = gDef.title || gKey;
    const mrows = rows.filter(r => members.includes(r.country));
    if (!mrows.length) continue;

    let agg;
    if ((meta.unit || "").includes("%") || meta.scale === "none") {
      agg = mrows.reduce((a, r) => a + (r.value || 0), 0) / mrows.length;
    } else {
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
      isGroup: true
    });
  }

  let sortedRows = [...rows];
  const sortType = (meta.sort || "higher").toLowerCase();
  const targetVal = parseFloat(meta.target_value || 0);

  if (userSort.col && userSort.col !== "rank") {
    const { col, asc } = userSort;
    sortedRows.sort((a, b) => {
      const A = a[col] ?? 0,
        B = b[col] ?? 0;
      if (A === B) return 0;
      return asc ? (A > B ? 1 : -1) : A < B ? 1 : -1;
    });
  } else {
    if (sortType === "higher") {
      sortedRows.sort((a, b) => (b.value || 0) - (a.value || 0));
    } else if (sortType === "lower") {
      sortedRows.sort((a, b) => (a.value || 0) - (b.value || 0));
    } else if (sortType === "target") {
      sortedRows.sort((a, b) => {
        const devA = Math.abs((a.value ?? 0) - targetVal);
        const devB = Math.abs((b.value ?? 0) - targetVal);
        return devA - devB;
      });
    } else {
      sortedRows.sort((a, b) => (b.value || 0) - (a.value || 0));
    }
  }

  const rankMap = new Map();
  let rankCounter = 0;
  sortedRows.forEach(r => {
    if (r.country === "World" || r.country === "Welt") {
      rankMap.set(r.country, "🌍");
    } else {
      rankCounter++;
      rankMap.set(r.country, rankCounter);
    }
  });

  const final = [
    ...sortedRows.map(r => ({ ...r, rank: rankMap.get(r.country) })),
    ...groupRows.map(r => ({ ...r, rank: "–" }))
  ];

  if (userSort.col === "rank") {
    final.sort((a, b) => {
      const ar = a.rank === "🌍" || a.rank === "–" ? Infinity : a.rank;
      const br = b.rank === "🌍" || b.rank === "–" ? Infinity : b.rank;
      if (ar === br) return 0;
      return userSort.asc ? (ar > br ? 1 : -1) : ar < br ? 1 : -1;
    });
  }

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
    if (r.country === "World" || r.country === "Welt") tr.classList.add("world-row");

    tr.addEventListener("click", () => {
      if (!r.isGroup) highlightOnMap(r.country);
    });

    const deltaTitle =
      r.deltaPrevAbs != null
        ? `title="Δ vs Prev: ${formatValueAuto(r.deltaPrevAbs, scaleMode)} (${
            r.deltaPrevPct != null ? r.deltaPrevPct.toFixed(2) + "%" : "n/a"
          })"`
        : `title="No previous year data"`;

    tr.innerHTML = `
      <td>${r.rank ?? ""}</td>
      <td>${r.country}</td>
      <td>${
        meta.scale === "auto"
          ? (r.value / scaleInfo.divisor).toFixed(2) + " " + scaleInfo.suffix
          : formatValueAuto(r.value, scaleMode)
      }${unit ? " " + unit : ""}</td>
      <td class="trend" ${deltaTitle}>${r.deltaPrevArrow}</td>
      <td>${r.deltaComp ?? "-"}</td>
      <td>${r.update ?? "-"}</td>
    `;
    tbody.appendChild(tr);
  });

  // === Header-Pfeile & aktive Spalte markieren ===
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
          setTimeout(() => {
            cell.style.background = "";
          }, 300);
        }
      });
    }
  }

  // === Legenden-Hinweis aktualisieren ===
  const roundInfo = document.getElementById("rounding-info");
  if (roundInfo) {
    if (scaleMode === "auto") {
      let explain =
        "Values are automatically scaled (K, M, B, T). K = thousand (10³), M = million (10⁶), B = billion (10⁹), T = trillion (10¹²).";
      roundInfo.textContent = explain;
      if (scaleInfo && scaleInfo.suffix) {
        roundInfo.textContent += ` (All values in ${scaleInfo.suffix})`;
      }
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

  const meta = getMetaForCurrent() || {
    title: currentKpi || "Selected KPI",
    unit: ""
  };
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
      fill: false,
      tension: 0.25
    });
  });

  const ctx = ctxEl.getContext("2d");
  if (chartInstance) chartInstance.destroy();

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
      plugins: {
        title: { display: true, text: meta.title || "No data selected" },
        legend: { display: datasets.length > 0 }
      },
      scales: {
        y: { beginAtZero: true, title: { display: true, text: meta.unit || "" } },
        x: { grid: { color: "rgba(255,255,255,0.05)" } }
      }
    }
  });
}

/* ========= Map ========= */
function initMap() {
  const el = document.getElementById("map");
  if (!el) {
    console.warn("⚠️ Kein #map-Element gefunden – Map wird nicht initialisiert.");
    return;
  }

  map = L.map("map").setView([20, 0], 2);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  setTimeout(() => {
    if (map && typeof map.invalidateSize === "function") {
      map.invalidateSize();
      console.log("✅ Leaflet map rendered & resized");
    } else {
      console.warn("⚠️ map.invalidateSize() nicht verfügbar");
    }
  }, 100);
}
/* ========= Map Update ========= */
function updateMap() {
  if (!map || !currentKpi) return;
  if (mapLayer) map.removeLayer(mapLayer);
  mapLayer = L.layerGroup().addTo(map);
}

/* ========= Country Highlight ========= */
function highlightOnMap(country) {
  if (!countries[country]) return;
  const info = countries[country];
  if (!info.lat || !info.lon) return;

  map.flyTo([info.lat, info.lon], 5);
  L.popup()
    .setLatLng([info.lat, info.lon])
    .setContent(
      `${country}<br>Capital: ${info.capital || "–"}<br>Gov: ${
        info.government || "–"
      }`
    )
    .openOn(map);
}

/* ========= Start ========= */
document.addEventListener("DOMContentLoaded", () => init());
  