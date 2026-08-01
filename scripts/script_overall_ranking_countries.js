/* ============================================================
   🌍 RealityCheck – Overall Country Ranking Script (Final 2025-10)
   ============================================================ */

let kpis = [];
let countries = [];
let missingKPIs = [];
let ALL_DATA = {}; // consolidated dataset from all_kpis_data.json
let FUN_SET = new Set();
let SAFE_SET = new Set();
let IMMIG_SET = new Set();
let FUN_BOTTOM_SET = new Set();
let SAFE_BOTTOM_SET = new Set();
let IMMIG_BOTTOM_SET = new Set();
let FUN_RANKING = [];
let SAFE_RANKING = [];
let IMMIG_RANKING = [];
let FUN_BOTTOM_RANKING = [];
let SAFE_BOTTOM_RANKING = [];
let IMMIG_BOTTOM_RANKING = [];
let CURRENT_OVERALL_RESULTS = [];
let funOn = false;
let safeOn = false;
let immigrOn = false;

const RELEVANCE_WEIGHTS = {
  very_high: 1.0,
  high: 0.7,
  normal: 0.4,
  low: 0.2,
  irrelevant: 0.0
};

const EXCLUDE_COUNTRIES = new Set(["World"]);
const OVERALL_WEIGHTS_STORAGE_KEY = "overallKPIWeightsV3";


/* ---------- Init ---------- */
async function initOverall() {
  showSpinner(true, "Building Overall Ranking…");
  try {
    if (typeof window.loadAllKPIData !== "function") {
      throw new Error("Consolidated KPI loader is unavailable");
    }
    [kpis, countries, ALL_DATA] = await Promise.all([
      loadJSON("data/meta/available_kpis.json"),
      loadJSON("data/meta/countries.json"),
      window.loadAllKPIData()
    ]);
    kpis = (Array.isArray(kpis) ? kpis : []).filter(kpi => kpi.publication_status !== "pending_first_fetch");

    buildRelevanceControls();
	  await buildOverallRanking();
    await loadFunSafeImmigrationSets();
    updateModeIcons();
    fetchLastUpdated();
  } catch (error) {
    console.error("Overall ranking initialization failed:", error);
    const status = document.getElementById("last-updated");
    if (status) {
      status.textContent = "The ranking could not be loaded. Please try again.";
      status.classList.add("table-status--error");
    }
  } finally {
    showSpinner(false);
  }
}
// ============================================================
// 🌈 Mode Switch (Normal / Fun / Safe Haven / Immigration)
// ============================================================
function initModeSwitch() {
  if (document.getElementById("mode-switch-initialized")) return;
  const marker = document.createElement("div");
  marker.id = "mode-switch-initialized";
  document.body.appendChild(marker);

  // Buttons
  const normalBtn = document.getElementById("normalMode");
  const funBtn    = document.getElementById("funMode");
  const safeBtn   = document.getElementById("safeMode");
  const immigrBtn = document.getElementById("immigrationMode");

  if (!normalBtn || !funBtn || !safeBtn || !immigrBtn) {
    console.warn("⚠️ Mode buttons not found");
    return;
  }

  // Reset shared mode state before wiring the controls.
  funOn = false;
  safeOn = false;
  immigrOn = false;
  updateModeIcons();

  // === Helper ===
  const updateLabel = (btn, text) => {
    const spans = btn.querySelectorAll("span");
    if (spans[1]) spans[1].textContent = text;
  };

  const activateMode = mode => {
    funOn = mode === "fun";
    safeOn = mode === "safe";
    immigrOn = mode === "immigration";
    updateLabel(funBtn, "Fun");
    updateLabel(safeBtn, "Safe");
    updateLabel(immigrBtn, "Immigration");
    if (funOn) updateLabel(funBtn, "Fun Mode activated");
    if (safeOn) updateLabel(safeBtn, "Safe Haven activated");
    if (immigrOn) updateLabel(immigrBtn, "Immigration activated");
    updateModeIcons();
  };

  // The modes are alternative analytical lenses. The underlying Overall score
  // always remains the KPI selection calculated from the list boxes.
  normalBtn.addEventListener("click", () => activateMode("normal"));

  // === Fun toggle ===
  funBtn.addEventListener("click", () => {
    activateMode("fun");
  });

  // === Safe toggle ===
  safeBtn.addEventListener("click", () => {
    activateMode("safe");
  });

  // === Immigration toggle ===
  immigrBtn.addEventListener("click", () => {
    activateMode("immigration");
  });
}

