/* ============================================================
   🌍 RealityCheck – Overall Country Ranking Script (Final)
   ============================================================ */

const multipliers = { very_high: 0.2, high: 1.0, not_interested: 0.0 };
let available = [];
let overall = [];
let titleByFilename = {};
const EXCLUDE_COUNTRIES = new Set(["World"]);
let missingKPIs = []; // für Anzeige unten
const spinner = document.getElementById("spinner");
if (spinner) spinner.classList.add("active");


// ---------- FILE EXISTENCE CHECK ----------
async function fileExists(url) {
  try {
    const resp = await fetch(url, { method: "HEAD" });
    return resp.ok;
  } catch {
    return false;
  }
}

// ---------- FILTER KPIs WITH REAL DATA (improved dummy + exclude world_kpi/neutral) ----------
async function filterKPIsWithRealData(kpis) {
  const valid = [];
  missingKPIs = [];

  for (const k of kpis) {
    if (!k.title) continue;
    // ⚠️ Welt-KPI oder neutrale KPI? -> komplett ignorieren (nicht als "fehlend" zählen)
    if (k.world_kpi === "e" || k.sort === "neutral") {
      continue;
    }

    const key = normalizeKeyFromTitle(k.title);
    const url = `data/${key}.json`;

    try {
      const resp = await fetch(url);
      if (!resp.ok) throw new Error("not ok");
      const data = await resp.json();

      // Prüfen, ob tatsächlich Zahlen drin sind
      const hasData = Array.isArray(data)
        ? data.length > 3
        : Object.keys(data || {}).length > 3;

      if (hasData) {
        valid.push(k);
      } else {
        missingKPIs.push(k.title);
        console.warn(`⚠️ Dummy or empty data: ${k.title}`);
      }
    } catch {
      missingKPIs.push(k.title);
      console.warn(`⚠️ No data for KPI: ${k.title}`);
    }
  }

  return valid;
}




// ---------- DATA LOADING ----------
async function loadData() {
  try {
    const spinner = document.getElementById("overlay-spinner");
    if (spinner) spinner.classList.remove("hidden");

    available = await (await fetch("available_kpis.json")).json();
    overall   = await (await fetch("data/overall_ranking.json")).json();

    available = await filterKPIsWithRealData(available);

    titleByFilename = Object.fromEntries(
      available
        .filter(k => k.sort !== "neutral" && k.world_kpi !== "e")
        .map(k => [normalizeKeyFromTitle(k.title), k.title || normalizeKeyFromTitle(k.title)])
    );

    renderPrioritySelectors();
    fetchLastUpdated();
    console.log(`✅ ${available.length} KPIs with real data loaded.`);

    if (spinner) spinner.classList.add("hidden");

  } catch (err) {
    console.error("❌ Error loading data:", err);
  }
}


// ---------- NORMALIZE KEY ----------
function normalizeKeyFromTitle(t) {
  if (!t) return "";

  // Unicode-Sonderzeichen, Tiefstellungen & Aliase korrigieren
  let s = t
    .toLowerCase()
    .replace(/co₂|co\u2082/g, "co2") // CO₂ → co2 (auch Unicode-Variante)
    .replace(/₀/g, "0").replace(/₁/g, "1").replace(/₂/g, "2")
    .replace(/₃/g, "3").replace(/₄/g, "4").replace(/₅/g, "5")
    .replace(/₆/g, "6").replace(/₇/g, "7").replace(/₈/g, "8").replace(/₉/g, "9")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");

  // Aliase für spezielle Fälle
  if (s.startsWith("gdp")) return "gdp";   // alle GDP-Varianten
  if (s === "land_area") return "area";    // Land Area → area
  return s;
}


	/* ---------- UI: PRIORITIES (grouped by dynamic clusters + improved layout) ---------- */
	function renderPrioritySelectors() {
	  const box = document.getElementById("priority-container");
	  if (!box) return;
	  box.innerHTML = "";

	  // 1️⃣ Gruppieren nach Cluster
	  const groups = {};
	  (available || []).forEach(k => {
		if (!k || !k.title) return;
		if (k.sort === "neutral" || k.world_kpi === "e") return;
		const cluster = (k.cluster && String(k.cluster).trim()) || "Other";
		if (!groups[cluster]) groups[cluster] = [];
		groups[cluster].push(k);
	  });

	  // 2️⃣ Cluster alphabetisch
	  const clusterNames = Object.keys(groups).sort((a, b) => a.localeCompare(b));

	  // 3️⃣ Cluster-Boxen + alphabetisch sortierte KPIs
	  clusterNames.forEach(cluster => {
		const clusterBox = document.createElement("div");
		clusterBox.className = "cluster-box";

		const header = document.createElement("h3");
		header.textContent = cluster;
		clusterBox.appendChild(header);

		groups[cluster]
		  .slice()
		  .sort((a, b) => (a.title || "").localeCompare(b.title || ""))
		  .forEach(k => {
			const key = normalizeKeyFromTitle(k.title);
			const row = document.createElement("div");
			row.className = "kpi-row";
			row.innerHTML = `
			  <label for="prio_${key}">${k.title}</label>
			  <select id="prio_${key}">
				<option value="very_high">very high</option>
				<option value="high" selected>high</option>
				<option value="not_interested">not interested</option>
			  </select>
			`;
			clusterBox.appendChild(row);
		  });

		box.appendChild(clusterBox);
	  });

	  // 4️⃣ Buttons (zentriert)
	  const btnContainer = document.createElement("div");
	  btnContainer.id = "priority-buttons";
	  btnContainer.innerHTML = `
		<button id="calc-btn">Recalculate Ranking</button>
		<button id="reset-btn">Reset</button>
	  `;
	  box.appendChild(btnContainer);

	  // 5️⃣ Wiederherstellung & Events
	  loadWeightsFromLocal();
	  createInfoBox();
	  attachChangeListeners();

	  document.getElementById("calc-btn")?.addEventListener("click", recalcRanking);
	  document.getElementById("reset-btn")?.addEventListener("click", resetPriorities);
	}




