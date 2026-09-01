/**
 * RealityCheck Data Glossary Page Scripts
 * Handles dynamic table generation and KPI data display
 */

/**
 * Debounce utility function to limit function calls
 * @param {Function} fn - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
const debounce = (fn, wait = 120) => {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(null, args), wait);
  };
};

/**
 * Updates scroll state classes for the glossary table
 * Manages responsive horizontal scrolling behavior
 */
const updateGlossaryScrollState = () => {
  const host = document.getElementById("glossary-container");
  const wrapper = document.getElementById("glossary-table-wrapper") || host;
  const table = wrapper?.querySelector("#glossary-table");
  if (!host || !wrapper || !table) return;

  const tolerance = window.devicePixelRatio > 1 ? 4 : 2;
  const needsScroll = table.scrollWidth - wrapper.clientWidth > tolerance;
  host.classList.toggle("glossary-scrollable", needsScroll);
  wrapper.classList.toggle("glossary-wrapper-scrollable", needsScroll);
  host.dataset.scrollable = needsScroll ? "true" : "false";
  wrapper.dataset.scrollable = host.dataset.scrollable;
};

/**
 * Initializes the data glossary table with KPI information
 */
async function loadGlossary() {
  try {
    // Load required data
    const [fetchRes, outlierRes, metaRes, countryRes] = await Promise.all([
      fetch("data/fetch_status.json"),
      fetch("data/analysis_outliers.json"),
      fetch("data/meta/available_kpis.json"),
      fetch("data/meta/countries.json")
    ]);

    const fetchData = await fetchRes.json();
    const outliers = await outlierRes.json();
    const meta = (await metaRes.json()).filter(kpi => kpi.publication_status !== "pending_first_fetch");
    const countries = await countryRes.json();
    const ALL_DATA = await loadAllKPIData();

    const totalCountries = Object.keys(countries).length || 200;
    const tbody = document.getElementById("glossary-body");
    tbody.innerHTML = "";

    const kpis = fetchData.kpis || {};
    const nowYear = new Date().getFullYear();

    // Create title mapping from meta data
    const titleMap = {};
    for (const m of meta) {
      if (m.filename) titleMap[m.filename] = m.title || m.id || m.filename;
    }

    // Exclude non-country entities from coverage calculations
    const EXCLUDE = new Set([
      "World", "European Union", "Euro area", "OECD members",
      "High income", "Upper middle income", "Lower middle income", "Low income"
    ]);

    // Helper functions
    const fmtShort = (dateStr) => {
      if (!dateStr) return "Unknown";
      const d = new Date(dateStr);
      return isNaN(d) ? "Unknown" : d.toISOString().slice(0, 10);
    };

    const countryCount = (filename) => {
      const arr = ALL_DATA[filename];
      if (!Array.isArray(arr) || arr.length === 0) return 0;
      const latest = new Map();
      for (const d of arr) {
        const v = parseFloat(d.value);
        if (!d.country || isNaN(v) || EXCLUDE.has(d.country)) continue;
        const prev = latest.get(d.country);
        if (!prev || (d.year ?? -Infinity) > (prev.year ?? -Infinity)) {
          latest.set(d.country, d);
        }
      }
      return latest.size;
    };

    const isSafeUrl = (url) => {
      try {
        const parsed = new URL(url, window.location.href);
        return ["http:", "https:"].includes(parsed.protocol);
      } catch {
        return false;
      }
    };

    const classifyYear = (year) => {
      if (!Number.isFinite(year) || year <= 0) return "glossary-stale";
      const age = nowYear - year;
      if (age <= 1) return "glossary-fresh";
      if (age <= 3) return "glossary-warn";
      return "glossary-stale";
    };

    const classifyDate = (dateStr) => {
      if (!dateStr || !/\d{4}/.test(dateStr)) return "glossary-stale";
      const y = parseInt(dateStr.match(/\d{4}/)[0], 10);
      return classifyYear(y);
    };

    // Process each KPI
    for (const [id, info] of Object.entries(kpis)) {
      const tr = document.createElement("tr");
      const out = outliers[id] || {};
      const highs = Array.isArray(out.high_outliers) ? out.high_outliers : [];
      const lows = Array.isArray(out.low_outliers) ? out.low_outliers : [];
      const flaggedCount = highs.length + lows.length;

      // Data year and freshness calculation
      const dy = parseInt(info.data_year, 10) || 0;
      const clsYear = classifyYear(dy);
      const clsSrc = classifyDate(info.source_date);
      const clsFetch = classifyDate(info.last_fetch);
      const clsOut = flaggedCount >= 10 ? "glossary-outlier" : flaggedCount > 0 ? "glossary-warn" : "";
      
      // Outlier information
      const minList = lows.slice(0, 3).map(e => `${e.country} (${e.year})`);
      const maxList = highs.slice(0, 3).map(e => `${e.country} (${e.year})`);
      const minInfo = minList.length ? minList.join(", ") : "–";
      const maxInfo = maxList.length ? maxList.join(", ") : "–";

      const n = countryCount(id);
      const pct = ((n / totalCountries) * 100).toFixed(0);
      const title = titleMap[id] || id;

      // Build table row
      const cellTitle = document.createElement("td");
      cellTitle.textContent = title;
      tr.appendChild(cellTitle);

      const cellSource = document.createElement("td");
      if (info.source && isSafeUrl(info.source)) {
        const link = document.createElement("a");
        link.href = info.source;
        link.target = "_blank";
        link.rel = "noopener";
        link.textContent = info.source;
        cellSource.appendChild(link);
      } else {
        cellSource.textContent = info.source || "?";
      }
      tr.appendChild(cellSource);

      const cellDataYear = document.createElement("td");
      cellDataYear.className = clsYear;
      cellDataYear.textContent = info.data_year || "Unknown";
      tr.appendChild(cellDataYear);

      const cellSourceDate = document.createElement("td");
      cellSourceDate.className = clsSrc;
      cellSourceDate.textContent = fmtShort(info.source_date);
      tr.appendChild(cellSourceDate);

      const cellLastFetch = document.createElement("td");
      cellLastFetch.className = clsFetch;
      cellLastFetch.textContent = fmtShort(info.last_fetch);
      tr.appendChild(cellLastFetch);

      const cellCoverage = document.createElement("td");
      cellCoverage.title = `Coverage: ${pct}%`;
      cellCoverage.textContent = n || "–";
      tr.appendChild(cellCoverage);

      const cellOutliers = document.createElement("td");
      if (clsOut) {
        cellOutliers.classList.add(clsOut);
      }
      if (flaggedCount) {
        const badge = document.createElement("span");
        badge.textContent = `🔺 ${flaggedCount}`;
        badge.className = clsOut;
        cellOutliers.appendChild(badge);
      } else {
        cellOutliers.textContent = "–";
      }

      const detail = document.createElement("span");
      detail.className = "outlier-info";
      const minStrong = document.createElement("strong");
      minStrong.textContent = "min:";
      const maxStrong = document.createElement("strong");
      maxStrong.textContent = "max:";
      detail.appendChild(minStrong);
      detail.appendChild(document.createTextNode(` ${minInfo}`));
      detail.appendChild(document.createElement("br"));
      detail.appendChild(maxStrong);
      detail.appendChild(document.createTextNode(` ${maxInfo}`));
      cellOutliers.appendChild(detail);

      tr.appendChild(cellOutliers);
      tbody.appendChild(tr);
    }

    makeTableSortable("glossary-table");
    requestAnimationFrame(updateGlossaryScrollState);

  } catch (err) {
    console.error("❌ Glossary load failed:", err);
    const body = document.getElementById("glossary-body");
    body.innerHTML = "";
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 7;
    cell.className = "table-status table-status--error";
    cell.textContent = "Error loading data";
    row.appendChild(cell);
    body.appendChild(row);
    requestAnimationFrame(updateGlossaryScrollState);
  }
}