if (typeof onDocumentReady === "function") {
  onDocumentReady(initModeSwitch);
} else {
  document.addEventListener("DOMContentLoaded", initModeSwitch);
}



/* ---------- Build KPI Cluster Boxes ---------- */
function buildRelevanceControls() {
  const container = document.getElementById("priority-container");
  container.innerHTML = "";

  const relevantGroups = groupKpisByCluster(kpis, {
    filter: k =>
      ["higher", "lower", "target"].includes(k.sort) &&
      k.world_kpi !== "e" &&
      (k.relevance ?? "normal") !== "none",
    itemSorter: (a, b) => (a.title || "").localeCompare(b.title || "")
  });

  for (const [clusterName, list] of relevantGroups) {
    const group = document.createElement("div");
    group.className = "cluster-box";
    const h3 = document.createElement("h3");
    h3.textContent = clusterName;
    group.appendChild(h3);

    list.forEach(meta => {
      const row = document.createElement("div");
      row.className = "kpi-row";
      const label = document.createElement("label");
      label.textContent = meta.title + ": ";

      const sel = document.createElement("select");
      ["very_high", "high", "normal", "low", "irrelevant"].forEach(opt => {
        const o = document.createElement("option");
        o.value = opt;
        o.textContent = opt.replace("_", " ");
        if (opt === (meta.relevance || "normal")) o.selected = true;
        sel.appendChild(o);
      });

      sel.dataset.kpi = meta.filename;
      row.appendChild(label);
      row.appendChild(sel);
      group.appendChild(row);
    });

    container.appendChild(group);
  }

  // Buttons
  const btnBox = document.getElementById("priority-buttons");
  btnBox.innerHTML = `
    <button id="calc-btn">Calculate</button>
    <button id="reset-btn">Reset</button>
  `;

  // Restore saved weights
  let saved = null;
  try { saved = localStorage.getItem(OVERALL_WEIGHTS_STORAGE_KEY); } catch { /* storage unavailable */ }
  if (saved) {
    try {
      const map = JSON.parse(saved);
      for (const meta of kpis) {
        if (map[meta.filename]) meta.relevance = map[meta.filename];
        const sel = container.querySelector(`select[data-kpi="${meta.filename}"]`);
        if (sel && map[meta.filename]) sel.value = map[meta.filename];
      }
    } catch {
      localStorage.removeItem(OVERALL_WEIGHTS_STORAGE_KEY);
    }
  }

  // Events
  document.getElementById("reset-btn").addEventListener("click", () => {
    localStorage.removeItem(OVERALL_WEIGHTS_STORAGE_KEY);
    location.reload();
  });

	// === Änderungen an Gewichtungen überwachen ===
	container.querySelectorAll("select").forEach(sel => {
		sel.addEventListener("change", () => {
			hasChangedSinceLastCalc = true;
		});
	});

	// === Calculate-Button: Ranking + GDPR-Popup nur bei echten Änderungen ===
	document.getElementById("calc-btn").addEventListener("click", async () => {
		const button = document.getElementById("calc-btn");
		button.disabled = true;
		button.setAttribute("aria-busy", "true");
		try {
			for (const meta of kpis) {
				const sel = container.querySelector(`select[data-kpi="${meta.filename}"]`);
				if (sel) meta.relevance = sel.value;
			}

				localStorage.setItem(
					OVERALL_WEIGHTS_STORAGE_KEY,
				JSON.stringify(Object.fromEntries(kpis.map(m => [m.filename, m.relevance || "normal"])))
			);
			showToast("KPI selection saved");

			if (hasChangedSinceLastCalc) {
				createInfoBox();
				hasChangedSinceLastCalc = false;
			}
			await buildOverallRanking();
		} finally {
			button.disabled = false;
			button.setAttribute("aria-busy", "false");
		}
	});

}

