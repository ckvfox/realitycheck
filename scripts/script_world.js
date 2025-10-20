/* ============================================================
   🌍 RealityCheck – World Trends Dashboard (auto from /data)
   ============================================================ */

const META_FILE = "data/meta/available_kpis.json";
const DATA_DIR = "data";

/* ========= Hilfsfunktionen ========= */
async function loadJSON(path) {
  try {
    const res = await fetch(path, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const txt = await res.text();
    return txt ? JSON.parse(txt) : [];
  } catch (e) {
    console.warn("⚠️ loadJSON failed:", path, e);
    return [];
  }
}

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

/* ========= Chart Renderer ========= */
function renderChart(container, title, unit, data) {
  const canvas = document.createElement("canvas");
  canvas.width = 800;
  canvas.height = 400;
  container.appendChild(canvas);

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
        fill: false,
        tension: 0.2
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: { display: true, text: title },
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: false,
          title: { display: !!unit, text: unit || "" }
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
  showSpinner(true, "Loading global indicators…");

  const meta = await loadJSON(META_FILE);
  const worldKpis = meta
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

    const data = await loadJSON(`${DATA_DIR}/${filename}.json`);
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
  });

  await Promise.allSettled(tasks);

  showSpinner(false);
}

/* ========= Start ========= */
document.addEventListener("DOMContentLoaded", () => {
  initWorldPage();
});