/* ============================================================
   🌍 RealityCheck – Shared Header & Footer Loader (no iframes)
   ============================================================ */

document.addEventListener("DOMContentLoaded", async () => {
  try {
    // === Header laden ===
    const headerRes = await fetch("header.html?t=" + Date.now());
    const headerHtml = await headerRes.text();
    const header = document.createElement("div");
    header.innerHTML = headerHtml;
    document.body.prepend(header);

    // Aktiven Menüpunkt markieren
    const current = location.pathname.split("/").pop();
    header.querySelectorAll("nav a").forEach(a => {
      if (a.getAttribute("href") === current) a.classList.add("active");
    });

    // === Footer laden ===
    const footerRes = await fetch("footer.html?t=" + Date.now());
    const footerHtml = await footerRes.text();
    const footer = document.createElement("div");
    footer.innerHTML = footerHtml;
    document.body.appendChild(footer);

    // === ⏳ Tracking & Besucherzähler (erst nach Footer) ===
    setTimeout(async () => {
      try {
        // Tracking-Ping nur außerhalb von iframes
        if (window.self === window.top) {
          await fetch("tracking.php", { method: "POST", cache: "no-store" });
          console.log("📈 Tracking ping sent (delayed).");
        }

        // Besucherzahl aus tracking.json laden
        const el = document.getElementById("total-visitors");
        if (el) {
          const resp = await fetch("tracking.json?nocache=" + Date.now());
          if (resp.ok) {
            const data = await resp.json();
            el.textContent = "Visitors total: " + (data.total ?? "–");
          } else {
            el.textContent = "Visitors total: unavailable";
          }
        }
      } catch (err) {
        console.warn("⚠️ Visitor tracking failed:", err);
        const el = document.getElementById("total-visitors");
        if (el) el.textContent = "Visitors total: unavailable";
      }
    }, 800); // Footer ist nach ~0,8 s sicher eingefügt

  } catch (err) {
    console.warn("⚠️ Header/Footer load failed:", err);
  }
});


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

		// ⚡ Parallel laden & entpacken
		const ALL_DATA = {};
		await Promise.all(
			index.parts.map(async part => {
				const url = "data/" + part + "?t=" + Date.now();
				rcLog("⬇️ Loading", url);

				const response = await fetch(url);
				if (!response.ok) throw new Error(`HTTP ${response.status} on ${url}`);

				const buffer = await response.arrayBuffer();
				const bytes = new Uint8Array(buffer);

				let text;
				try {
					text = pako.ungzip(bytes, { to: "string" });
				} catch {
					text = new TextDecoder("utf-8").decode(bytes);
				}

				const json = JSON.parse(text);
				Object.assign(ALL_DATA, json);
			})
		);


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


/* ============================================================
   🧭 Navigation + Visitor Stats (index.html integration)
   ============================================================ */


// === IFrame Page Loader ===
window.loadPage = function (page, link) {
  const frame = document.getElementById("main-frame");
  const loader = document.getElementById("frame-loader");

  if (!frame) return;
  if (frame.src.includes(page)) return;

  frame.src = page + "?t=" + Date.now();
  if (loader) loader.classList.add("active");

  // Active link highlight
  document.querySelectorAll("nav a").forEach(a => a.classList.remove("active"));
  if (link) link.classList.add("active");
};

// === IFrame Load Event ===
document.addEventListener("DOMContentLoaded", () => {
  const frame = document.getElementById("main-frame");
  const loader = document.getElementById("frame-loader");

  if (frame && loader) {
    frame.addEventListener("load", () => loader.classList.remove("active"));
  }

});


/* ============================================================
   🔼 Global Scroll-to-Top Button (iframe-aware RealityCheck v9.3)
   ============================================================ */
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("scroll-top-btn");
  const frame = document.getElementById("main-frame");
  if (!btn) return;

	btn.addEventListener("click", () => {
		try {
			if (frame && frame.contentWindow && frame.contentDocument) {
				const doc = frame.contentDocument;
				const scrollTarget = doc.scrollingElement || doc.documentElement;
				scrollTarget.scrollTo({ top: 0, behavior: "smooth" });
			} else {
				window.scrollTo({ top: 0, behavior: "smooth" });
			}
			btn.style.transform = "scale(0.9)";
			setTimeout(() => (btn.style.transform = ""), 150);
		} catch (err) {
			console.warn("⚠️ Scroll-to-top failed:", err);
		}
	});

  // Sichtbar machen
  btn.style.opacity = "0.9";
  btn.style.pointerEvents = "auto";
});

/* ============================================================
   📱 Mobile Tooltip Popups for Mode Buttons
   ============================================================ */
document.addEventListener("DOMContentLoaded", () => {
  // Nur auf mobilen Geräten aktivieren
  if (window.innerWidth > 600) return;

  document.querySelectorAll(".mode-button").forEach(btn => {
    btn.addEventListener("click", e => {
      // Falls schon ein Tooltip offen ist → entfernen
      const old = document.querySelector(".mode-tooltip");
      if (old) old.remove();

      const text = btn.getAttribute("title") || "";
      if (!text) return;

      // Tooltip-Element erzeugen
      const tip = document.createElement("div");
      tip.className = "mode-tooltip";
      tip.textContent = text;
      document.body.appendChild(tip);

      // Position über Button berechnen
      const rect = btn.getBoundingClientRect();
      tip.style.left = `${rect.left + rect.width / 2}px`;
      tip.style.top = `${rect.top - 8}px`;

      // Sanft einblenden
      requestAnimationFrame(() => tip.classList.add("visible"));

      // Nach 1.5s wieder entfernen
      setTimeout(() => {
        tip.classList.remove("visible");
        setTimeout(() => tip.remove(), 300);
      }, 1500);
    });
  });
});