/* ---------- Build Overall Ranking ---------- */
async function buildOverallRanking() {
  const valid = kpis.filter(
    k =>
      ["higher", "lower", "target"].includes(k.sort) &&
      k.world_kpi !== "e" &&
      (k.relevance ?? "normal") !== "none"
  );

  const aggregated = {};
  missingKPIs = [];
  const countryNames = new Set(Array.isArray(countries) ? countries : Object.keys(countries || {}));
  const totalWeight = valid.reduce((sum, meta) => sum + getRelevanceWeight(meta.relevance), 0);

  for (const meta of valid) {
    const id = meta.filename;
    const weight = getRelevanceWeight(meta.relevance);
    try {
      const data = ALL_DATA[id] || [];
      if (!Array.isArray(data) || data.length === 0) continue;

      const numeric = data.filter(d => countryNames.has(d.country) && !isNaN(parseFloat(d.value)));
      if (numeric.length < 2) continue;

      // pro Land neuestes Jahr
      const latestByCountry = new Map();
      for (const d of numeric) {
        if (!d.country) continue;
        const prev = latestByCountry.get(d.country);
        if (!prev || (d.year ?? -Infinity) > (prev.year ?? -Infinity))
          latestByCountry.set(d.country, d);
      }
      const latest = Array.from(latestByCountry.values());
      if (latest.length < 2) continue;

      const target = Number(meta.target_value);
      const scoredValues = latest.map(d => {
        const value = parseFloat(d.value);
        return meta.sort === "target" && Number.isFinite(target) ? Math.abs(value - target) : value;
      });
      const sorted = [...scoredValues].sort((a, b) => a - b);
      const percentileByValue = new Map();
      for (let i = 0; i < sorted.length;) {
        let end = i;
        while (end + 1 < sorted.length && sorted[end + 1] === sorted[i]) end++;
        percentileByValue.set(sorted[i], sorted.length === 1 ? 0.5 : ((i + end) / 2) / (sorted.length - 1));
        i = end + 1;
      }

      for (let index = 0; index < latest.length; index++) {
        const d = latest[index];
        const c = d.country;
        let norm = percentileByValue.get(scoredValues[index]) ?? 0.5;
        if (meta.sort === "lower" || meta.sort === "target") norm = 1 - norm;
        const val = norm * weight;

        if (!aggregated[c]) aggregated[c] = { sum: 0, count: 0, weightSum: 0 };
        aggregated[c].sum += val;
        aggregated[c].count++;
        aggregated[c].weightSum += weight;
      }
    } catch (e) {
      console.warn(`⚠️ KPI ${id} failed:`, e);
      missingKPIs.push(meta.title);
    }
  }

  const prioritizedCount = valid.length;

  const list = Object.entries(aggregated)
    .map(([country, obj]) => ({
      country,
      // base score = Ø of weighted KPIs; final score rewards data coverage
      baseScore: obj.weightSum > 0 ? obj.sum / obj.weightSum : 0,
      used: obj.count,
      coverage: totalWeight ? obj.weightSum / totalWeight : 0
    }))
    .filter(r => r.coverage >= 0.6); // Mindestabdeckung 60 %

  list.forEach(entry => {
    entry.score = entry.baseScore * entry.coverage; // penalize gaps in KPI coverage
  });

  list.sort((a, b) => b.score - a.score);
  CURRENT_OVERALL_RESULTS = list;

  renderOverallTable(list);
  renderLegend(prioritizedCount, missingKPIs);
  initModeSwitch();          // Buttons sicher initialisieren (einmalig)
  updateModeIcons();         // Icons gemäß aktuellem Toggle-Status (Default: aus)


}
// === Lädt Top-/Bottom-20-Sets einmal (robust gegen ältere JSON-Formate) ===
async function loadFunSafeImmigrationSets() {
  try {
    const [funRaw, funBottomRaw, safeRaw, safeBottomRaw, immigrRaw, immigrBottomRaw] = await Promise.all([
      fetch("data/fun_ranking.json?v=20260801-ranking-2").then(r => r.ok ? r.json() : []),
      fetch("data/fun_ranking_bottom.json?v=20260801-ranking-2").then(r => r.ok ? r.json() : []),
      fetch("data/safe_haven_ranking.json?v=20260801-ranking-2").then(r => r.ok ? r.json() : []),
      fetch("data/safe_haven_ranking_bottom.json?v=20260801-ranking-2").then(r => r.ok ? r.json() : []),
      fetch("data/immigration_ranking.json?v=20260801-ranking-2").then(r => r.ok ? r.json() : []),
      fetch("data/immigration_ranking_bottom.json?v=20260801-ranking-2").then(r => r.ok ? r.json() : [])
    ]);

    const funList = Array.isArray(funRaw)
      ? funRaw
      : funRaw["Fun Ranking"] || funRaw.countries || Object.values(funRaw);

    const safeList = Array.isArray(safeRaw)
      ? safeRaw
      : safeRaw["Safe Haven Ranking"] || safeRaw.countries || Object.values(safeRaw);

    const immigrList = Array.isArray(immigrRaw)
      ? immigrRaw
      : immigrRaw["Immigration Mode"] || immigrRaw.countries || Object.values(immigrRaw);

    const funBottomList = Array.isArray(funBottomRaw) ? funBottomRaw : Object.values(funBottomRaw);
    const safeBottomList = Array.isArray(safeBottomRaw) ? safeBottomRaw : Object.values(safeBottomRaw);
    const immigrBottomList = Array.isArray(immigrBottomRaw) ? immigrBottomRaw : Object.values(immigrBottomRaw);

    FUN_RANKING = (funList || []).slice(0, 20);
    SAFE_RANKING = (safeList || []).slice(0, 20);
    IMMIG_RANKING = (immigrList || []).slice(0, 20);
    FUN_SET = new Set(FUN_RANKING.map(e => e.country || e));
    SAFE_SET = new Set(SAFE_RANKING.map(e => e.country || e));
    IMMIG_SET = new Set(IMMIG_RANKING.map(e => e.country || e));
    // Fail safely for older generated artifacts: never label one country as both
    // a strongest and weakest match while a clean regeneration is pending.
    FUN_BOTTOM_RANKING = (funBottomList || []).filter(e => !FUN_SET.has(e.country || e)).slice(0, 20);
    SAFE_BOTTOM_RANKING = (safeBottomList || []).filter(e => !SAFE_SET.has(e.country || e)).slice(0, 20);
    IMMIG_BOTTOM_RANKING = (immigrBottomList || []).filter(e => !IMMIG_SET.has(e.country || e)).slice(0, 20);
    FUN_BOTTOM_SET = new Set(FUN_BOTTOM_RANKING.map(e => e.country || e));
    SAFE_BOTTOM_SET = new Set(SAFE_BOTTOM_RANKING.map(e => e.country || e));
    IMMIG_BOTTOM_SET = new Set(IMMIG_BOTTOM_RANKING.map(e => e.country || e));

    console.log("😎 FUN_SET loaded:", [...FUN_SET]);
    console.log("🛡️ SAFE_SET loaded:", [...SAFE_SET]);
    console.log("🧳 IMMIG_SET loaded:", [...IMMIG_SET]);
  } catch (e) {
    console.warn("⚠️ Could not load fun/safe/immigration sets:", e);
    FUN_SET = new Set();
    SAFE_SET = new Set();
    IMMIG_SET = new Set();
    FUN_BOTTOM_SET = new Set();
    SAFE_BOTTOM_SET = new Set();
    IMMIG_BOTTOM_SET = new Set();
    FUN_RANKING = [];
    SAFE_RANKING = [];
    IMMIG_RANKING = [];
    FUN_BOTTOM_RANKING = [];
    SAFE_BOTTOM_RANKING = [];
    IMMIG_BOTTOM_RANKING = [];
  }
}


