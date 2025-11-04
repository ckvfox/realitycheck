/* ============================================================
   🌐 RealityCheck – Core Utilities (shared functions, 2025-10)
   ============================================================ */

// === Load JSON with cache-bypass & safe parse (FINAL FIX 2025-11-02) ===
async function loadJSON(path) {
  try {
    const res = await fetch(path + "?t=" + Date.now(), { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const txt = await res.text();
    if (!txt) return [];

    // 🔧 Sicherstellen, dass wir ein Objekt zurückgeben, kein String
    let parsed;
    try {
      parsed = JSON.parse(txt);
    } catch (err) {
      console.warn("⚠️ loadJSON: content not valid JSON → returning raw text", path);
      parsed = txt;
    }

    // 🩵 Falls JSON doppelt serialisiert war (z. B. als String mit {...})
    if (typeof parsed === "string" && parsed.trim().startsWith("{")) {
      try {
        parsed = JSON.parse(parsed);
        console.log("🧩 loadJSON reparsed nested JSON:", path);
      } catch {/* ignore */}
    }

    return parsed;
  } catch (e) {
    console.warn("⚠️ loadJSON failed:", path, e);
    return [];
  }
}

// === Spinner (zentriert + fade) ===
function showSpinner(show = true, msg = "Loading…") {
  const sp = document.getElementById("overlay-spinner");
  if (!sp) return;

  // Struktur bei erstem Aufruf automatisch einfügen
  if (!sp.dataset.init) {
    sp.innerHTML = `
      <div class="spinner-circle"></div>
      <p class="spinner-text"></p>
    `;
    sp.dataset.init = "1";
  }

  // Text aktualisieren
  const textEl = sp.querySelector(".spinner-text");
  if (textEl) textEl.textContent = msg || "Loading…";

  // Sichtbarkeit steuern mit Fade-Effekt
  if (show) {
    sp.classList.remove("hidden");
    sp.style.opacity = "1";

    // Spinner immer im sichtbaren Bereich halten (auch im iframe)
    try {
      window.scrollTo({ top: 0, behavior: "instant" });
    } catch {
      /* ignore */
    }
  } else {
    sp.style.opacity = "0";
    setTimeout(() => sp.classList.add("hidden"), 300);
  }
}



// === Normalize KPI/Country names ===
function normalizeName(str) {
  if (!str) return "";
  return str
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .replace(/co₂/g, "co2")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
}

// === Resolve country aliases (from meta mapping) ===
async function resolveCountryName(alias) {
  if (!window._countryMappings) {
    window._countryMappings = await loadJSON("data/meta/country_mappings.json");
  }
  const m = window._countryMappings || {};
  return m[alias] || alias;
}

// === Calculate aggregate group values ===
function calculateGroupValues(group, dataset) {
  if (!group?.members || !Array.isArray(dataset)) return null;
  const members = group.members;
  const records = dataset.filter(r => members.includes(r.country));
  if (!records.length) return null;
  const isRelative = records.some(r => String(r.unit || "").includes("%"));
  const val = isRelative
    ? records.reduce((a, r) => a + (r.value || 0), 0) / records.length
    : records.reduce((a, r) => a + (r.value || 0), 0);
  const year = Math.max(...records.map(r => r.year || 0));
  return { country: group.title || group.id, value: val, year };
}

// === Simple console logging helper ===
function rcLog(...msg) {
  console.log("🧭 RealityCheck:", ...msg);
}

/* ============================================================
   🧩 Consolidated KPI Loader (Split + Gzip Support, InfinityFree safe)
   ============================================================ */
async function loadAllKPIData() {
  try {
    const index = await loadJSON("data/all_kpis_index.json");
    if (!index || !index.parts) {
      console.warn("⚠️ No index found for split dataset.");
      return {};
    }

    rcLog(`Found ${index.parts.length} KPI data parts.`);

    const ALL_DATA = {};
    for (const part of index.parts) {
      const url = "data/" + part + "?t=" + Date.now();
      rcLog("⬇️ Loading", url);

      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status} on ${url}`);

      // 💡 Immer als Binärdaten laden
      const buffer = await response.arrayBuffer();
      const bytes = new Uint8Array(buffer);

      let text;
      try {
        // zuerst versuchen, als gzip zu entpacken
        text = pako.ungzip(bytes, { to: "string" });
      } catch {
        // falls kein gzip: normal decodieren
        text = new TextDecoder("utf-8").decode(bytes);
      }

      const json = JSON.parse(text);
      Object.assign(ALL_DATA, json);
    }

    rcLog(`✅ Loaded ${Object.keys(ALL_DATA).length} KPI datasets`);
    return ALL_DATA;

  } catch (e) {
    console.error("❌ Failed to load consolidated split data:", e);
    return {};
  }
}

// ============================================================
// 🧠 KPI Smart Analysis Loader (shared for all pages)
// ============================================================

const KPI_ANALYSIS_CACHE = {};

async function loadKpiAnalysis(metaOrId) {
  // --- Parameter normalisieren ---
  let key = null;
  if (!metaOrId) return "";
  if (typeof metaOrId === "string") key = metaOrId.replace(/\.json$/i, "");
  else if (metaOrId.filename) key = metaOrId.filename.replace(/\.json$/i, "");
  else return "";

  // --- Cache prüfen ---
  if (KPI_ANALYSIS_CACHE[key]) return KPI_ANALYSIS_CACHE[key];

  try {
    const res = await fetch("data/kpi_analysis.json?nocache=" + Date.now());
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const all = await res.json();
    const info = all[key];
    const summary = info?.summary || "";
    KPI_ANALYSIS_CACHE[key] = summary;
    return summary;
  } catch (err) {
    console.warn("⚠️ loadKpiAnalysis failed:", err);
    return "";
  }
}

/**
 * Rendert die KI-Analyse in ein Ziel-Element (z.B. #kpi-analysis)
 * @param {Object|string} metaOrId - KPI-Metaobjekt oder Dateiname
 * @param {string} targetId - Ziel-Element-ID
 */
async function renderKpiAnalysis(metaOrId, targetId = "kpi-analysis") {
  // 🕐 Warte bis das Ziel-Element im DOM verfügbar ist (max 1 Sekunde)
  let box = document.getElementById(targetId);
  let retries = 0;
  while (!box && retries < 10) {
    await new Promise(r => setTimeout(r, 100));
    box = document.getElementById(targetId);
    retries++;
  }

  if (!box) {
    console.warn(`⚠️ Target element #${targetId} not found (after waiting).`);
    return;
  }

  // --- Fade-out vorbereiten ---
  box.classList.remove("loaded");

  // --- KPI-Schlüssel bestimmen ---
  let key = null;
  if (typeof metaOrId === "string") key = metaOrId.replace(/\.json$/i, "");
  else if (metaOrId.filename) key = metaOrId.filename.replace(/\.json$/i, "");

  if (!key) {
    box.innerHTML = "<em>No KPI selected.</em>";
    setTimeout(() => box.classList.add("loaded"), 50);
    return;
  }

  // --- Anzeige aktualisieren ---
  box.innerHTML = "<em>Loading AI insights…</em>";
  const summary = await loadKpiAnalysis(key);

  // --- Ergebnis einfügen + Fade-in aktivieren ---
  if (summary) {
    box.innerHTML = `<strong>🧠 KPI Insights:</strong> ${summary}`;
  } else {
    box.innerHTML = "<em>No AI analysis available for this indicator.</em>";
  }

  // ✨ leicht verzögert aktivieren für sanftes Einblenden
  setTimeout(() => box.classList.add("loaded"), 50);
}

// === Expose globally for non-module pages ===
window.loadJSON = loadJSON;
window.showSpinner = showSpinner;
window.normalizeName = normalizeName;
window.resolveCountryName = resolveCountryName;
window.calculateGroupValues = calculateGroupValues;
window.rcLog = rcLog;
window.loadAllKPIData = loadAllKPIData;
window.loadKpiAnalysis = loadKpiAnalysis;
window.renderKpiAnalysis = renderKpiAnalysis;
