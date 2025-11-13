/* ============================================================
   🌍 RealityCheck – Overall Country Ranking Script (Final 2025-10)
   ============================================================ */

let kpis = [];
let countries = [];
let missingKPIs = [];
let ALL_DATA = {}; // consolidated dataset from all_kpis_data.json

const RELEVANCE_WEIGHTS = {
  very_high: 1.0,
  high: 0.7,
  normal: 0.4,
  low: 0.2,
  irrelevant: 0.0
};

const EXCLUDE_COUNTRIES = new Set(["World"]);


/* ---------- Init ---------- */
async function initOverall() {
  showSpinner(true, "Building Overall Ranking…");

  kpis = await loadJSON("data/meta/available_kpis.json");
  countries = await loadJSON("data/meta/countries.json");
  ALL_DATA = await loadAllKPIData(); // ✅ consolidated dataset

  buildRelevanceControls();
	await buildOverallRanking();   // 🧩 Ranking berechnen und Tabelle rendern
  await loadFunSafeImmigrationSets();

  showSpinner(false);
  fetchLastUpdated();
  
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

  // === Global-State benutzen (nicht lokale let!) ===
  window.funOn = false;
  window.safeOn = false;
  window.immigrOn = false;

  // === Helper ===
  const updateLabel = (btn, text) => {
    const spans = btn.querySelectorAll("span");
    if (spans[1]) spans[1].textContent = text;
  };

  // === Reset ===
  normalBtn.addEventListener("click", () => {
    document.querySelectorAll("#mode-switch button").forEach(b => b.classList.remove("active"));
    normalBtn.classList.add("active");

    funOn = safeOn = immigrOn = false;
    updateLabel(funBtn, "Fun");
    updateLabel(safeBtn, "Safe");
    updateLabel(immigrBtn, "Immigration");

    updateModeIcons();
  });

  // === Fun toggle ===
  funBtn.addEventListener("click", () => {
    funOn = !funOn;
    funBtn.classList.toggle("active", funOn);
    updateLabel(funBtn, funOn ? "Fun Mode activated" : "Fun");
    updateModeIcons();
  });

  // === Safe toggle ===
  safeBtn.addEventListener("click", () => {
    safeOn = !safeOn;
    safeBtn.classList.toggle("active", safeOn);
    updateLabel(safeBtn, safeOn ? "Safe Haven activated" : "Safe");
    updateModeIcons();
  });

  // === Immigration toggle ===
  immigrBtn.addEventListener("click", () => {
    immigrOn = !immigrOn;
    immigrBtn.classList.toggle("active", immigrOn);
    updateLabel(immigrBtn, immigrOn ? "Immigration activated" : "Immigration");
    updateModeIcons();
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
  const saved = localStorage.getItem("overallKPIWeights");
  if (saved) {
    const map = JSON.parse(saved);
    for (const meta of kpis) {
      if (map[meta.filename]) meta.relevance = map[meta.filename];
      const sel = container.querySelector(`select[data-kpi="${meta.filename}"]`);
      if (sel && map[meta.filename]) sel.value = map[meta.filename];
    }
  }

  // Events
  document.getElementById("calc-btn").addEventListener("click", async () => {
    for (const meta of kpis) {
      const sel = container.querySelector(`select[data-kpi="${meta.filename}"]`);
      if (sel) meta.relevance = sel.value;
    }
    localStorage.setItem(
      "overallKPIWeights",
      JSON.stringify(Object.fromEntries(kpis.map(m => [m.filename, m.relevance || "normal"])))
    );
    showToast("KPI selection saved");
    await buildOverallRanking();
  });

  document.getElementById("reset-btn").addEventListener("click", () => {
    localStorage.removeItem("overallKPIWeights");
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
		for (const meta of kpis) {
			const sel = container.querySelector(`select[data-kpi="${meta.filename}"]`);
			if (sel) meta.relevance = sel.value;
		}

		localStorage.setItem(
			"overallKPIWeights",
			JSON.stringify(Object.fromEntries(kpis.map(m => [m.filename, m.relevance || "normal"])))
		);

		showToast("KPI selection saved");

		// Nur zeigen, wenn etwas verändert wurde
		if (hasChangedSinceLastCalc) {
			createInfoBox();
			hasChangedSinceLastCalc = false;
		}

		await buildOverallRanking();
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

  for (const meta of valid) {
    const id = meta.filename;
    const weight = getRelevanceWeight(meta.relevance);
    try {
      const data = ALL_DATA[id] || [];
      if (!Array.isArray(data) || data.length === 0) continue;

      const numeric = data.filter(d => !isNaN(parseFloat(d.value)));
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

      const min = Math.min(...latest.map(d => parseFloat(d.value)));
      const max = Math.max(...latest.map(d => parseFloat(d.value)));
      const range = max - min || 1;

      for (const d of latest) {
        const c = d.country;
        let norm = (parseFloat(d.value) - min) / range;
        if (meta.sort === "lower") norm = 1 - norm;
        const val = norm * weight;

        if (!aggregated[c]) aggregated[c] = { sum: 0, count: 0 };
        aggregated[c].sum += val;
        aggregated[c].count++;
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
      score: obj.count > 0 ? obj.sum / obj.count : 0,
      used: obj.count,
      coverage: prioritizedCount ? obj.count / prioritizedCount : 0
    }))
    .filter(r => r.coverage >= 0.6); // Mindestabdeckung 60 %

  list.sort((a, b) => b.score - a.score);

  renderOverallTable(list);
  renderLegend(prioritizedCount, missingKPIs);
  initModeSwitch();          // Buttons sicher initialisieren (einmalig)
  updateModeIcons();         // Icons gemäß aktuellem Toggle-Status (Default: aus)


}
// === Global state ===
let FUN_SET = new Set();
let SAFE_SET = new Set();
let IMMIG_SET = new Set();  // 🧳 neu
let funOn = false;
let safeOn = false;
let immigrOn = false;       // 🧳 neu


// === Lädt Top-10 Sets EINMAL (robust gegen GPT-JSON-Formate) ===
async function loadFunSafeImmigrationSets() {
  try {
    const [funRaw, safeRaw, immigrRaw] = await Promise.all([
      fetch("data/fun_ranking.json").then(r => r.ok ? r.json() : []),
      fetch("data/safe_haven_ranking.json").then(r => r.ok ? r.json() : []),
      fetch("data/immigration_ranking.json").then(r => r.ok ? r.json() : []) // 🧳 neu
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

    FUN_SET = new Set((funList || []).slice(0, 10).map(e => e.country || e));
    SAFE_SET = new Set((safeList || []).slice(0, 10).map(e => e.country || e));
    IMMIG_SET = new Set((immigrList || []).slice(0, 10).map(e => e.country || e)); // 🧳 neu

    console.log("😎 FUN_SET loaded:", [...FUN_SET]);
    console.log("🛡️ SAFE_SET loaded:", [...SAFE_SET]);
    console.log("🧳 IMMIG_SET loaded:", [...IMMIG_SET]);
  } catch (e) {
    console.warn("⚠️ Could not load fun/safe/immigration sets:", e);
    FUN_SET = new Set();
    SAFE_SET = new Set();
    IMMIG_SET = new Set();
  }
}


// === Fügt/entfernt ausschließlich die Icons gemäß funOn/safeOn ===
function updateModeIcons() {
  document.querySelectorAll("#overall-table tbody tr").forEach(tr => {
    const nameCell = tr.children[1];
    if (!nameCell) return;

    // alte Icons entfernen
    nameCell.querySelectorAll(".mode-icons").forEach(n => n.remove());

    const country = nameCell.textContent.trim();
    let icons = "";
    if (funOn && FUN_SET.has(country)) icons += "😎";
    if (safeOn && SAFE_SET.has(country)) icons += "🛡️";
	if (immigrOn && IMMIG_SET.has(country)) icons += "🧳";

    if (icons) {
      const span = document.createElement("span");
      span.className = "mode-icons";
      span.textContent = " " + icons;
      nameCell.appendChild(span);
    }
  });
}


/* ---------- Weight Helper ---------- */
function getRelevanceWeight(r) {
  return RELEVANCE_WEIGHTS[r] ?? 0.4;
}

/* ---------- Render Table ---------- */
function renderOverallTable(list) {
  const tbody = document.querySelector("#overall-table tbody");
  tbody.innerHTML = "";

  if (!list.length) {
    tbody.innerHTML = `<tr><td colspan="4">No countries meet the 60 % data coverage requirement.</td></tr>`;
    return;
  }

  const total = list.length;
  list.forEach((entry, i) => {
    const rank = i + 1;
    const medal = rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : rank;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${medal}</td>
      <td>${entry.country}</td>
      <td>${(entry.score * 100).toFixed(2)}</td>
      <td>${entry.used}</td>
    `;
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
  if (!leg) {
    leg = document.createElement("div");
    leg.id = "legend";
    const table = document.getElementById("overall-table");
    table.insertAdjacentElement("afterend", leg);
  }

  const missingList = missing.length
    ? `<div class="missing-kpis"><strong>📉 KPIs currently without country-level data:</strong><br><span>${missing.join(
        ", "
      )}</span></div>`
    : "";

  leg.innerHTML = `
    <div class="legend-block">
      <h3>📊 How the Overall Ranking Works</h3>
      <p>
        For each KPI the <b>latest country value</b> is normalized to <code>[0,1]</code>:
      </p>
      <pre class="legend-code">
norm = (value - min) / (max - min)
if sort == "lower": norm = 1 - norm
weighted = norm × relevance_weight
score(country) = Σ(weighted) / KPIs_used
      </pre>
      <ul>
        <li>🚫 Only indicators that make sense for such comparison are included.</li>
        <li>⚖️ Only countries with <b>≥ 60 %</b> KPI coverage appear in the ranking.</li>
        <li>🥇 Top 10 rows highlighted green 💔 Bottom 10 red</li>
      </ul>
      <p><b>${prioritizedCount}</b> KPIs with data included in calculation.</p>
      ${missingList}
    </div>

    <div class="legend-block">
      <h3>🌍 Mode Highlights</h3>
      <p><strong>😎 Fun Mode:</strong> Warm, sunny, happy and relaxed. Good beer, reasonably priced</p>
      <p><strong>🛡️ Safe Haven Mode:</strong> Peaceful, resilient, and rights-respecting democracies with low climate risk.</p>
	  <p><strong>🧳 Immigration Mode:</strong> Countries open to immigration, with job opportunities and welcoming integration culture.</p>
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


/* ---------- Toast Helper (zentriert + Fade + Auto-hide) ---------- */
function showToast(msg) {
  // Reuse existing toast element if present
  let toast = document.getElementById("toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    document.body.appendChild(toast);

    // Basis-Styles (falls CSS fehlt oder noch nicht geladen)
    Object.assign(toast.style, {
      position: "fixed",
      top: "50%",
      left: "50%",
      transform: "translate(-50%, -50%) scale(0.9)",
      background: "rgba(0, 0, 0, 0.8)",
      color: "#fff",
      padding: "1rem 1.6rem",
      borderRadius: "10px",
      fontSize: "1rem",
      fontWeight: "500",
      boxShadow: "0 6px 18px rgba(0,0,0,0.35)",
      opacity: "0",
      transition: "opacity 0.4s ease, transform 0.4s ease",
      zIndex: "99999",
      pointerEvents: "none",
      textAlign: "center",
      maxWidth: "80%"
    });
  }

  // Aktualisieren und sichtbar machen
  toast.textContent = msg;
  toast.classList.add("show");

  // Animation: Fade-In
  requestAnimationFrame(() => {
    toast.style.opacity = "1";
    toast.style.transform = "translate(-50%, -50%) scale(1)";
  });

  // Automatisches Ausblenden nach 2.5 s
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translate(-50%, -50%) scale(0.9)";
    toast.classList.remove("show");
  }, 2500);
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