/**
 * Makes a table sortable by clicking column headers
 * @param {string} id - Table element ID
 */
function makeTableSortable(id) {
  const table = document.getElementById(id);
  const headers = table.querySelectorAll("th.sortable");
  
  headers.forEach((th, i) => {
    th.addEventListener("click", () => {
      const asc = !th.classList.contains("sort-asc");
      headers.forEach(h => h.classList.remove("sort-asc", "sort-desc"));
      th.classList.toggle("sort-asc", asc);
      th.classList.toggle("sort-desc", !asc);
      sortTableByColumn(table, i, asc);
    });
  });
}

/**
 * Sorts table rows by specified column
 * @param {HTMLTableElement} table - Table to sort
 * @param {number} col - Column index to sort by
 * @param {boolean} asc - Sort ascending if true
 */
function sortTableByColumn(table, col, asc = true) {
  const tbody = table.tBodies[0];
  const rows = Array.from(tbody.querySelectorAll("tr"));
  const dir = asc ? 1 : -1;

  const parseVal = v => {
    const raw = String(v ?? "").trim();
    const text = raw.toLowerCase();

    const isUnknown = raw === "" || text === "unknown" || text === "n/a" || text === "na" || text === "-" || text === "–";
    if (isUnknown) {
      return { unknown: true, type: "unknown", value: null, text };
    }

    // Parse ISO dates before numeric parsing so 2026-07-13 is treated as a date, not as 2026.
    if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
      const ts = Date.parse(raw);
      if (!isNaN(ts)) return { unknown: false, type: "date", value: ts, text };
    }

    const num = parseFloat(raw.replace(/[^\d.\-]/g, ""));
    if (!isNaN(num)) return { unknown: false, type: "number", value: num, text };

    const date = Date.parse(raw);
    if (!isNaN(date)) return { unknown: false, type: "date", value: date, text };

    return { unknown: false, type: "string", value: text, text };
  };
  
  rows.sort((a, b) => {
    const va = parseVal(a.cells[col].innerText.trim());
    const vb = parseVal(b.cells[col].innerText.trim());

    // Unknown is always treated as the worst value:
    // ascending -> first, descending -> last.
    if (va.unknown !== vb.unknown) return va.unknown ? -1 * dir : 1 * dir;

    if (va.type === vb.type) {
      if (va.value > vb.value) return 1 * dir;
      if (va.value < vb.value) return -1 * dir;
      return 0;
    }

    if (va.text > vb.text) return 1 * dir;
    if (va.text < vb.text) return -1 * dir;
    return 0;
  });
  
  rows.forEach(r => tbody.appendChild(r));
}

// Initialize when DOM is ready
window.addEventListener("resize", debounce(updateGlossaryScrollState, 160));

if (typeof onDocumentReady === "function") {
  onDocumentReady(loadGlossary);
} else {
  window.addEventListener("DOMContentLoaded", loadGlossary);
}