// ---------- RESET ----------
function resetPriorities() {
  document.querySelectorAll("select[id^='prio_']").forEach(sel => {
    sel.value = "high";
  });
  saveWeightsToLocal();
  recalcRanking();
}

// ---------- CALCULATION ----------
function recalcRanking() {
  const weights = {};
  available.forEach(k => {
    if (k.sort === "neutral" || k.world_kpi === "e" || !k.title) return;
    const key = normalizeKeyFromTitle(k.title);
    const sel = document.getElementById(`prio_${key}`);
    const w = multipliers[(sel?.value) || "high"];
    weights[key] = w;
  });

  const filtered = overall.filter(e => !EXCLUDE_COUNTRIES.has(e.country));

  const globallyAvailableKPIs = new Set();
  overall.forEach(entry => {
    Object.entries(entry.ranks).forEach(([kpi, rank]) => {
      if (rank !== null && !isNaN(rank)) globallyAvailableKPIs.add(kpi);
    });
  });

  const prioritizedValidKPIs = Object.keys(weights).filter(
    k => weights[k] > 0 && globallyAvailableKPIs.has(k)
  );
  const prioritizedCount = prioritizedValidKPIs.length;

  const results = filtered.map(entry => {
    let sum = 0, used = 0;
    Object.entries(entry.ranks).forEach(([kpi, rank]) => {
      const w = weights[kpi];
      if (w > 0 && globallyAvailableKPIs.has(kpi)) {
        sum += rank * w;
        used++;
      }
    });

    const coverage = prioritizedCount > 0 ? used / prioritizedCount : 0;
    const meetsCoverage = coverage >= 0.6;
    const bonusFactor = 1 + coverage * 0.1;
    const score = meetsCoverage ? (sum / used) / bonusFactor : Infinity;
    return { ...entry, score, used_kpis: used, all_kpis: Object.keys(entry.ranks).length, coverage };
  });

  const sorted = results.filter(r => r.score < Infinity).sort((a, b) => a.score - b.score);
  sorted.forEach((r, i) => r.rank = i + 1);
  saveWeightsToLocal();
  renderTable(sorted);
  renderLegend(prioritizedCount);
  // 🩵 Layout-Fix: Falls Priority-Container unsichtbar oder leer wurde, neu sichtbar machen
  const box = document.getElementById("priority-container");
  if (box && box.offsetHeight === 0) {
    console.warn("Priority container collapsed – restoring visibility.");
    box.style.display = "flex";
    box.style.minHeight = "200px";
}
}



// ---------- TABLE (Improved Strong/Weak logic) ----------
function niceList(ids, n = 3) {
  return ids
    .slice(0, n)
    .map((id) => titleByFilename[id] || id)
    .join(", ");
}

// Hilfsfunktion: erkennt aus available_kpis.json, ob höhere Werte besser sind
function isHigherBetter(kpiKey) {
  const kpiMeta = available.find(
    (k) => normalizeKeyFromTitle(k.title) === kpiKey
  );
  if (!kpiMeta) return true; // Default: higher = better
  return (kpiMeta.sort || "higher") === "higher";
}