// === Fügt/entfernt ausschließlich die Icons gemäß funOn/safeOn ===
function updateModeIcons() {
  const states = {
    normalMode: !funOn && !safeOn && !immigrOn,
    funMode: Boolean(funOn),
    safeMode: Boolean(safeOn),
    immigrationMode: Boolean(immigrOn)
  };
  Object.entries(states).forEach(([id, active]) => {
    const button = document.getElementById(id);
    if (!button) return;
    button.setAttribute("aria-pressed", active ? "true" : "false");
    button.classList.toggle("active", active);
  });
  document.querySelectorAll("#overall-table tbody tr").forEach(tr => {
    const nameCell = tr.children[1];
    if (!nameCell) return;

    // alte Icons entfernen
    nameCell.querySelectorAll(".mode-icons").forEach(n => n.remove());

    const country = nameCell.textContent.trim();
    let icons = "";
    let iconLabel = "";
    if (funOn && FUN_SET.has(country)) { icons = "😎"; iconLabel = "Fun Top 20"; }
    if (funOn && FUN_BOTTOM_SET.has(country)) { icons = "☔"; iconLabel = "Fun Bottom 20"; }
    if (safeOn && SAFE_SET.has(country)) { icons = "🛡️"; iconLabel = "Safe Haven Top 20"; }
    if (safeOn && SAFE_BOTTOM_SET.has(country)) { icons = "💥"; iconLabel = "Safe Haven Bottom 20"; }
	if (immigrOn && IMMIG_SET.has(country)) { icons = "🧳"; iconLabel = "Immigration Top 20"; }
	if (immigrOn && IMMIG_BOTTOM_SET.has(country)) { icons = "🚧"; iconLabel = "Immigration Bottom 20"; }

    if (icons) {
      const span = document.createElement("span");
      span.className = "mode-icons";
      span.textContent = " " + icons;
      span.title = iconLabel;
      span.setAttribute("aria-label", iconLabel);
      nameCell.appendChild(span);
    }
  });
  renderModeAnalysis();
}

