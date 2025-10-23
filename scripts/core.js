/* ============================================================
   🌐 RealityCheck – Core Utilities (shared functions, 2025-10)
   ============================================================ */

// === Load JSON with cache-bypass & error-handling ===
async function loadJSON(path) {
  try {
    const res = await fetch(path + "?t=" + Date.now(), { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const txt = await res.text();
    return txt ? JSON.parse(txt) : [];
  } catch (e) {
    console.warn("⚠️ loadJSON failed:", path, e);
    return [];
  }
}

// === Spinner ===
function showSpinner(show = true, msg = "Loading…") {
  const sp = document.getElementById("overlay-spinner");
  if (!sp) return;
  if (msg) sp.textContent = msg;
  sp.classList.toggle("hidden", !show);
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



// === Expose globally for non-module pages ===
window.loadJSON = loadJSON;
window.showSpinner = showSpinner;
window.normalizeName = normalizeName;
window.resolveCountryName = resolveCountryName;
window.calculateGroupValues = calculateGroupValues;
window.rcLog = rcLog;
window.loadAllKPIData = loadAllKPIData;
