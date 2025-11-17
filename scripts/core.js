if (window.__RC_CORE_LOADED__) {
  console.warn("⚠️ RealityCheck core.js was loaded twice – ignoring duplicate include.");
} else {
  window.__RC_CORE_LOADED__ = true;

// ✅ Globale Utility-Funktionen (außerhalb IIFE für bessere Verfügbarkeit)
function whenDocumentReady() {
  if (document.readyState === "complete" || document.readyState === "interactive") {
    return Promise.resolve();
  }
  return new Promise(resolve =>
    document.addEventListener("DOMContentLoaded", resolve, { once: true })
  );
}

function onDocumentReady(handler) {
  if (typeof handler !== "function") return;
  if (document.readyState === "complete" || document.readyState === "interactive") {
    handler();
  } else {
    document.addEventListener("DOMContentLoaded", handler, { once: true });
  }
}

function showSpinner(show = true, msg = "Loading…") {
  const spinner = document.getElementById("overlay-spinner");
  if (!spinner) return;
  
  if (show) {
    spinner.classList.remove("hidden");
    spinner.classList.add("active");
    spinner.innerHTML = `<div class="spinner-content"><p>${msg}</p></div>`;
  } else {
    spinner.classList.add("hidden");
    spinner.classList.remove("active");
  }
}

async function loadJSON(path) {
  try {
    const response = await fetch(path, { cache: "no-cache" });
    if (!response.ok) {
      console.warn(`⚠️ loadJSON: HTTP ${response.status} for ${path}`);
      return [];
    }
    
    const txt = await response.text();
    if (!txt.trim()) {
      console.warn("⚠️ loadJSON: empty response from", path);
      return [];
    }

    let parsed;
    try {
      parsed = JSON.parse(txt);
    } catch (err) {
      console.warn("⚠️ loadJSON: content not valid JSON → returning raw text", path);
      parsed = txt;
    }

    if (typeof parsed === "string") {
      try {
        parsed = JSON.parse(parsed);
        console.log("🧩 loadJSON: double-parsed JSON string", path);
      } catch {
        // Bleibt String
      }
    }

    return parsed || [];
  } catch (e) {
    console.warn("⚠️ loadJSON failed:", path, e);
    return [];
  }
}

function chooseScaleFromValues(values) {
  const numbers = Array.isArray(values) ? values : [];
  const maxValue = numbers.reduce((max, value) => {
    const numeric = value == null ? 0 : Math.abs(Number(value));
    return numeric > max ? numeric : max;
  }, 0);

  if (maxValue >= 1e9) return { factor: 1e9, suffix: "B", label: "Billions" };
  if (maxValue >= 1e6) return { factor: 1e6, suffix: "M", label: "Millions" };
  if (maxValue >= 1e3) return { factor: 1e3, suffix: "K", label: "Thousands" };
  return { factor: 1, suffix: "", label: "Exact values" };
}

function formatValueAuto(value, scaleMode = "auto") {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  const abs = Math.abs(Number(value));

  if (scaleMode === "%" || scaleMode === "none" || scaleMode === "index") {
    return Number(value).toFixed(2);
  }

  if (scaleMode === "auto") {
    if (abs >= 1e12) return (value / 1e12).toFixed(2) + " T";
    if (abs >= 1e9) return (value / 1e9).toFixed(2) + " B";
    if (abs >= 1e6) return (value / 1e6).toFixed(2) + " M";
    if (abs >= 1e3) return (value / 1e3).toFixed(2) + " K";
    return Number(value).toFixed(2);
  }

  return Number(value).toFixed(2);
}

function calcTrend(current, previous) {
  if (current == null || previous == null) return "→";
  if (current > previous) return "↑";
  if (current < previous) return "↓";
  return "→";
}

function escapeHTML(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function deepMerge(target, ...sources) {
  if (!target) target = {};
  for (const source of sources) {
    if (!source) continue;
    for (const key of Object.keys(source)) {
      const value = source[key];
      if (value && typeof value === "object" && !Array.isArray(value)) {
        target[key] = deepMerge(target[key] || {}, value);
      } else {
        target[key] = value;
      }
    }
  }
  return target;
}

// ✅ Sofort globale Exports für kritische Funktionen
window.whenDocumentReady = whenDocumentReady;
window.onDocumentReady = onDocumentReady;
window.showSpinner = showSpinner;
window.loadJSON = loadJSON;
window.chooseScaleFromValues = chooseScaleFromValues;
window.formatValueAuto = formatValueAuto;
window.calcTrend = calcTrend;
window.escapeHTML = escapeHTML;
window.deepMerge = deepMerge;

  (() => {
  /* ============================================================
     🌍 RealityCheck – Shared Header & Footer Loader (no iframes)
     ============================================================ */

const TRANSLATOR_SESSION_KEY = "rc_google_translate_consent";
const translatorState = {
  button: null,
  panel: null,
  closeBtn: null,
  overlay: null,
  dialog: null,
  confirmBtn: null,
  cancelBtn: null,
  consent: false,
  previousFocus: null,
  scriptPromise: null,
  ready: false,
  pendingOpen: false,
  initialized: false,
  listenersAttached: false
};

const TRANSLATOR_LAUNCHER_MARKUP = `
  <button
    type="button"
    id="translator-toggle"
    class="translator-button"
    title="Translate this page"
    aria-label="Translate this page"
    aria-haspopup="dialog"
    aria-controls="translator-panel"
    aria-expanded="false"
  >
    <img src="images/translate.png" alt="" class="translator-icon" aria-hidden="true" />
  </button>
  <div id="translator-panel" class="translator-panel" role="region" aria-label="Google Translate" hidden>
    <div class="translator-panel-header">
      <span>Google Translate</span>
      <button type="button" class="translator-close" aria-label="Close translator" title="Close">&times;</button>
    </div>
    <div class="translator-panel-body">
      <p class="translator-loading-message">Google Translate is loading…</p>
      <div id="google_translate_element" class="translator-widget"></div>
    </div>
  </div>
`;

let translatorInitResolve;
let translatorInitReject;

document.addEventListener("DOMContentLoaded", async () => {
  let launcher = ensureTranslatorLauncherMounted();
  try {
    const assetVersion =
      document.querySelector('meta[name="rc-build-version"]')?.content ||
      window.__RC_ASSET_VERSION__ ||
      "1";
    const fetchOptions = { cache: "no-cache" };

    const [headerHtml, footerHtml] = await Promise.all([
      fetch(`header.html?v=${assetVersion}`, fetchOptions).then(res => {
        if (!res.ok) throw new Error(`Header fetch failed: ${res.status}`);
        return res.text();
      }),
      fetch(`footer.html?v=${assetVersion}`, fetchOptions).then(res => {
        if (!res.ok) throw new Error(`Footer fetch failed: ${res.status}`);
        return res.text();
      })
    ]);

    const header = document.createElement("div");
    header.innerHTML = headerHtml;
    header.querySelectorAll(".translator-launcher").forEach(node => node.remove());
    document.body.prepend(header);

    const current = location.pathname.split("/").pop();
    header.querySelectorAll("nav a").forEach(a => {
      if (a.getAttribute("href") === current) a.classList.add("active");
    });

    const footer = document.createElement("div");
    footer.innerHTML = footerHtml;
    footer.querySelectorAll(".translator-launcher").forEach(node => node.remove());
    document.body.appendChild(footer);

    setTimeout(async () => {
      try {
        if (window.self === window.top) {
          await fetch("tracking.php", { method: "POST", cache: "no-store" });
          console.log("📈 Tracking ping sent (delayed).");
        }

        const el = document.getElementById("total-visitors");
        if (el) {
          const resp = await fetch(`tracking.json?v=${assetVersion}`);
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
    }, 400);
  } catch (err) {
    console.warn("⚠️ Header/Footer load failed:", err);
  }

  launcher = ensureTranslatorLauncherMounted();
  if (launcher) setupTranslatorControls();
});

function ensureTranslatorLauncherMounted() {
  const launchers = document.querySelectorAll(".translator-launcher");
  if (launchers.length > 1) {
    launchers.forEach((node, idx) => {
      if (idx === 0) return;
      node.remove();
    });
  }

  let existing = launchers[0];
  if (existing) {
    syncTranslatorLauncherPosition(existing);
    return existing;
  }

  const container = document.createElement("div");
  container.className = "translator-launcher";
  container.innerHTML = TRANSLATOR_LAUNCHER_MARKUP.trim();
  syncTranslatorLauncherPosition(container);
  
  // 🎨 Force glassmorphism styles for translator button
  const btn = container.querySelector(".translator-button");
  if (btn) {
    Object.assign(btn.style, {
      background: "rgba(255, 255, 255, 0.15)",
      backdropFilter: "blur(12px)",
      border: "1px solid rgba(255, 255, 255, 0.2)",
      borderRadius: "50%",
      width: "48px",
      height: "48px",
      boxShadow: "0 4px 20px rgba(0, 0, 0, 0.1), 0 2px 10px rgba(0, 0, 0, 0.05)",
      transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
      cursor: "pointer",
      display: "flex",
      alignItems: "center",
      justifyContent: "center"
    });
    
    // 🌟 Hover effects
    btn.addEventListener("mouseenter", () => {
      Object.assign(btn.style, {
        background: "rgba(255, 255, 255, 0.25)",
        borderColor: "rgba(255, 255, 255, 0.4)",
        transform: "translateY(-2px) scale(1.05)",
        boxShadow: "0 8px 30px rgba(0, 0, 0, 0.15), 0 4px 15px rgba(0, 0, 0, 0.1), 0 0 0 4px rgba(255, 255, 255, 0.1)"
      });
    });
    
    btn.addEventListener("mouseleave", () => {
      Object.assign(btn.style, {
        background: "rgba(255, 255, 255, 0.15)",
        borderColor: "rgba(255, 255, 255, 0.2)",
        transform: "translateY(0) scale(1)",
        boxShadow: "0 4px 20px rgba(0, 0, 0, 0.1), 0 2px 10px rgba(0, 0, 0, 0.05)"
      });
    });
  }

  const scrollButton = document.getElementById("scroll-top-btn");
  if (scrollButton && scrollButton.parentNode === document.body) {
    document.body.insertBefore(container, scrollButton.nextSibling);
  } else {
    document.body.appendChild(container);
  }

  return container;
}

function syncTranslatorLauncherPosition(node) {
  if (!node || node.dataset.positionSynced) return;
  node.style.position = "fixed";
  node.style.top = "var(--floating-btn-offset)";
  node.style.right = "var(--floating-btn-offset)";
  node.style.left = "auto";
  node.style.bottom = "auto";
  node.style.margin = "0";
  node.style.zIndex = "3000";
  node.style.display = "flex";
  node.style.alignItems = "center";
  node.style.justifyContent = "center";
  node.dataset.positionSynced = "true";
}
function setupTranslatorControls() {
  if (translatorState.initialized) return;

  const button = document.getElementById("translator-toggle");
  const panel = document.getElementById("translator-panel");
  if (!button || !panel) return;

  translatorState.button = button;
  translatorState.panel = panel;
  translatorState.closeBtn = panel.querySelector(".translator-close");
  translatorState.initialized = true;

  button.addEventListener("click", handleTranslatorButtonClick);
  button.setAttribute("aria-expanded", "false");

  translatorState.closeBtn?.addEventListener("click", event => {
    event.preventDefault();
    hideTranslatorPanel();
    translatorState.button?.focus();
  });

  panel.addEventListener("click", event => event.stopPropagation());

  if (!translatorState.listenersAttached) {
    document.addEventListener("click", handleTranslatorDocumentClick);
    document.addEventListener("keydown", handleTranslatorKeydown, true);
    translatorState.listenersAttached = true;
  }

  createTranslatorConsentOverlay();

  translatorState.consent = sessionStorage.getItem(TRANSLATOR_SESSION_KEY) === "true";

  if (translatorState.consent) {
    ensureGoogleTranslate().catch(err => {
      console.warn("⚠️ Google Translate could not be loaded:", err);
      updateTranslatorMessage("Google Translate could not be loaded.");
    });
  }
}

function handleTranslatorButtonClick(event) {
  event.preventDefault();
  event.stopPropagation();

  if (!translatorState.consent) {
    openTranslatorConsentDialog();
    return;
  }

  if (!translatorState.ready) {
    translatorState.pendingOpen = true;
    showTranslatorPanel();
    ensureGoogleTranslate().catch(err => {
      console.warn("⚠️ Google Translate could not be loaded:", err);
      updateTranslatorMessage("Google Translate could not be loaded.");
      translatorState.pendingOpen = false;
    });
    return;
  }

  if (translatorState.panel.hidden) {
    showTranslatorPanel();
  } else {
    hideTranslatorPanel();
  }
}

function handleTranslatorDocumentClick(event) {
  if (!translatorState.panel || translatorState.panel.hidden) return;
  if (translatorState.button && event.target === translatorState.button) return;
  if (translatorState.panel.contains(event.target)) return;
  hideTranslatorPanel();
}

function handleTranslatorKeydown(event) {
  if (event.key !== "Escape") return;

  if (translatorState.overlay && !translatorState.overlay.hidden) {
    closeTranslatorConsentDialog();
    event.stopPropagation();
    event.preventDefault();
    return;
  }

  if (translatorState.panel && !translatorState.panel.hidden) {
    hideTranslatorPanel();
    event.stopPropagation();
    event.preventDefault();
  }
}

function showTranslatorPanel() {
  if (!translatorState.panel) return;
  translatorState.panel.hidden = false;
  translatorState.button?.setAttribute("aria-expanded", "true");
}

function hideTranslatorPanel() {
  if (!translatorState.panel) return;
  translatorState.panel.hidden = true;
  translatorState.button?.setAttribute("aria-expanded", "false");
  translatorState.pendingOpen = false;
}

function createTranslatorConsentOverlay() {
  if (translatorState.overlay) return;

  const overlay = document.createElement("div");
  overlay.className = "translator-consent-overlay";
  overlay.hidden = true;
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-modal", "true");
  overlay.setAttribute("aria-labelledby", "translator-consent-title");
  overlay.innerHTML = `
    <div class="translator-consent-dialog" tabindex="-1">
      <h2 id="translator-consent-title">Activate Google Translate</h2>
      <p>We offer an optional translation feature powered by Google Translate. A connection to Google is only established after you confirm.</p>
      <p class="translator-consent-note">Without your consent, no data is sent to Google. Your decision applies to this session and can be withdrawn at any time.</p>
      <div class="translator-consent-actions">
        <button type="button" class="translator-consent-cancel" id="translator-consent-cancel">Cancel</button>
        <button type="button" class="translator-consent-accept" id="translator-consent-accept">Agree – launch Google Translate</button>
      </div>
    </div>
  `;

  // 🎨 Force glassmorphism modal styles directly (but keep it hidden initially!)
  Object.assign(overlay.style, {
    position: "fixed",
    top: "0",
    left: "0",
    width: "100vw",
    height: "100vh",
    background: "rgba(17, 25, 40, 0.7)",
    backdropFilter: "blur(8px)",
    display: "none", // 🚫 Wichtig: Versteckt beim Start!
    alignItems: "center",
    justifyContent: "center",
    zIndex: "999999",
    visibility: "hidden", // 🔒 Doppelte Sicherheit
    opacity: "0"
  });

  document.body.appendChild(overlay);
  
  // 🌟 Style the dialog box with premium glassmorphism
  const dialog = overlay.querySelector(".translator-consent-dialog");
  if (dialog) {
    Object.assign(dialog.style, {
      background: "rgba(255, 255, 255, 0.95)",
      backdropFilter: "blur(25px)",
      border: "1px solid rgba(255, 255, 255, 0.3)",
      borderRadius: "24px",
      padding: "3rem",
      maxWidth: "560px",
      width: "90%",
      boxShadow: "0 30px 100px rgba(0, 0, 0, 0.25), 0 15px 50px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.6)",
      position: "relative",
      zIndex: "1000000",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    });
    
    // Style the title
    const title = dialog.querySelector("h2");
    if (title) {
      Object.assign(title.style, {
        fontSize: "1.75rem",
        fontWeight: "700",
        color: "#1a202c",
        textAlign: "center",
        marginBottom: "1.5rem",
        letterSpacing: "-0.025em"
      });
    }
    
    // Style paragraphs
    dialog.querySelectorAll("p").forEach(p => {
      Object.assign(p.style, {
        fontSize: "1.1rem",
        lineHeight: "1.7",
        color: "#4a5568",
        marginBottom: "1.25rem"
      });
    });
    
    // Style the note
    const note = dialog.querySelector(".translator-consent-note");
    if (note) {
      Object.assign(note.style, {
        fontSize: "0.95rem",
        color: "#718096",
        fontStyle: "italic",
        marginBottom: "2.5rem"
      });
    }
  }

  translatorState.overlay = overlay;
  translatorState.dialog = dialog;
  translatorState.confirmBtn = overlay.querySelector("#translator-consent-accept");
  translatorState.cancelBtn = overlay.querySelector("#translator-consent-cancel");
  
  // 🎨 Style the action buttons
  const actions = overlay.querySelector(".translator-consent-actions");
  if (actions) {
    Object.assign(actions.style, {
      display: "flex",
      gap: "1rem",
      justifyContent: "center",
      marginTop: "2rem"
    });
  }
  
  if (translatorState.cancelBtn) {
    Object.assign(translatorState.cancelBtn.style, {
      padding: "0.875rem 2rem",
      border: "2px solid rgba(226, 232, 240, 0.8)",
      borderRadius: "14px",
      background: "rgba(248, 250, 252, 0.9)",
      color: "#2d3748",
      fontWeight: "600",
      fontSize: "1rem",
      cursor: "pointer",
      transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
      backdropFilter: "blur(10px)"
    });
    
    translatorState.cancelBtn.addEventListener("mouseenter", () => {
      Object.assign(translatorState.cancelBtn.style, {
        background: "rgba(237, 242, 247, 0.95)",
        borderColor: "rgba(203, 213, 224, 0.9)",
        transform: "translateY(-1px)",
        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)"
      });
    });
    
    translatorState.cancelBtn.addEventListener("mouseleave", () => {
      Object.assign(translatorState.cancelBtn.style, {
        background: "rgba(248, 250, 252, 0.9)",
        borderColor: "rgba(226, 232, 240, 0.8)",
        transform: "translateY(0)",
        boxShadow: "none"
      });
    });
  }
  
  if (translatorState.confirmBtn) {
    Object.assign(translatorState.confirmBtn.style, {
      padding: "0.875rem 2rem",
      border: "none",
      borderRadius: "14px",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)",
      color: "white",
      fontWeight: "600",
      fontSize: "1rem",
      cursor: "pointer",
      transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
      boxShadow: "0 6px 20px rgba(102, 126, 234, 0.4)"
    });
    
    translatorState.confirmBtn.addEventListener("mouseenter", () => {
      Object.assign(translatorState.confirmBtn.style, {
        transform: "translateY(-2px)",
        boxShadow: "0 8px 30px rgba(102, 126, 234, 0.5)"
      });
    });
    
    translatorState.confirmBtn.addEventListener("mouseleave", () => {
      Object.assign(translatorState.confirmBtn.style, {
        transform: "translateY(0)",
        boxShadow: "0 6px 20px rgba(102, 126, 234, 0.4)"
      });
    });
  }

  // 🔗 Wichtig: Event-Handler wieder hinzufügen!
  translatorState.dialog?.addEventListener("click", event => event.stopPropagation());
  translatorState.confirmBtn?.addEventListener("click", confirmTranslatorConsent);
  translatorState.cancelBtn?.addEventListener("click", closeTranslatorConsentDialog);
  overlay.addEventListener("click", event => {
    if (event.target === overlay) {
      closeTranslatorConsentDialog();
    }
  });
}

function openTranslatorConsentDialog() {
  if (!translatorState.overlay) createTranslatorConsentOverlay();
  hideTranslatorPanel();
  translatorState.previousFocus = document.activeElement;
  
  // 🎯 Show modal with glassmorphism styles
  translatorState.overlay.hidden = false;
  Object.assign(translatorState.overlay.style, {
    display: "flex",
    visibility: "visible",
    opacity: "1"
  });

  requestAnimationFrame(() => {
    translatorState.confirmBtn?.focus();
  });
}

function closeTranslatorConsentDialog() {
  if (!translatorState.overlay) return;
  
  // 🎯 Hide modal completely
  translatorState.overlay.hidden = true;
  Object.assign(translatorState.overlay.style, {
    display: "none",
    visibility: "hidden",
    opacity: "0"
  });
  
  if (translatorState.previousFocus && typeof translatorState.previousFocus.focus === "function") {
    translatorState.previousFocus.focus();
  } else {
    translatorState.button?.focus();
  }
  translatorState.previousFocus = null;
}

function confirmTranslatorConsent() {
  translatorState.consent = true;
  sessionStorage.setItem(TRANSLATOR_SESSION_KEY, "true");
  closeTranslatorConsentDialog();
  translatorState.pendingOpen = true;
  showTranslatorPanel();
  ensureGoogleTranslate().catch(err => {
    console.warn("⚠️ Google Translate could not be loaded:", err);
    updateTranslatorMessage("Google Translate could not be loaded.");
    translatorState.pendingOpen = false;
  });
}

function ensureGoogleTranslate() {
  if (translatorState.ready) return Promise.resolve();
  if (translatorState.scriptPromise) return translatorState.scriptPromise;

  updateTranslatorMessage("Google Translate is loading…");

  translatorState.scriptPromise = new Promise((resolve, reject) => {
    translatorInitResolve = resolve;
    translatorInitReject = reject;

    const script = document.createElement("script");
    script.src = "https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
    script.async = true;
    script.onerror = () => {
      script.remove();
      translatorInitResolve = null;
      translatorInitReject = null;
      translatorState.scriptPromise = null;
      updateTranslatorMessage("Google Translate could not be loaded.");
      reject(new Error("Google Translate script failed to load."));
    };
    document.head.appendChild(script);
  });

  return translatorState.scriptPromise;
}

function updateTranslatorMessage(message) {
  const msgEl = document.querySelector(".translator-loading-message");
  if (!msgEl) return;
  msgEl.textContent = message;
  msgEl.hidden = false;
}

window.googleTranslateElementInit = function googleTranslateElementInit() {
  try {
    const pageLanguage = document.documentElement.lang || "en";
    const layout = google.translate?.TranslateElement?.InlineLayout?.SIMPLE;
    // 🌍 Top 5 world languages + German: English, Mandarin Chinese, Hindi, Spanish, French, German, Arabic, Portuguese
    new google.translate.TranslateElement({
      pageLanguage,
      includedLanguages: "en,zh,hi,es,fr,de,ar,pt,ru,ja",
      layout: layout ?? undefined,
      autoDisplay: false
    }, "google_translate_element");

    translatorState.ready = true;
    translatorState.scriptPromise = Promise.resolve();

    const msgEl = document.querySelector(".translator-loading-message");
    if (msgEl) msgEl.hidden = true;

    // 🎨 Style the Google Translate panel
    setTimeout(() => {
      const panel = document.getElementById("translator-panel");
      const widget = document.getElementById("google_translate_element");
      
      if (panel) {
        Object.assign(panel.style, {
          background: "rgba(255, 255, 255, 0.95)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(255, 255, 255, 0.3)",
          borderRadius: "16px",
          boxShadow: "0 20px 60px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.5)",
          padding: "1.5rem",
          minWidth: "280px"
        });
        
        const header = panel.querySelector(".translator-panel-header");
        if (header) {
          Object.assign(header.style, {
            fontSize: "1.1rem",
            fontWeight: "600",
            color: "#1a202c",
            marginBottom: "1rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center"
          });
        }
        
        const closeBtn = panel.querySelector(".translator-close");
        if (closeBtn) {
          Object.assign(closeBtn.style, {
            background: "rgba(226, 232, 240, 0.8)",
            border: "none",
            borderRadius: "8px",
            width: "28px",
            height: "28px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "1.2rem",
            color: "#4a5568",
            cursor: "pointer",
            transition: "all 0.2s ease"
          });
        }
      }
      
      if (widget) {
        // Style Google Translate dropdown
        const select = widget.querySelector("select");
        if (select) {
          Object.assign(select.style, {
            background: "rgba(248, 250, 252, 0.9)",
            border: "2px solid rgba(226, 232, 240, 0.8)",
            borderRadius: "12px",
            padding: "0.75rem 1rem",
            fontSize: "1rem",
            color: "#2d3748",
            fontWeight: "500",
            cursor: "pointer",
            width: "100%",
            backdropFilter: "blur(5px)"
          });
        }
        
        // Hide Google branding
        const powered = widget.querySelector(".goog-logo-link");
        if (powered) powered.style.display = "none";
        
        const logo = widget.querySelector(".goog-te-gadget-simple .goog-te-menu-value span:first-child");
        if (logo) logo.style.display = "none";
      }
    }, 500);
    
    if (translatorState.pendingOpen) {
      showTranslatorPanel();
      const select = document.querySelector("#google_translate_element select");
      if (select) {
        requestAnimationFrame(() => select.focus());
      }
    }
    translatorState.pendingOpen = false;

    if (typeof translatorInitResolve === "function") translatorInitResolve();
  } catch (err) {
    translatorState.ready = false;
    translatorState.scriptPromise = null;
    translatorState.pendingOpen = false;
    updateTranslatorMessage("Google Translate could not be loaded.");
    if (typeof translatorInitReject === "function") translatorInitReject(err);
    console.warn("⚠️ googleTranslateElementInit error", err);
  } finally {
    translatorInitResolve = null;
    translatorInitReject = null;
  }
};





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



// === Deep merge helper (for Chart option overrides) ===
function deepMerge(target, ...sources) {
  if (!target) target = {};
  for (const src of sources) {
    if (!src || typeof src !== "object") continue;
    for (const [key, value] of Object.entries(src)) {
      if (
        value &&
        typeof value === "object" &&
        !Array.isArray(value) &&
        typeof target[key] === "object" &&
        !Array.isArray(target[key])
      ) {
        deepMerge(target[key], value);
      } else {
        target[key] = value;
      }
    }
  }
  return target;
}

// === Shared KPI cluster grouping ===
function groupKpisByCluster(list, options = {}) {
  const {
    filter,
    mapItem,
    sortClusters = true,
    itemSorter
  } = options;

  if (!Array.isArray(list)) return [];

  const clusters = new Map();
  for (const meta of list) {
    if (filter && !filter(meta)) continue;
    const clusterName = meta?.cluster || "Other";
    if (!clusters.has(clusterName)) clusters.set(clusterName, []);
    clusters.get(clusterName).push(mapItem ? mapItem(meta) : meta);
  }

  const entries = Array.from(clusters.entries());
  if (sortClusters) entries.sort((a, b) => a[0].localeCompare(b[0]));

  for (const [, items] of entries) {
    if (typeof itemSorter === "function") {
      items.sort(itemSorter);
    } else {
      items.sort((a, b) => {
        const aKey = (a?.title || a?.label || a?.id || "").toString();
        const bKey = (b?.title || b?.label || b?.id || "").toString();
        return aKey.localeCompare(bKey);
      });
    }
  }

  return entries;
}

// === Shared Chart.js renderer ===
const FALLBACK_CHART_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  layout: { padding: { top: 16, bottom: 12, left: 8, right: 8 } },
  interaction: { mode: "nearest", intersect: false },
  plugins: {
    title: { display: false, text: "" },
    legend: { display: true },
    tooltip: {
      enabled: true,
      callbacks: {
        title: ctx => (ctx?.length ? `Year: ${ctx[0].label ?? ""}` : ""),
        label: ctx => {
          const datasetLabel = ctx.dataset?.label ? `${ctx.dataset.label}: ` : "";
          const value = ctx.parsed?.y;
          if (value == null || isNaN(value)) {
            return `${datasetLabel}no data`;
          }
          return `${datasetLabel}${Number(value).toLocaleString()}`;
        }
      }
    }
  },
  scales: {
    y: { beginAtZero: false, grid: { color: "rgba(0,0,0,0.1)" } },
    x: {
      ticks: { autoSkip: true, maxTicksLimit: 12 },
      grid: { color: "rgba(0,0,0,0.05)" }
    }
  }
};

function cloneChartOptions(obj) {
  if (obj == null) return {};

  if (typeof structuredClone === "function") {
    try {
      return structuredClone(obj);
    } catch {
      /* ignored, fall back to manual deep clone below */
    }
  }

  return deepCloneWithFunctions(obj);
}

function deepCloneWithFunctions(value) {
  if (value == null || typeof value !== "object") {
    return value;
  }
  if (value instanceof Date) {
    return new Date(value.getTime());
  }
  if (Array.isArray(value)) {
    return value.map(item => deepCloneWithFunctions(item));
  }

  const cloned = {};
  for (const [key, entry] of Object.entries(value)) {
    if (typeof entry === "function") {
      cloned[key] = entry;
    } else {
      cloned[key] = deepCloneWithFunctions(entry);
    }
  }
  return cloned;
}

function resolveChartOptions({ title = "", unit = "", datasetCount = 0, overrides = {} }) {
  const base =
    (typeof window !== "undefined" && window.DEFAULT_CHART_OPTIONS) || FALLBACK_CHART_OPTIONS;
  const merged = cloneChartOptions(base);

  merged.plugins = merged.plugins || {};
  merged.plugins.title = merged.plugins.title || { display: false, text: "" };
  merged.plugins.title.display = !!title;
  merged.plugins.title.text = title || "";

  if (merged.plugins.legend) {
    merged.plugins.legend.display = datasetCount > 0;
  }

  merged.scales = merged.scales || {};
  merged.scales.y = merged.scales.y || {};
  merged.scales.y.title = unit
    ? { display: true, text: unit }
    : { display: false, text: "" };

  const tooltip = merged.plugins.tooltip || {};
  merged.plugins.tooltip = tooltip;
  tooltip.callbacks = tooltip.callbacks || {};
  const baseLabel = tooltip.callbacks.label;
  tooltip.callbacks.label = ctx => {
    if (typeof baseLabel === "function" && !unit) {
      return baseLabel(ctx);
    }
    const datasetLabel = ctx.dataset?.label ? `${ctx.dataset.label}: ` : "";
    const value = ctx.parsed?.y;
    if (value == null || isNaN(value)) {
      return `${datasetLabel}no data`;
    }
    const formatted = Number(value).toLocaleString();
    return unit ? `${datasetLabel}${formatted} ${unit}`.trim() : `${datasetLabel}${formatted}`;
  };
  if (!tooltip.callbacks.title) {
    tooltip.callbacks.title = ctx => (ctx?.length ? `Year: ${ctx[0].label ?? ""}` : "");
  }

  return deepMerge(merged, overrides || {});
}

function renderLineChart(canvas, config = {}) {
  if (!canvas || typeof canvas.getContext !== "function") return null;

  const {
    labels = [],
    datasets = [],
    title = "",
    unit = "",
    existingChart = null,
    fallbackDataset = null,
    options = {}
  } = config;

  const registryChart =
    existingChart && typeof existingChart.destroy === "function"
      ? existingChart
      : typeof Chart !== "undefined" && typeof Chart.getChart === "function"
      ? Chart.getChart(canvas)
      : null;

  if (registryChart?.destroy) {
    registryChart.destroy();
  }

  const attachedChart = canvas.__rcChart;
  if (attachedChart && attachedChart !== registryChart && attachedChart.destroy) {
    attachedChart.destroy();
  }
  canvas.__rcChart = null;

  const safeLabels = labels.length ? labels : [0, 1, 2];
  const baseFallback = fallbackDataset || {
    label: "No data available",
    data: safeLabels.map(() => null),
    borderColor: "rgba(180,180,180,0.5)",
    borderWidth: 1,
    pointRadius: 0,
    fill: false
  };

  const configObj = {
    type: "line",
    data: {
      labels: safeLabels,
      datasets: datasets.length ? datasets : [baseFallback]
    },
    options: resolveChartOptions({
      title,
      unit,
      datasetCount: datasets.length,
      overrides: options
    })
  };

  const ctx = canvas.getContext("2d");
  const chart = new Chart(ctx, configObj);
  canvas.__rcChart = chart;
  return chart;
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

/* ============================================================
   🧭 Unified RealityCheck Init (Header/Footer + ScrollTop + Tooltips)
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
  if (window._rcInitDone) return;
  window._rcInitDone = true;
  try {
    // --- Header/Footer werden automatisch über fetch geladen ---
    // (siehe obersten Block dieses Skripts)

    // === Iframe Loader ===
    const frame = document.getElementById("main-frame");
    const loader = document.getElementById("frame-loader");
    if (frame && loader) {
      frame.addEventListener("load", () => loader.classList.remove("active"));
    }

    // === Scroll-to-Top Button ===
    const btn = document.getElementById("scroll-top-btn");
    if (btn) {
      const frame = document.getElementById("main-frame");
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
      btn.style.opacity = "0.9";
      btn.style.pointerEvents = "auto";
    }

    // === Mobile Mode Tooltips (nur auf kleinen Geräten) ===
    if (window.innerWidth <= 600) {
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

    console.log("✅ RealityCheck core init complete");
  } catch (err) {
    console.error("❌ RealityCheck init failed:", err);
  }

  // ✅ Exportiere IIFE-interne Funktionen global
  window.normalizeName = normalizeName;
  window.resolveCountryName = resolveCountryName;
  window.calculateGroupValues = calculateGroupValues;
  window.groupKpisByCluster = groupKpisByCluster;
  window.rcLog = rcLog;
  window.loadAllKPIData = loadAllKPIData;
  window.renderLineChart = renderLineChart;
  window.loadKpiAnalysis = loadKpiAnalysis;
  window.renderKpiAnalysis = renderKpiAnalysis;
});

  })();
}