function getActiveMode() {
  if (funOn) return "fun";
  if (safeOn) return "safe";
  if (immigrOn) return "immigration";
  return "normal";
}

function appendAnalysisHeading(container, title, text) {
  const heading = document.createElement("h2");
  heading.textContent = title;
  container.appendChild(heading);
  const description = document.createElement("p");
  description.textContent = text;
  container.appendChild(description);
}

function renderModeAnalysis() {
  const container = document.getElementById("mode-analysis");
  if (!container) return;
  container.textContent = "";
  const mode = getActiveMode();

  if (mode === "normal") {
    appendAnalysisHeading(
      container,
      "⚙️ Standard Overall analysis",
      "This is the primary, data-driven scenario. Its country order is calculated from your current KPI list-box weights; no editorial mode changes that score."
    );
    const priorities = kpis
      .filter(meta => ["very_high", "high"].includes(meta.relevance))
      .map(meta => meta.title)
      .slice(0, 8);
    const priorityText = document.createElement("p");
    priorityText.className = "mode-analysis__note";
    priorityText.textContent = priorities.length
      ? `Strongest selected priorities: ${priorities.join(", ")}${priorities.length === 8 ? " …" : ""}`
      : "No high-priority KPI is currently selected.";
    container.appendChild(priorityText);

    if (CURRENT_OVERALL_RESULTS.length) {
      const list = document.createElement("ol");
      list.className = "mode-analysis__ranking mode-analysis__ranking--compact";
      CURRENT_OVERALL_RESULTS.slice(0, 3).forEach(entry => {
        const item = document.createElement("li");
        item.textContent = `${entry.country}: ${(entry.score * 100).toFixed(2)} points, ${(entry.coverage * 100).toFixed(0)}% weighted data coverage`;
        list.appendChild(item);
      });
      container.appendChild(list);
    }
    return;
  }

  const configs = {
    fun: {
      title: "😎 Fun lens",
      text: "A deliberately light-hearted editorial lens combining measured quality of life with qualitative context such as climate, sunshine, social life, beer affordability and appealing cities.",
      bottomNote: "Its Bottom list measures weak living-condition fit from KPI evidence; it does not judge whether a culture or its people are fun.",
      topData: FUN_RANKING,
      bottomData: FUN_BOTTOM_RANKING,
      topIcon: "😎",
      bottomIcon: "☔"
    },
    safe: {
      title: "🛡️ Safe Haven lens",
      text: "An editorial risk lens covering domestic safety, climate effects and resilience, conflict proximity, spillover exposure, geography and alliances. It is not a prediction of war.",
      bottomNote: "Its Bottom list is a reproducible measured-risk ranking anchored in the Global Peace Index, not a model-selected narrative shortlist.",
      topData: SAFE_RANKING,
      bottomData: SAFE_BOTTOM_RANKING,
      topIcon: "🛡️",
      bottomIcon: "💥"
    },
    immigration: {
      title: "🧳 Immigration lens",
      text: "An editorial relocation lens combining destination quality with cautious consideration of visa, work-permit and residence accessibility. It is not legal advice.",
      bottomNote: "Its Bottom list describes comparative access barriers and destination conditions, not immigrants or a country's population.",
      topData: IMMIG_RANKING,
      bottomData: IMMIG_BOTTOM_RANKING,
      topIcon: "🧳",
      bottomIcon: "🚧"
    }
  };
  const config = configs[mode];
  appendAnalysisHeading(container, config.title, config.text);

  const note = document.createElement("p");
  note.className = "mode-analysis__note";
  note.textContent = `${config.bottomNote} These lists do not replace your KPI-weighted Overall ranking.`;
  container.appendChild(note);

  if (!config.topData.length && !config.bottomData.length) {
    const unavailable = document.createElement("p");
    unavailable.textContent = "This analytical lens is currently unavailable.";
    container.appendChild(unavailable);
    return;
  }

  const overallRank = new Map(CURRENT_OVERALL_RESULTS.map((entry, index) => [entry.country, index + 1]));
  appendLensRanking(container, `${config.topIcon} Top ${config.topData.length}`, config.topData, overallRank, true, "strongest");
  appendLensRanking(container, `${config.bottomIcon} Bottom ${config.bottomData.length}`, config.bottomData, overallRank, false, "weakest");
}

