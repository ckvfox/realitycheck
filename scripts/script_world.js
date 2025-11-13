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

  let canvas = container.querySelector("canvas");
  if (!canvas) {
    canvas = document.createElement("canvas");
    container.appendChild(canvas);
  }

  const existingChart = canvas.__rcChart;
  if (existingChart?.destroy) {
    existingChart.destroy();
    canvas.__rcChart = null;
  }

  canvas.style.boxShadow = "0 2px 8px rgba(0,0,0,0.08)";
  canvas.style.borderRadius = "8px";
  canvas.style.marginBottom = "1rem";
  canvas.style.background = "#fff";

  const chart = renderLineChart(canvas, {
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

  canvas.__rcChart = chart;
}

/* ========= Einzel-Render-Funktion ========= */
async function renderWorldKpi(container, kpi) {
  const filename = kpi.filename;
  const title = kpi.title || filename;
  const desc = kpi.description || "";
  const unit = kpi.unit || "";

  const block = document.createElement("div");
  block.className = "graph-block";
  block.innerHTML = `<h3>${title}</h3>`;
  container.appendChild(block);

  const data = ALL_DATA[filename] || [];
  if (!Array.isArray(data) || data.length === 0) {
    block.innerHTML += `<p style="color:#666;font-style:italic;">No data available.</p>`;
    return;
  }

  const worldData = getWorldSeries(data);
  if (worldData.years.length === 0) {
    block.innerHTML += `<p style="color:#666;font-style:italic;">No global values in dataset.</p>`;
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
      const hostname = new URL(kpi.source).hostname.replace("www.", "");
      source.innerHTML = `Source: <a href="${kpi.source}" target="_blank" rel="noopener">${hostname}</a>`;
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
      worldContainer.innerHTML = `<p style="text-align:center;margin-top:2rem;">No global KPIs found.</p>`;
      return;
    }

    worldContainer.innerHTML = "";

    // === Rendern nach Cluster ===
    for (const [cluster, list] of Object.entries(grouped)) {
      const h2 = document.createElement("h2");
      h2.textContent = cluster;
      h2.style.margin = "2rem auto 1rem";
      h2.style.textAlign = "center";
      h2.style.color = "var(--steel-blue)";
      worldContainer.appendChild(h2);

      for (const kpi of list) {
        await renderWorldKpi(worldContainer, kpi);
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
document.addEventListener("DOMContentLoaded", initWorldPage);
