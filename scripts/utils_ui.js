/* ============================================================
   🌈 RealityCheck – UI Utilities (Final 2025-11, Global Version)
   ------------------------------------------------------------
   Purpose:
   • Central helper for UI feedback, animations, and mobile UX
   • Merges existing toast + tooltip logic without behavior change
   • Adds Chart.js default configuration used across pages
   ============================================================ */

/* ------------------------------------------------------------
   🧩 Toast Helper (zentriert + Fade + Auto-hide)
   ------------------------------------------------------------ */
function showToast(msg) {
  let toast = document.getElementById("toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    document.body.appendChild(toast);

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

  toast.textContent = msg;

  toast.classList.add("show");
  requestAnimationFrame(() => {
    toast.style.opacity = "1";
    toast.style.transform = "translate(-50%, -50%) scale(1)";
  });

  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translate(-50%, -50%) scale(0.9)";
    toast.classList.remove("show");
  }, 2500);
}

/* ------------------------------------------------------------
   📱 Mobile Tooltips (for Mode Buttons)
   ------------------------------------------------------------ */
function initMobileTooltips() {
  if (window.innerWidth > 600) return;

  document.querySelectorAll(".mode-button").forEach(btn => {
    btn.addEventListener("click", e => {
      const old = document.querySelector(".mode-tooltip");
      if (old) old.remove();

      const text = btn.getAttribute("title") || "";
      if (!text) return;

      const tip = document.createElement("div");
      tip.className = "mode-tooltip";
      tip.textContent = text;
      document.body.appendChild(tip);

      const rect = btn.getBoundingClientRect();
      tip.style.left = `${rect.left + rect.width / 2}px`;
      tip.style.top = `${rect.top - 8}px`;

      requestAnimationFrame(() => tip.classList.add("visible"));

      setTimeout(() => {
        tip.classList.remove("visible");
        setTimeout(() => tip.remove(), 300);
      }, 1500);
    });
  });
}

/* ------------------------------------------------------------
   🎨 Chart.js Default Options (shared baseline)
   ------------------------------------------------------------ */
const DEFAULT_CHART_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  layout: { padding: { top: 20, bottom: 10, left: 10, right: 10 } },
  interaction: { mode: "nearest", intersect: false },
  plugins: {
    title: { display: false },
    legend: { display: true },
    tooltip: {
      enabled: true,
      callbacks: {
        title: ctx => "Year: " + (ctx[0]?.label ?? ""),
        label: ctx => {
          const val = ctx.parsed.y;
          if (val == null || isNaN(val)) return "No data";
          return `${val.toLocaleString()}`;
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: false,
      grid: { color: "rgba(0,0,0,0.05)" }
    },
    x: {
      grid: { color: "rgba(0,0,0,0.05)" },
      ticks: { autoSkip: true, maxTicksLimit: 10 }
    }
  }
};

/* ------------------------------------------------------------
   ✨ Simple Fade-in Helper (UI Animation)
   ------------------------------------------------------------ */
function fadeIn(el, delay = 0) {
  if (!el) return;
  el.style.opacity = "0";
  setTimeout(() => {
    el.style.transition = "opacity 0.4s ease";
    el.style.opacity = "1";
  }, delay);
}

/* ------------------------------------------------------------
   🌐 Make globals available
   ------------------------------------------------------------ */
window.showToast = showToast;
window.initMobileTooltips = initMobileTooltips;
window.DEFAULT_CHART_OPTIONS = DEFAULT_CHART_OPTIONS;
window.fadeIn = fadeIn;
