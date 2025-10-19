/* ============================================================
   🌍 RealityCheck – Overall Country Ranking (Relevance + Normalization)
   ============================================================ */

async function loadJSON(path) {
  try {
    const res = await fetch(path, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.error("❌ loadJSON failed:", path, e);
    return [];
  }
}

let kpis = [];
let countries = {};
let results = [];

/* ========= Init ========= */
document.addEventListener("DOMContentLoaded", () => initOverall());

async function initOverall() {
  const spinner = document.getElementById("overlay-spinner");
  if (spinner) spinner.classList.remove("hidden");

  kpis = await loadJSON("data/meta/available_kpis.json");
  countries = await loadJSON("data/meta/countries.json");

  buildRelevanceControls();
  await buildOverallRanking();

  if (spinner) spinner.classList.add("hidden");
}

/* ========= Relevance Weights ========= */
function getRelevanceWeight(level) {
  const map = {
    very_high: 1.5,
    high: 1.2,
    normal: 1.0,
    low: 0.6,
    irrelevant: 0.0
  };
  return map[level?.toLowerCase()] ?? 1.0;
}

/* ========= Build relevance selectors (clustered layout) ========= */
function buildRelevanceControls() {
  const container = document.getElementById("relevance-controls");
  container.innerHTML = "";

  const clusters = {};
  kpis
    .filter(k => k.world_kpi !== "e")
    .forEach(meta => {
      const cl = meta.cluster || "Other";
      if (!clusters[cl]) clusters[cl] = [];
      clusters[cl].push(meta);
    });

  for (const [clusterName, list] of Object.entries(clusters)) {
    const group = document.createElement("div");
    group.className = "cluster-group";
    const h3 = document.createElement("h3");
    h3.textContent = clusterName;
    group.appendChild(h3);

    list.sort((a, b) => a.title.localeCompare(b.title)).forEach(meta => {
      const row = document.createElement("div");
      row.className = "kpi-row";

      const label = document.createElement("label");
      label.textContent = meta.title + ": ";

      const sel = document.createElement("select");
      ["very_high", "high", "normal", "low", "irrelevant"].forEach(opt => {
        const o = document.createElement("option");
        o.value = opt;
        o.textContent = opt.replace("_", " ");
        if (opt === (meta.relevance || "normal")) o.selected = true; // ← Default aus available_kpis.json
        sel.appendChild(o);
      });

      sel.dataset.kpi = meta.filename;
      row.appendChild(label);
      row.appendChild(sel);
      group.appendChild(row);
    });

    container.appendChild(group);
  }

  // Event: Ranking neu berechnen
  document.getElementById("recalc-btn")?.addEventListener("click", async () => {
    for (const meta of kpis) {
      const sel = container.querySelector(`select[data-kpi="${meta.filename}"]`);
      if (sel) meta.relevance = sel.value;
    }
    await buildOverallRanking();
  });
}

/* ========= Build Overall Ranking ========= */
async function buildOverallRanking() {
  const valid = kpis.filter(k => k.world_kpi !== "e" && getRelevanceWeight(k.relevance) > 0);
  const aggregated = {};

  for (const meta of valid) {
    const id = meta.filename;
    const weight = getRelevanceWeight(meta.relevance);
    try {
      const data = await loadJSON(`data/${id}.json`);
      if (!Array.isArray(data) || data.length === 0) continue;

      const numeric = data.filter(d => typeof d.value === "number");
      if (numeric.length < 2) continue;

      const min = Math.min(...numeric.map(d => d.value));
      const max = Math.max(...numeric.map(d => d.value));
      const range = max - min || 1;

      for (const d of numeric) {
        const c = d.country;
        let norm = (d.value - min) / range;
        if (meta.relation === "lower") norm = 1 - norm;
        const val = norm * weight;

        if (!aggregated[c]) aggregated[c] = { sum: 0, count: 0 };
        aggregated[c].sum += val;
        aggregated[c].count++;
      }
    } catch (e) {
      console.warn(`⚠️ KPI ${id} failed:`, e);
    }
  }

  results = Object.entries(aggregated).map(([country, obj]) => ({
    country,
    score: obj.count ? obj.sum / obj.count : 0,
    used: obj.count
  }));

  results.sort((a, b) => b.score - a.score);
  renderOverallTable(results);
}

/* ========= Render Table ========= */
function renderOverallTable(list) {
  const tbody = document.querySelector("#overall-table tbody");
  tbody.innerHTML = "";

  let rank = 1;
  for (const entry of list) {
    if (entry.country === "World" || entry.country === "Welt") continue;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${rank}</td>
      <td>${entry.country}</td>
      <td>${(entry.score * 100).toFixed(2)}</td>
      <td>${entry.used}</td>
    `;
    tbody.appendChild(tr);
    rank++;
  }

  const lastUpdated = document.getElementById("last-updated");
  if (lastUpdated) {
    const d = new Date();
    lastUpdated.textContent = "Last calculated: " + d.toISOString().slice(0, 10);
  }
}