function appendLensRanking(container, title, data, overallRank, open, rankMeaning) {
  const details = document.createElement("details");
  details.className = "mode-analysis__details";
  details.open = open;
  const summary = document.createElement("summary");
  summary.textContent = `${title} — rank 1 is the ${rankMeaning} match`;
  details.appendChild(summary);
  if (!data.length) {
    const unavailable = document.createElement("p");
    unavailable.textContent = "This list is currently unavailable.";
    details.appendChild(unavailable);
    container.appendChild(details);
    return;
  }
  const list = document.createElement("ol");
  list.className = "mode-analysis__ranking";
  data.forEach((entry, index) => {
    const country = entry.country || entry;
    const item = document.createElement("li");
    const heading = document.createElement("strong");
    const standardRank = overallRank.get(country);
    heading.textContent = `${country}${standardRank ? ` — Overall #${standardRank}` : ""}`;
    item.appendChild(heading);
    if (entry.reason) {
      const reason = document.createElement("span");
      reason.textContent = ` ${entry.reason}`;
      item.appendChild(reason);
    }
    if (Number.isInteger(entry.rank) && entry.rank !== index + 1) item.value = entry.rank;
    list.appendChild(item);
  });
  details.appendChild(list);
  container.appendChild(details);
}


/* ---------- Weight Helper ---------- */
function getRelevanceWeight(r) {
  return RELEVANCE_WEIGHTS[r] ?? 0.4;
}

