/* ============================================================
   🌍 RealityCheck – World Trends Dashboard (auto from /data)
   ------------------------------------------------------------
   Final Clean Version (2025-11-01)
   • Spinner-Handling über core.js (showSpinner)
   • Einheitliche Nutzung von loadJSON() und loadAllKPIData()
   ============================================================ */

const META_FILE = "data/meta/available_kpis.json";
const DATA_DIR = "data";

let META = [], ALL_DATA = {}; // consolidated dataset + meta

/* ========= Chart Helper ========= */
function getWorldSeries(entries) {
  const worldRows = entries.filter(r =>
    r.country === "World" || r.country === "Welt" || r.country === "Global"
  );
  const sorted = worldRows.sort((a, b) => a.year - b.year);
  const years = sorted.map(r => r.year);
  const values = sorted.map(r => r.value);
  return { years, values };
}

/* ========= Chart Renderer mit Tooltip ========= */
function renderChart(container, title, unit, data) {
  if (!container) return;

  let canvasEl = container.querySelector("canvas");
  if (!canvasEl) {
    canvasEl = document.createElement("canvas");
    canvasEl.classList.add("chart-canvas");
    container.appendChild(canvasEl);
  } else {
    canvasEl.classList.add("chart-canvas");
  }

  const chart = renderLineChart(canvasEl, {
    labels: data.years,
    datasets: [
      {
        label: title,
        data: data.values,
        borderColor: "#1a355e",
        borderWidth: 2,
        pointRadius: 2,
        pointHoverRadius: 5,
        fill: false,
        tension: 0.25
      }
    ],
    unit,
    title: "",
    existingChart: canvasEl.__rcChart,
    options: {
      plugins: {
        title: { display: false },
        legend: { display: false },
        tooltip: {
          enabled: true,
          callbacks: {
            title: ctx => "Year: " + (ctx[0]?.label ?? ""),
            label: ctx => {
              const val = ctx.parsed?.y;
              if (val == null || isNaN(val)) return "No data";
              return `${val.toLocaleString()} ${unit || ""}`.trim();
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          title: { display: !!unit, text: unit || "" },
          grid: { color: "rgba(0,0,0,0.05)" }
        },
        x: {
          ticks: { autoSkip: true, maxTicksLimit: 10 },
          grid: { color: "rgba(0,0,0,0.05)" }
        }
      }
    }
  });

  canvasEl.__rcChart = chart;
}

/* ========= Einzel-Render-Funktion ========= */
async function renderWorldKpi(container, kpi) {
  const filename = kpi.filename;
  const title = kpi.title || filename;
  const desc = kpi.description || "";
  const unit = kpi.unit || "";

  let safeIdBase = window.normalizeName
    ? window.normalizeName(filename || title)
    : (filename || title || "").toLowerCase().replace(/[^a-z0-9]+/g, "-");
  safeIdBase = (safeIdBase || "kpi").replace(/^-+|-+$/g, "");
  const blockId = `world-kpi-${safeIdBase}`;

  let block = container.querySelector(`#${blockId}`);
  if (!block) {
    block = document.createElement("div");
    block.className = "graph-block";
    block.id = blockId;
    container.appendChild(block);
  }

  let titleEl = block.querySelector("h3");
  if (!titleEl) {
    titleEl = document.createElement("h3");
    block.prepend(titleEl);
  }
  titleEl.textContent = title;

  const existingCanvas = block.querySelector("canvas") || null;
  Array.from(block.children).forEach(child => {
    if (child.tagName === "H3" || child === existingCanvas) return;
    if (child.tagName === "CANVAS" && child !== existingCanvas && child.__rcChart?.destroy) {
      child.__rcChart.destroy();
    }
    child.remove();
  });

  const data = ALL_DATA[filename] || [];
  if (!Array.isArray(data) || data.length === 0) {
    block.querySelectorAll("canvas").forEach(c => {
      if (c.__rcChart?.destroy) c.__rcChart.destroy();
      c.remove();
    });
    const msg = document.createElement("p");
    msg.className = "kpi-message";
    msg.textContent = "No data available.";
    block.appendChild(msg);
    return;
  }

  const worldData = getWorldSeries(data);
  if (worldData.years.length === 0) {
    block.querySelectorAll("canvas").forEach(c => {
      if (c.__rcChart?.destroy) c.__rcChart.destroy();
      c.remove();
    });
    const msg = document.createElement("p");
    msg.className = "kpi-message";
    msg.textContent = "No global values in dataset.";
    block.appendChild(msg);
    return;
  }

  renderChart(block, title, unit, worldData);

  if (desc) {
    const p = document.createElement("p");
    p.className = "kpi-desc";
    p.textContent = desc;
    block.appendChild(p);
  }

  // === KI-Analysebox einfügen ===
  const aiBox = document.createElement("div");
  aiBox.id = `kpi-analysis-${filename}`;
  aiBox.className = "kpi-analysis";
  block.appendChild(aiBox);
  renderKpiAnalysis(kpi, aiBox.id);

  // === Quelle hinzufügen ===
  const source = document.createElement("p");
  source.className = "chart-source";
  if (kpi.source) {
    try {
      const url = new URL(kpi.source, window.location.href);
      if (["http:", "https:"].includes(url.protocol)) {
        const hostname = url.hostname.replace(/^www\./, "");
        const link = document.createElement("a");
        link.href = url.href;
        link.target = "_blank";
        link.rel = "noopener";
        link.textContent = hostname;
        source.textContent = "Source: ";
        source.appendChild(link);
      } else {
        source.textContent = `Source: ${kpi.source}`;
      }
    } catch {
      source.textContent = `Source: ${kpi.source}`;
    }
  } else {
    source.textContent = "Source: RealityCheck Database (OWID, World Bank, UN, EPI)";
  }
  block.appendChild(source);
}

/* ========= Hauptlogik ========= */
async function initWorldPage() {
  if (initWorldPage.__running) {
    return;
  }
  initWorldPage.__running = true;
  try {
    // 🌀 Zeige globalen Spinner (aus core.js)
    showSpinner(true, "Loading world data…");

    META = await loadJSON(META_FILE);
    ALL_DATA = await loadAllKPIData();

    // === Gruppierung nach Cluster ===
    const grouped = {};
    for (const k of META) {
      if ((k.world_kpi === "y" || k.world_kpi === "e") && k.filename) {
        const cl = k.cluster || "Other";
        if (!grouped[cl]) grouped[cl] = [];
        grouped[cl].push(k);
      }
    }

    const worldContainer = document.getElementById("world-kpis");
    if (!worldContainer) {
      console.error("❌ #world-kpis container missing");
      return;
    }

    if (Object.keys(grouped).length === 0) {
      worldContainer.innerHTML = "";
      const emptyMsg = document.createElement("p");
      emptyMsg.className = "world-empty";
      emptyMsg.textContent = "No global KPIs found.";
      worldContainer.appendChild(emptyMsg);
      return;
    }

    worldContainer.innerHTML = "";

    // === Rendern nach Cluster ===
    for (const [cluster, list] of Object.entries(grouped)) {
      const clusterKey = window.normalizeName
        ? window.normalizeName(cluster)
        : (cluster || "cluster").toLowerCase().replace(/[^a-z0-9]+/g, "-");
      const clusterId = `world-cluster-${clusterKey || "group"}`;

      let clusterSection = worldContainer.querySelector(`#${clusterId}`);
      if (!clusterSection) {
        clusterSection = document.createElement("section");
        clusterSection.id = clusterId;
        clusterSection.className = "world-cluster";

        const h2 = document.createElement("h2");
        h2.textContent = cluster;
        h2.className = "world-cluster-title";
        clusterSection.appendChild(h2);

        worldContainer.appendChild(clusterSection);
      } else {
        // Clean out previous KPI blocks before rerendering the cluster.
        clusterSection.querySelectorAll(".graph-block").forEach(block => {
          block.querySelectorAll("canvas").forEach(c => {
            if (c.__rcChart?.destroy) c.__rcChart.destroy();
          });
          block.remove();
        });
      }

      for (const kpi of list) {
        await renderWorldKpi(clusterSection, kpi);
      }
    }
  } catch (err) {
    console.error("🌍 initWorldPage failed:", err);
  } finally {
    // ✅ Spinner immer ausblenden
    showSpinner(false);
    initWorldPage.__running = false;
  }
}

// === Seite initialisieren ===
if (typeof onDocumentReady === "function") {
  onDocumentReady(initWorldPage);
} else {
  document.addEventListener("DOMContentLoaded", initWorldPage);
}
