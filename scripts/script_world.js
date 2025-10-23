/* ============================================================
   🌍 RealityCheck – World Trends Dashboard (auto from /data)
   ============================================================ */

const META_FILE = "data/meta/available_kpis.json";
const DATA_DIR = "data";

let META = [], ALL_DATA = {}; // consolidated dataset + meta


/* ========= Chart Helper ========= */
function getWorldSeries(entries) {
  const worldRows = entries.filter(r => 
    r.country === "World" || r.country === "Welt" || r.country === "Global"
  );
  const sorted = worldRows.sort((a,b) => a.year - b.year);
  const years = sorted.map(r => r.year);
  const values = sorted.map(r => r.value);
  return { years, values };
}

/* ========= Spinner Steuerung ========= */
function showSpinner(show=true, msg="Loading global data…") {
  let spinner = document.getElementById("overlay-spinner");
  if (!spinner) return;
  spinner.textContent = msg;
  spinner.classList.toggle("hidden", !show);
}

/* ========= Chart Renderer mit Tooltip ========= */
function renderChart(container, title, unit, data) {
  const canvas = document.createElement("canvas");
  canvas.width = 800;
  canvas.height = 400;
  container.appendChild(canvas);
// 🌈 Optionales Styling für bessere Optik
  canvas.style.boxShadow = "0 2px 8px rgba(0,0,0,0.08)";
  canvas.style.borderRadius = "8px";
  canvas.style.marginBottom = "1rem";
  canvas.style.background = "#fff";

  const ctx = canvas.getContext("2d");

  new Chart(ctx, {
    type: "line",
    data: {
      labels: data.years,
      datasets: [{
        label: title,
        data: data.values,
        borderColor: "#1a355e",
        borderWidth: 2,
        pointRadius: 2,
        pointHoverRadius: 5,
        fill: false,
        tension: 0.2
      }]
    },
    options: {
      responsive: true,
      interaction: { mode: "nearest", intersect: false },
      plugins: {
        title: { display: true, text: title },
        legend: { display: false },
        tooltip: {
          enabled: true,
          callbacks: {
            title: ctx => "Year: " + (ctx[0]?.label ?? ""),
            label: ctx => {
              const val = ctx.parsed.y;
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
}

/* ========= Hauptlogik ========= */
async function initWorldPage() {
  showSpinner(true, "Loading world data…");
  META = await loadJSON("data/meta/available_kpis.json");
  ALL_DATA = await loadAllKPIData();

  const worldKpis = META
    .filter(k => (k.world_kpi === "y" || k.world_kpi === "e") && k.filename)
    .sort((a,b) => a.title.localeCompare(b.title));

  console.log(`🌐 Found ${worldKpis.length} global KPIs.`);

  const worldContainer = document.getElementById("world-kpis");
  if (!worldContainer) {
    console.error("❌ #world-kpis container missing");
    return;
  }

  if (worldKpis.length === 0) {
    showSpinner(false);
    worldContainer.innerHTML = `<p style="text-align:center;margin-top:2rem;">No global KPIs found.</p>`;
    return;
  }

  const tasks = worldKpis.map(async (kpi) => {
    const filename = kpi.filename;
    const title = kpi.title || filename;
    const desc = kpi.description || "";
    const unit = kpi.unit || "";

    const block = document.createElement("div");
    block.className = "graph-block";
    block.innerHTML = `<h3>${title}</h3>`;
    worldContainer.appendChild(block);

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
		// === Quelle hinzufügen ===
	const source = document.createElement("p");
	source.className = "chart-source";
	if (kpi.source) {
	  // Wenn in available_kpis.json ein Source-Link steht → verwende ihn
	  source.innerHTML = `Source: <a href="${kpi.source}" target="_blank" rel="noopener">${new URL(kpi.source).hostname}</a>`;
	} else {
	  // Fallback für KPIs ohne Link
	  source.textContent = "Source: RealityCheck Database (OWID, World Bank, UN, EPI)";
	}
	block.appendChild(source);

  });

  await Promise.allSettled(tasks);

  showSpinner(false);
}

/* ========= Start ========= */
document.addEventListener("DOMContentLoaded", () => {
  initWorldPage();
});