function renderTable(rows) {
  const tbody = document.querySelector("#overall-table tbody");
  tbody.innerHTML = "";

  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="3">No countries meet the data coverage requirement.</td></tr>`;
    return;
  }

  const last10 = rows.slice(-10).map((d) => d.country);
  const top10 = rows.slice(0, 10).map((d) => d.country);

  rows.forEach((r) => {
    const tr = document.createElement("tr");
    const cup =
      r.rank === 1
        ? "🥇"
        : r.rank === 2
        ? "🥈"
        : r.rank === 3
        ? "🥉"
        : r.rank;

    // sortiere KPIs nach Rang
    const sorted = Object.entries(r.ranks).sort((a, b) => a[1] - b[1]);

    const bestIds = [];
    const weakIds = [];

    // bewerte KPI korrekt je nach „higher“ oder „lower“
    sorted.forEach(([id, rank]) => {
      const highBetter = isHigherBetter(id);
      if (highBetter) {
        // niedriger Rang = gut
        bestIds.push(id);
      } else {
        // niedriger Rang = schlecht → gehört in Weak
        weakIds.unshift(id);
      }
    });

    const desc = `
      <div style="line-height:1.4;">
        <b>Strong in:</b> ${niceList(bestIds)}<br>
        <b>Weak in:</b> ${niceList(weakIds)}<br>
        <small>Evaluated: ${r.used_kpis} / ${r.all_kpis} KPIs · Score: ${r.score.toFixed(2)}</small>
      </div>
    `;

    tr.innerHTML = `<td>${cup}</td><td>${r.country}</td><td>${desc}</td>`;
    if (top10.includes(r.country)) tr.classList.add("top10");
    if (last10.includes(r.country)) tr.classList.add("flop10");
    tbody.appendChild(tr);
  });
}


// ---------- LEGEND & INFO (improved layout & clarity) ----------
function renderLegend(prioritizedCount) {
  let leg = document.getElementById("legend");
  if (!leg) {
    leg = document.createElement("div");
    leg.id = "legend";
    // 🔧 Legend unterhalb der Tabelle platzieren, nicht ans Ende des Body
	const table = document.getElementById("overall-table");
	table.insertAdjacentElement("afterend", leg);
  }

  // 🧩 Übersicht fehlender KPIs
  const missingList = missingKPIs.length
    ? `
      <div class="missing-kpis">
        <strong>📉 KPIs currently without country-level data:</strong><br>
        <span>${missingKPIs.join(", ")}</span>
      </div>`
    : "";

// 💬 Legendeninhalt
	leg.innerHTML = `
	  <div class="legend-block">
		<h3>📊 How the Overall Ranking Works</h3>
		<p>
		  Countries are ranked based on the <b>weighted average</b> of all selected KPIs.
		  Each KPI can be prioritized as <b>Very High</b>, <b>High</b>, or marked as <b>Not Interested</b>.
		</p>
		<ul>
		  <li>✅ Only KPIs with <b>real, country-level data</b> are included.</li>
		  <li>⚖️ A country must have data for at least <b>60 %</b> of prioritized KPIs to appear.</li>
		  <li>🥇 <span style="color:#d4af37;font-weight:bold;">Gold rows</span> = Top 10 countries</li>
		  <li>💔 <span style="color:#ff6f61;font-weight:bold;">Red rows</span> = Bottom 10 countries</li>
		</ul>

		<p>
		  <b>Calculation logic:</b><br>
		  <code>score = (Σ(rank × weight) / used KPIs) ÷ (1 + coverage × 0.1)</code><br>
		  Lower scores indicate better performance.<br>
		  A small bonus factor <code>(1 + coverage × 0.1)</code> rewards countries with more complete data coverage.
		</p>

		<p>
		  <b>${prioritizedCount}</b> KPIs with available data were included in this ranking.<br>
		  KPIs without data are automatically excluded from calculations.
		</p>

		${missingList}
	  </div>
	`;

}


// ---------- LOCAL STORAGE ----------
function saveWeightsToLocal() {
  const weights = {};
  document.querySelectorAll("select[id^='prio_']").forEach(sel => {
    weights[sel.id.replace("prio_", "")] = sel.value;
  });
  localStorage.setItem("realitycheck_weights", JSON.stringify(weights));
}
function loadWeightsFromLocal() {
  try {
    const stored = localStorage.getItem("realitycheck_weights");
    if (!stored) return;
    const weights = JSON.parse(stored);
    Object.entries(weights).forEach(([kpi, val]) => {
      const sel = document.getElementById(`prio_${kpi}`);
      if (sel) sel.value = val;
    });
  } catch (err) { console.warn("Local weights could not be loaded:", err); }
}

// ---------- INFO BOX (GDPR NOTICE) ----------
function createInfoBox() {
  if (document.getElementById("localinfo-box")) return;
  const box = document.createElement("div");
  box.id = "localinfo-box";
  box.innerHTML = `
    <strong>ℹ️ Info:</strong> Your weighting settings are stored <b>locally</b> in your browser.<br>
    No cookies and no data are sent anywhere.
    <button id="close-localinfo">×</button>
  `;
  document.body.appendChild(box);
  const closeBtn = box.querySelector("#close-localinfo");
  if (closeBtn) {
    closeBtn.addEventListener("click", () => box.style.display = "none");
}

}
function attachChangeListeners() {
  document.querySelectorAll("select[id^='prio_']").forEach(sel => {
    sel.addEventListener("change", () => {
      const box = document.getElementById("localinfo-box");
      if (box && box.style.display !== "block") box.style.display = "block";
    });
  });
}

// ---------- LAST UPDATED ----------
async function fetchLastUpdated() {
  try {
    const resp = await fetch("data/fetch_status.json");
    if (!resp.ok) return;
    const json = await resp.json();
    if (json.last_fetch) {
      document.getElementById("last-updated").textContent =
        "Last data update: " + new Date(json.last_fetch).toLocaleDateString();
    }
  } catch { /* ignore */ }
}

// ---------- INIT ----------
window.addEventListener("DOMContentLoaded", loadData);