/* ---------- Render Table ---------- */
function renderOverallTable(list) {
  const tbody = document.querySelector("#overall-table tbody");
  if (!tbody) return;
  tbody.textContent = "";

  if (!list.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 4;
    td.textContent = "No countries meet the 60 % data coverage requirement.";
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  const total = list.length;
  list.forEach((entry, i) => {
    const rank = i + 1;
    const medal = rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : rank;
    const tr = document.createElement("tr");

    const rankCell = document.createElement("td");
    rankCell.textContent = medal;
    tr.appendChild(rankCell);

    const countryCell = document.createElement("td");
    countryCell.textContent = entry.country;
    tr.appendChild(countryCell);

    const scoreCell = document.createElement("td");
    scoreCell.textContent = (entry.score * 100).toFixed(2);
    tr.appendChild(scoreCell);

    const usedCell = document.createElement("td");
    usedCell.textContent = entry.used;
    tr.appendChild(usedCell);

    if (rank <= 10) tr.classList.add("top10");
    if (rank > total - 10) tr.classList.add("flop10");
    tbody.appendChild(tr);
  });

  const lastUpdated = document.getElementById("last-updated");
  if (lastUpdated) {
    const d = new Date();
    lastUpdated.textContent = "Last calculated: " + d.toISOString().slice(0, 10);
  }
}
/* ---------- Legend (unter Tabelle) ---------- */
function renderLegend(prioritizedCount, missing = []) {
  let leg = document.getElementById("legend");
  const table = document.getElementById("overall-table");
  const wrapper = table?.closest(".table-wrapper");

  if (!leg) {
    leg = document.createElement("div");
    leg.id = "legend";
    if (wrapper) {
      wrapper.insertAdjacentElement("afterend", leg);
    } else if (table) {
      table.insertAdjacentElement("afterend", leg);
    }
  } else if (wrapper && leg.parentElement !== wrapper.parentElement) {
    wrapper.insertAdjacentElement("afterend", leg);
  }

  const escapeValue =
    typeof window !== "undefined" && typeof window.escapeHTML === "function"
      ? window.escapeHTML
      : value => (value ?? "").toString();

  const missingList = missing.length
    ? `<div class="missing-kpis"><strong>📉 KPIs currently without country-level data:</strong><br><span>${missing
        .map(item => escapeValue(item))
        .join(", ")}</span></div>`
    : "";

  leg.innerHTML = `
    <div class="legend-block">
      <h3>📊 How the Overall Ranking Works</h3>
      <p>
        For each KPI the <b>latest country value</b> is converted to a robust percentile score in <code>[0,1]</code>:
      </p>
      <pre class="legend-code">
norm = percentile_rank(value)
if sort == "lower": norm = 1 - norm
if sort == "target": norm = 1 - percentile_rank(abs(value - target))
weighted = norm × relevance_weight
base_score(country) = Σ(weighted) / Σ(available KPI weights)
weighted_coverage = Σ(available KPI weights) / Σ(all selected KPI weights)
score(country) = base_score × weighted_coverage
      </pre>
      <ul>
        <li>🚫 Only indicators that make sense for such comparison are included.</li>
        <li>⚖️ Only countries with <b>≥ 60 %</b> KPI coverage appear in the ranking, and coverage reduces the final score.</li>
        <li>🥇 Top 10 rows highlighted green 💔 Bottom 10 red</li>
      </ul>
      <p><b>${prioritizedCount}</b> KPIs with data included in calculation.</p>
      ${missingList}
    </div>

    <div class="legend-block">
      <h3>🌍 Mode Highlights</h3>
      <p><strong>😎 / ☔ Fun Mode:</strong> Top and Bottom 20 for a light-hearted “cool place to live” view combining happiness and quality of life with sunshine, climate, affordable beer and recognised liveable cities.</p>
      <p><strong>🛡️ / 💥 Safe Haven Mode:</strong> Top and Bottom 20 for domestic safety and resilience plus climate effects, conflict proximity and alliance exposure.</p>
	  <p><strong>🧳 / 🚧 Immigration Mode:</strong> Top and Bottom 20 for destination attractiveness and comparatively accessible visa, work-permit and residence paths. It is orientation, not individual legal advice.</p>
    <p><strong>! Feature disabled while Google Translate is on! Switch to the original version to continue !  </strong> </p>
    </div>
  `;
}
/* ---------- Info Box (GDPR notice – show only after Calculate if changed) ---------- */
let hasChangedSinceLastCalc = false;

function createInfoBox() {
  // Bestehende Box wiederverwenden, falls sie noch da ist
  let box = document.getElementById("localinfo-box");
  if (!box) {
    box = document.createElement("div");
    box.id = "localinfo-box";
    box.innerHTML = `
      <strong>ℹ️ Info:</strong> Your weighting settings are stored <b>locally</b> in your browser.<br>
      No cookies and no data are sent anywhere.
      <button id="close-localinfo">×</button>
    `;
    document.body.appendChild(box);
    box.querySelector("#close-localinfo")?.addEventListener("click", () => box.remove());
  }

  // Sanft einblenden (zentriert)
  requestAnimationFrame(() => box.classList.add("show"));

  // Langsamer ausblenden (nach 4 s sichtbar, danach 5 s Fade)
  clearTimeout(box._timeout);
  box._timeout = setTimeout(() => box.classList.remove("show"), 4000);
  setTimeout(() => box.remove(), 5000);
}


/* ---------- Last Updated ---------- */
async function fetchLastUpdated() {
  try {
    const r = await fetch("data/fetch_status.json");
    if (!r.ok) return;
    const j = await r.json();
    if (j.last_fetch)
      document.getElementById("last-updated").textContent =
        "Last data update: " + new Date(j.last_fetch).toLocaleDateString();
  } catch {}
}

/* ---------- Start ---------- */
if (typeof onDocumentReady === "function") {
  onDocumentReady(initOverall);
} else {
  window.addEventListener("DOMContentLoaded", initOverall);
}
