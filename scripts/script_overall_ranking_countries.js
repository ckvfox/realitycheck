/* ============================================================
   🌍 RealityCheck – Overall Country Ranking Script (Final 2025-10)
   ============================================================ */

let kpis = [];
let countries = [];
let missingKPIs = [];
let ALL_DATA = {}; // consolidated dataset from all_kpis_data.json

const RELEVANCE_WEIGHTS = {
  very_high: 1.0,
  high: 0.7,
  normal: 0.4,
  low: 0.2,
  irrelevant: 0.0
};

const EXCLUDE_COUNTRIES = new Set(["World"]);


/* ---------- Google Translate Detection ---------- */
let googleTranslateActive = false;
let originalTexts = {};
let translateCheckInterval = null;

function isGoogleTranslateActive() {
  return googleTranslateActive;
}

function captureOriginalTexts() {
  // Capture original English texts to compare against
  const funBtn = document.querySelector('#funMode');
  const safeBtn = document.querySelector('#safeMode');
  const immigBtn = document.querySelector('#immigrationMode');
  
  originalTexts = {
    funButton: funBtn ? funBtn.textContent.trim() : 'Fun',
    safeButton: safeBtn ? safeBtn.textContent.trim() : 'Safe Haven', 
    immigrationButton: immigBtn ? immigBtn.textContent.trim() : 'Immigration',
    pageTitle: document.title,
    headerTexts: Array.from(document.querySelectorAll('h1, h2, h3')).map(el => el.textContent.trim())
  };
  console.log('📝 [GoogleTranslate] Captured original texts:', originalTexts);
}

function detectGoogleTranslateByContent() {
  console.log('🔍 [GoogleTranslate] Checking for translation by content changes...');
  console.log('🔍 [GoogleTranslate] Original texts available:', !!originalTexts, originalTexts);
  
  let translationDetected = false;
  const checks = [];
  
  // Method 1: Check if buttons have been translated by comparing to original text
  const funButton = document.querySelector('#funMode');
  const safeButton = document.querySelector('#safeMode');  
  const immigrationButton = document.querySelector('#immigrationMode');
  
  console.log('🔍 [GoogleTranslate] Button elements found:', {
    funButton: !!funButton,
    safeButton: !!safeButton, 
    immigrationButton: !!immigrationButton
  });
  
  if (funButton) {
    const currentText = funButton.textContent.trim();
    const originalText = originalTexts?.funButton || 'Fun';
    console.log(`🔍 [GoogleTranslate] Fun button analysis: current="${currentText}", original="${originalText}"`);
    checks.push(`Fun button: "${currentText}" (original: "${originalText}")`);
    
    // Only check for German if text actually changed from original
    if (currentText !== originalText) {
      const lowerText = currentText.toLowerCase();
      if (lowerText.includes('spaß') || lowerText.includes('lustig') || 
          lowerText.includes('unterhalts') || lowerText.includes('vergnüg')) {
        translationDetected = true;
        checks.push('✓ German translation detected in Fun button');
      } else {
        checks.push(`? Fun button text changed but not German: "${currentText}"`);
      }
    }
  }
  
  if (safeButton) {
    const currentText = safeButton.textContent.trim();
    const originalText = originalTexts?.safeButton || 'Safe Haven';
    console.log(`🔍 [GoogleTranslate] Safe button analysis: current="${currentText}", original="${originalText}"`);
    checks.push(`Safe button: "${currentText}" (original: "${originalText}")`);
    
    // Only check for German if text actually changed from original
    if (currentText !== originalText) {
      const lowerText = currentText.toLowerCase();
      if (lowerText.includes('sicher') || lowerText.includes('zufluchts') || 
          lowerText.includes('sichere') || lowerText.includes('hafen')) {
        translationDetected = true;
        checks.push('✓ German translation detected in Safe button');
      } else {
        checks.push(`? Safe button text changed but not German: "${currentText}"`);
      }
    }
  }
  
    if (immigrationButton) {
    const currentText = immigrationButton.textContent.trim();
    const originalText = originalTexts?.immigrationButton || 'Immigration';
    console.log(`🔍 [GoogleTranslate] Immigration button analysis: current="${currentText}", original="${originalText}"`);
    checks.push(`Immigration button: "${currentText}" (original: "${originalText}")`);
    
    // Only check for German if text actually changed from original
    if (currentText !== originalText) {
      const lowerText = currentText.toLowerCase();
      if (lowerText.includes('einwander') || lowerText.includes('zuwander')) {
        translationDetected = true;
        checks.push('✓ German translation detected in Immigration button');
      } else {
        checks.push(`? Immigration button text changed but not German: "${currentText}"`);
      }
    }
  }  // Method 2: Check page title
  const currentTitle = document.title;
  const originalTitle = originalTexts?.pageTitle || 'RealityCheck – Overall Country Ranking';
  console.log(`🔍 [GoogleTranslate] Title analysis: current="${currentTitle}", original="${originalTitle}"`);
  
  if (currentTitle !== originalTitle) {
    checks.push(`Title changed: "${currentTitle}" (original: "${originalTitle}")`);
    const lowerTitle = currentTitle.toLowerCase();
    if (lowerTitle.includes('länder') || lowerTitle.includes('rangfolge') || 
        lowerTitle.includes('realitätsprüfung') || lowerTitle.includes('übersicht')) {
      translationDetected = true;
      checks.push('✓ German translation detected in page title');
    }
  } else {
    checks.push('Title unchanged');
  }
  
  // Method 3: Fallback - check Google Translate selects if available
  const allSelects = Array.from(document.querySelectorAll('select'));
  console.log(`🔍 [GoogleTranslate] Found ${allSelects.length} select elements`);
  
  let googleTranslateSelects = 0;
  allSelects.forEach((select, i) => {
    if (select.className.includes('goog-te') || select.parentElement?.id === 'google_translate_element') {
      googleTranslateSelects++;
      const selectedText = select.options[select.selectedIndex]?.text || 'N/A';
      console.log(`🔍 [GoogleTranslate] Google Translate select ${i}: value="${select.value}", text="${selectedText}"`);
      checks.push(`Google Translate select ${i}: value="${select.value}" (${selectedText})`);
      
      if (select.value && select.value !== '' && select.value !== 'en' && select.value !== 'auto') {
        translationDetected = true;
        checks.push(`✓ Active translation via dropdown: "${select.value}"`);
      }
    }
  });
  console.log(`🔍 [GoogleTranslate] Found ${googleTranslateSelects} Google Translate selects`);
  
  // Method 4: Check HTML lang attribute change
  const htmlLang = document.documentElement.getAttribute('lang') || 'en';
  console.log(`🔍 [GoogleTranslate] HTML lang: "${htmlLang}"`);
  checks.push(`HTML lang: "${htmlLang}"`);
  
  if (htmlLang && htmlLang !== 'en' && htmlLang !== '') {
    if (htmlLang === 'de' || htmlLang.startsWith('de-')) {
      translationDetected = true;
      checks.push('✓ German language detected in HTML lang attribute');
    } else {
      checks.push(`? Non-English lang detected: "${htmlLang}"`);
    }
  }
  
  // Method 5: Check for Google Translate CSS classes
  const bodyClasses = document.body.className;
  const htmlClasses = document.documentElement.className;
  console.log(`🔍 [GoogleTranslate] CSS classes - body: "${bodyClasses}", html: "${htmlClasses}"`);
  
  if (bodyClasses.includes('translated') || htmlClasses.includes('translated')) {
    translationDetected = true;
    checks.push('✓ Google Translate CSS classes detected');
  } else {
    checks.push('No translation CSS classes found');
  }
  
  console.log('🔍 [GoogleTranslate] Detection results:', checks);
  console.log(`🎯 [GoogleTranslate] Final result: ${translationDetected ? 'TRANSLATION ACTIVE' : 'NO TRANSLATION'}`);
  
  return translationDetected;
}

function debugGoogleTranslateState() {
  console.log('🐛 [DEBUG] Current Google Translate State:');
  console.log('- Widget present:', !!document.querySelector('#google_translate_element'));
  
  // Show ALL selects with detailed info
  const allSelects = Array.from(document.querySelectorAll('select'));
  console.log('- Total selects found:', allSelects.length);
  allSelects.forEach((select, i) => {
    console.log(`  Select ${i}:`, {
      id: select.id,
      className: select.className,
      value: select.value,
      selectedIndex: select.selectedIndex,
      optionText: select.options[select.selectedIndex]?.text,
      parentElement: select.parentElement?.className,
      isVisible: select.offsetParent !== null
    });
  });
  
  console.log('- Body classes:', document.body.className);
  console.log('- HTML classes:', document.documentElement.className);
  console.log('- HTML lang:', document.documentElement.getAttribute('lang'));
  console.log('- Current googleTranslateActive:', googleTranslateActive);
  
  // Check button states and texts
  ['#funMode', '#safeMode', '#immigrationMode'].forEach(sel => {
    const btn = document.querySelector(sel);
    if (btn) {
      console.log(`- ${sel}:`, {
        text: btn.textContent.trim(),
        disabled: btn.disabled,
        style: btn.style.cssText
      });
    }
  });
  
  // Check for Google Translate specific elements
  console.log('- Google Translate iframe:', !!document.querySelector('iframe[src*="translate.googleapis.com"]'));
  console.log('- Google Translate spans:', document.querySelectorAll('span[class*="goog-te"]').length);
  console.log('- Google Translate divs:', document.querySelectorAll('div[class*="goog-te"]').length);
}

function monitorGoogleTranslate() {
  console.log('🚀 [GoogleTranslate] Setting up enhanced detection...');
  
  // Capture original texts first
  captureOriginalTexts();
  
  // Clear any existing interval
  if (translateCheckInterval) {
    clearInterval(translateCheckInterval);
  }
  
  const checkForTranslation = () => {
    const wasActive = googleTranslateActive;
    const isActive = detectGoogleTranslateByContent();
    
    if (isActive !== wasActive) {
      googleTranslateActive = isActive;
      console.log(`🔄 [GoogleTranslate] Status changed: ${isActive ? 'ACTIVE' : 'INACTIVE'}`);
      debugGoogleTranslateState(); // Add debug info when state changes
      updateGoogleTranslateWarning();
    }
  };
  
  // Initial debug
  setTimeout(() => {
    debugGoogleTranslateState();
    checkForTranslation();
  }, 1000);
  
  // Check every 3 seconds (less frequent to reduce noise)
  translateCheckInterval = setInterval(checkForTranslation, 3000);
  
  // Set up mutation observer only for Google Translate specific changes
  const observer = new MutationObserver((mutations) => {
    let shouldCheck = false;
    
    mutations.forEach(mutation => {
      if (mutation.type === 'attributes' && 
          mutation.target &&
          (mutation.target.classList?.contains('goog-te-combo') ||
           mutation.target.id === 'google_translate_element' ||
           mutation.attributeName === 'lang')) {
        shouldCheck = true;
      }
    });
    
    if (shouldCheck) {
      console.log('🔄 [GoogleTranslate] Mutation detected - checking...');
      setTimeout(checkForTranslation, 200);
    }
  });
  
  // More targeted observation
  const translateWidget = document.querySelector('#google_translate_element');
  if (translateWidget) {
    observer.observe(translateWidget, {
      subtree: true,
      attributes: true,
      childList: true
    });
  }
  
  // Also observe document for lang changes
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['lang']
  });
  
  console.log('✅ [GoogleTranslate] Enhanced detection system active');
  
  // Add manual debug function to window
  window.debugGoogleTranslate = debugGoogleTranslateState;
}

function updateGoogleTranslateWarning() {
  const modeSection = document.getElementById('mode-switch');
  let warningDiv = document.getElementById('google-translate-warning');
  
  const isActive = isGoogleTranslateActive();
  
  console.log('🔄 [GoogleTranslate] Updating warning display:', {
    isActive,
    modeSection: !!modeSection,
    warningExists: !!warningDiv
  });
  
  if (isActive) {
    console.warn('⚠️ [GoogleTranslate] SHOWING WARNING - Translation is active');
    
    // Show warning if Google Translate is detected
    if (!warningDiv && modeSection) {
      warningDiv = document.createElement('div');
      warningDiv.id = 'google-translate-warning';
      warningDiv.className = 'notranslate';
      warningDiv.setAttribute('translate', 'no');
      warningDiv.setAttribute('data-google-translate', 'no');
      warningDiv.style.cssText = `
        background: #ff9800 !important;
        border: 3px solid #f57c00 !important;
        border-radius: 8px;
        padding: 15px;
        margin: 15px 0;
        font-weight: bold;
        color: #333 !important;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        font-size: 16px;
        z-index: 1000;
        position: relative;
      `;
      warningDiv.innerHTML = `
        <span class="notranslate">⚠️ <strong>WARNING: Fun/Safe/Immigration modes are disabled during translation!</strong><br>
        <small>Please switch back to the original language to use these ranking modes.</small></span>
      `;
      
      // Insert after mode section
      if (modeSection.parentNode) {
        modeSection.parentNode.insertBefore(warningDiv, modeSection.nextSibling);
      } else {
        // Fallback: insert at top of main content
        const mainContent = document.querySelector('main') || document.body;
        mainContent.insertBefore(warningDiv, mainContent.firstChild);
      }
      
      console.log('✅ [GoogleTranslate] Warning box created and inserted');
    }
    
    // Disable mode buttons (except Normal) - try multiple selectors
    const buttonSelectors = [
      '#funMode', '#safeMode', '#immigrationMode',
      '.mode-button:not(#normalMode)',
      '#mode-switch .mode-button:not(#normalMode)',
      '[data-mode="fun"]', '[data-mode="safe"]', '[data-mode="immigration"]'
    ];
    
    buttonSelectors.forEach(selector => {
      document.querySelectorAll(selector).forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = '0.3';
        btn.style.pointerEvents = 'none';
        btn.style.cursor = 'not-allowed';
        btn.title = 'Deaktiviert während der Übersetzung';
        console.log(`🚫 [GoogleTranslate] Disabled button: ${selector}`);
      });
    });
    
  } else {
    console.log('✅ [GoogleTranslate] HIDING WARNING - Translation is inactive');
    
    // Remove warning and re-enable buttons
    if (warningDiv) {
      warningDiv.remove();
      console.log('🗑️ [GoogleTranslate] Warning box removed');
    }
    
    // Re-enable all mode buttons
    const buttonSelectors = [
      '#funMode', '#safeMode', '#immigrationMode',
      '.mode-button',
      '#mode-switch .mode-button',
      '[data-mode]'
    ];
    
    buttonSelectors.forEach(selector => {
      document.querySelectorAll(selector).forEach(btn => {
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.style.pointerEvents = 'auto';
        btn.style.cursor = 'pointer';
        btn.title = '';
        console.log(`✅ [GoogleTranslate] Re-enabled button: ${selector}`);
      });
    });
  }
}

/* ---------- Init ---------- */
async function initOverall() {
  showSpinner(true, "Building Overall Ranking…");

  kpis = await loadJSON("data/meta/available_kpis.json");
  countries = await loadJSON("data/meta/countries.json");
  ALL_DATA = await loadAllKPIData(); // ✅ consolidated dataset

  buildRelevanceControls();
	await buildOverallRanking();   // 🧩 Ranking berechnen und Tabelle rendern
  await loadFunSafeImmigrationSets();

  // Setup Google Translate monitoring  
  monitorGoogleTranslate();
  updateGoogleTranslateWarning(); // Initial check

  showSpinner(false);
  fetchLastUpdated();
  
}
// ============================================================
// 🌈 Mode Switch (Normal / Fun / Safe Haven / Immigration)
// ============================================================
function initModeSwitch() {
  if (document.getElementById("mode-switch-initialized")) return;
  const marker = document.createElement("div");
  marker.id = "mode-switch-initialized";
  document.body.appendChild(marker);

  // Buttons
  const normalBtn = document.getElementById("normalMode");
  const funBtn    = document.getElementById("funMode");
  const safeBtn   = document.getElementById("safeMode");
  const immigrBtn = document.getElementById("immigrationMode");

  if (!normalBtn || !funBtn || !safeBtn || !immigrBtn) {
    console.warn("⚠️ Mode buttons not found");
    return;
  }

  // === Global-State benutzen (nicht lokale let!) ===
  window.funOn = false;
  window.safeOn = false;
  window.immigrOn = false;

  // === Helper ===
  const updateLabel = (btn, text) => {
    const spans = btn.querySelectorAll("span");
    if (spans[1]) spans[1].textContent = text;
  };

  // === Reset ===
  normalBtn.addEventListener("click", () => {
    document.querySelectorAll("#mode-switch button").forEach(b => b.classList.remove("active"));
    normalBtn.classList.add("active");

    funOn = safeOn = immigrOn = false;
    updateLabel(funBtn, "Fun");
    updateLabel(safeBtn, "Safe");
    updateLabel(immigrBtn, "Immigration");

    updateModeIcons();
  });

  // === Fun toggle ===
  funBtn.addEventListener("click", () => {
    funOn = !funOn;
    funBtn.classList.toggle("active", funOn);
    updateLabel(funBtn, funOn ? "Fun Mode activated" : "Fun");
    updateModeIcons();
  });

  // === Safe toggle ===
  safeBtn.addEventListener("click", () => {
    safeOn = !safeOn;
    safeBtn.classList.toggle("active", safeOn);
    updateLabel(safeBtn, safeOn ? "Safe Haven activated" : "Safe");
    updateModeIcons();
  });

  // === Immigration toggle ===
  immigrBtn.addEventListener("click", () => {
    immigrOn = !immigrOn;
    immigrBtn.classList.toggle("active", immigrOn);
    updateLabel(immigrBtn, immigrOn ? "Immigration activated" : "Immigration");
    updateModeIcons();
  });
}

if (typeof onDocumentReady === "function") {
  onDocumentReady(initModeSwitch);
} else {
  document.addEventListener("DOMContentLoaded", initModeSwitch);
}



/* ---------- Build KPI Cluster Boxes ---------- */
function buildRelevanceControls() {
  const container = document.getElementById("priority-container");
  container.innerHTML = "";

  const relevantGroups = groupKpisByCluster(kpis, {
    filter: k =>
      ["higher", "lower", "target"].includes(k.sort) &&
      k.world_kpi !== "e" &&
      (k.relevance ?? "normal") !== "none",
    itemSorter: (a, b) => (a.title || "").localeCompare(b.title || "")
  });

  for (const [clusterName, list] of relevantGroups) {
    const group = document.createElement("div");
    group.className = "cluster-box";
    const h3 = document.createElement("h3");
    h3.textContent = clusterName;
    group.appendChild(h3);

    list.forEach(meta => {
      const row = document.createElement("div");
      row.className = "kpi-row";
      const label = document.createElement("label");
      label.textContent = meta.title + ": ";

      const sel = document.createElement("select");
      ["very_high", "high", "normal", "low", "irrelevant"].forEach(opt => {
        const o = document.createElement("option");
        o.value = opt;
        o.textContent = opt.replace("_", " ");
        if (opt === (meta.relevance || "normal")) o.selected = true;
        sel.appendChild(o);
      });

      sel.dataset.kpi = meta.filename;
      row.appendChild(label);
      row.appendChild(sel);
      group.appendChild(row);
    });

    container.appendChild(group);
  }

  // Buttons
  const btnBox = document.getElementById("priority-buttons");
  btnBox.innerHTML = `
    <button id="calc-btn">Calculate</button>
    <button id="reset-btn">Reset</button>
  `;

  // Restore saved weights
  const saved = localStorage.getItem("overallKPIWeights");
  if (saved) {
    const map = JSON.parse(saved);
    for (const meta of kpis) {
      if (map[meta.filename]) meta.relevance = map[meta.filename];
      const sel = container.querySelector(`select[data-kpi="${meta.filename}"]`);
      if (sel && map[meta.filename]) sel.value = map[meta.filename];
    }
  }

  // Events
  document.getElementById("calc-btn").addEventListener("click", async () => {
    for (const meta of kpis) {
      const sel = container.querySelector(`select[data-kpi="${meta.filename}"]`);
      if (sel) meta.relevance = sel.value;
    }
    localStorage.setItem(
      "overallKPIWeights",
      JSON.stringify(Object.fromEntries(kpis.map(m => [m.filename, m.relevance || "normal"])))
    );
    showToast("KPI selection saved");
    await buildOverallRanking();
  });

  document.getElementById("reset-btn").addEventListener("click", () => {
    localStorage.removeItem("overallKPIWeights");
    location.reload();
  });

	// === Änderungen an Gewichtungen überwachen ===
	container.querySelectorAll("select").forEach(sel => {
		sel.addEventListener("change", () => {
			hasChangedSinceLastCalc = true;
		});
	});

	// === Calculate-Button: Ranking + GDPR-Popup nur bei echten Änderungen ===
	document.getElementById("calc-btn").addEventListener("click", async () => {
		for (const meta of kpis) {
			const sel = container.querySelector(`select[data-kpi="${meta.filename}"]`);
			if (sel) meta.relevance = sel.value;
		}

		localStorage.setItem(
			"overallKPIWeights",
			JSON.stringify(Object.fromEntries(kpis.map(m => [m.filename, m.relevance || "normal"])))
		);

		showToast("KPI selection saved");

		// Nur zeigen, wenn etwas verändert wurde
		if (hasChangedSinceLastCalc) {
			createInfoBox();
			hasChangedSinceLastCalc = false;
		}

		await buildOverallRanking();
	});

}

/* ---------- Build Overall Ranking ---------- */
async function buildOverallRanking() {
  const valid = kpis.filter(
    k =>
      ["higher", "lower", "target"].includes(k.sort) &&
      k.world_kpi !== "e" &&
      (k.relevance ?? "normal") !== "none"
  );

  const aggregated = {};
  missingKPIs = [];

  for (const meta of valid) {
    const id = meta.filename;
    const weight = getRelevanceWeight(meta.relevance);
    try {
      const data = ALL_DATA[id] || [];
      if (!Array.isArray(data) || data.length === 0) continue;

      const numeric = data.filter(d => !isNaN(parseFloat(d.value)));
      if (numeric.length < 2) continue;

      // pro Land neuestes Jahr
      const latestByCountry = new Map();
      for (const d of numeric) {
        if (!d.country) continue;
        const prev = latestByCountry.get(d.country);
        if (!prev || (d.year ?? -Infinity) > (prev.year ?? -Infinity))
          latestByCountry.set(d.country, d);
      }
      const latest = Array.from(latestByCountry.values());
      if (latest.length < 2) continue;

      const min = Math.min(...latest.map(d => parseFloat(d.value)));
      const max = Math.max(...latest.map(d => parseFloat(d.value)));
      const range = max - min || 1;

      for (const d of latest) {
        const c = d.country;
        let norm = (parseFloat(d.value) - min) / range;
        if (meta.sort === "lower") norm = 1 - norm;
        const val = norm * weight;

        if (!aggregated[c]) aggregated[c] = { sum: 0, count: 0 };
        aggregated[c].sum += val;
        aggregated[c].count++;
      }
    } catch (e) {
      console.warn(`⚠️ KPI ${id} failed:`, e);
      missingKPIs.push(meta.title);
    }
  }

  const prioritizedCount = valid.length;

  const list = Object.entries(aggregated)
    .map(([country, obj]) => ({
      country,
      score: obj.count > 0 ? obj.sum / obj.count : 0,
      used: obj.count,
      coverage: prioritizedCount ? obj.count / prioritizedCount : 0
    }))
    .filter(r => r.coverage >= 0.6); // Mindestabdeckung 60 %

  list.sort((a, b) => b.score - a.score);

  renderOverallTable(list);
  renderLegend(prioritizedCount, missingKPIs);
  initModeSwitch();          // Buttons sicher initialisieren (einmalig)
  updateModeIcons();         // Icons gemäß aktuellem Toggle-Status (Default: aus)


}
// === Global state ===
let FUN_SET = new Set();
let SAFE_SET = new Set();
let IMMIG_SET = new Set();  // 🧳 neu
let funOn = false;
let safeOn = false;
let immigrOn = false;       // 🧳 neu


// === Lädt Top-10 Sets EINMAL (robust gegen GPT-JSON-Formate) ===
async function loadFunSafeImmigrationSets() {
  try {
    const [funRaw, safeRaw, immigrRaw] = await Promise.all([
      fetch("data/fun_ranking.json").then(r => r.ok ? r.json() : []),
      fetch("data/safe_haven_ranking.json").then(r => r.ok ? r.json() : []),
      fetch("data/immigration_ranking.json").then(r => r.ok ? r.json() : []) // 🧳 neu
    ]);

    const funList = Array.isArray(funRaw)
      ? funRaw
      : funRaw["Fun Ranking"] || funRaw.countries || Object.values(funRaw);

    const safeList = Array.isArray(safeRaw)
      ? safeRaw
      : safeRaw["Safe Haven Ranking"] || safeRaw.countries || Object.values(safeRaw);

    const immigrList = Array.isArray(immigrRaw)
      ? immigrRaw
      : immigrRaw["Immigration Mode"] || immigrRaw.countries || Object.values(immigrRaw);

    FUN_SET = new Set((funList || []).slice(0, 10).map(e => e.country || e));
    SAFE_SET = new Set((safeList || []).slice(0, 10).map(e => e.country || e));
    IMMIG_SET = new Set((immigrList || []).slice(0, 10).map(e => e.country || e)); // 🧳 neu

    console.log("😎 FUN_SET loaded:", [...FUN_SET]);
    console.log("🛡️ SAFE_SET loaded:", [...SAFE_SET]);
    console.log("🧳 IMMIG_SET loaded:", [...IMMIG_SET]);
  } catch (e) {
    console.warn("⚠️ Could not load fun/safe/immigration sets:", e);
    FUN_SET = new Set();
    SAFE_SET = new Set();
    IMMIG_SET = new Set();
  }
}


// === Fügt/entfernt ausschließlich die Icons gemäß funOn/safeOn ===
function updateModeIcons() {
  document.querySelectorAll("#overall-table tbody tr").forEach(tr => {
    const nameCell = tr.children[1];
    if (!nameCell) return;

    // alte Icons entfernen
    nameCell.querySelectorAll(".mode-icons").forEach(n => n.remove());

    const country = nameCell.textContent.trim();
    let icons = "";
    if (funOn && FUN_SET.has(country)) icons += "😎";
    if (safeOn && SAFE_SET.has(country)) icons += "🛡️";
	if (immigrOn && IMMIG_SET.has(country)) icons += "🧳";

    if (icons) {
      const span = document.createElement("span");
      span.className = "mode-icons";
      span.textContent = " " + icons;
      nameCell.appendChild(span);
    }
  });
}


/* ---------- Weight Helper ---------- */
function getRelevanceWeight(r) {
  return RELEVANCE_WEIGHTS[r] ?? 0.4;
}

/* ---------- Render Table ---------- */
function renderOverallTable(list) {
  const tbody = document.querySelector("#overall-table tbody");
  if (!tbody) return;
  tbody.textContent = "";

  if (!list.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 4;
    td.textContent = "No countries meet the 60 % data coverage requirement.";
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  const total = list.length;
  list.forEach((entry, i) => {
    const rank = i + 1;
    const medal = rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : rank;
    const tr = document.createElement("tr");

    const rankCell = document.createElement("td");
    rankCell.textContent = medal;
    tr.appendChild(rankCell);

    const countryCell = document.createElement("td");
    countryCell.textContent = entry.country;
    tr.appendChild(countryCell);

    const scoreCell = document.createElement("td");
    scoreCell.textContent = (entry.score * 100).toFixed(2);
    tr.appendChild(scoreCell);

    const usedCell = document.createElement("td");
    usedCell.textContent = entry.used;
    tr.appendChild(usedCell);

    if (rank <= 10) tr.classList.add("top10");
    if (rank > total - 10) tr.classList.add("flop10");
    tbody.appendChild(tr);
  });

  const lastUpdated = document.getElementById("last-updated");
  if (lastUpdated) {
    const d = new Date();
    lastUpdated.textContent = "Last calculated: " + d.toISOString().slice(0, 10);
  }
}
/* ---------- Legend (unter Tabelle) ---------- */
function renderLegend(prioritizedCount, missing = []) {
  let leg = document.getElementById("legend");
  const table = document.getElementById("overall-table");
  const wrapper = table?.closest(".table-wrapper");

  if (!leg) {
    leg = document.createElement("div");
    leg.id = "legend";
    if (wrapper) {
      wrapper.insertAdjacentElement("afterend", leg);
    } else if (table) {
      table.insertAdjacentElement("afterend", leg);
    }
  } else if (wrapper && leg.parentElement !== wrapper.parentElement) {
    wrapper.insertAdjacentElement("afterend", leg);
  }

  const escapeValue =
    typeof window !== "undefined" && typeof window.escapeHTML === "function"
      ? window.escapeHTML
      : value => (value ?? "").toString();

  const missingList = missing.length
    ? `<div class="missing-kpis"><strong>📉 KPIs currently without country-level data:</strong><br><span>${missing
        .map(item => escapeValue(item))
        .join(", ")}</span></div>`
    : "";

  leg.innerHTML = `
    <div class="legend-block">
      <h3>📊 How the Overall Ranking Works</h3>
      <p>
        For each KPI the <b>latest country value</b> is normalized to <code>[0,1]</code>:
      </p>
      <pre class="legend-code">
norm = (value - min) / (max - min)
if sort == "lower": norm = 1 - norm
weighted = norm × relevance_weight
score(country) = Σ(weighted) / KPIs_used
      </pre>
      <ul>
        <li>🚫 Only indicators that make sense for such comparison are included.</li>
        <li>⚖️ Only countries with <b>≥ 60 %</b> KPI coverage appear in the ranking.</li>
        <li>🥇 Top 10 rows highlighted green 💔 Bottom 10 red</li>
      </ul>
      <p><b>${prioritizedCount}</b> KPIs with data included in calculation.</p>
      ${missingList}
    </div>

    <div class="legend-block">
      <h3>🌍 Mode Highlights</h3>
      <p><strong>😎 Fun Mode:</strong> Warm, sunny, happy and relaxed. Good beer, reasonably priced</p>
      <p><strong>🛑️ Safe Haven Mode:</strong> Peaceful, resilient, and rights-respecting democracies with low climate risk.</p>
	  <p><strong>🧳 Immigration Mode:</strong> Countries open to immigration, with job opportunities and welcoming integration culture.</p>
    </div>
  `;
}
/* ---------- Info Box (GDPR notice – show only after Calculate if changed) ---------- */
let hasChangedSinceLastCalc = false;

function createInfoBox() {
  // Bestehende Box wiederverwenden, falls sie noch da ist
  let box = document.getElementById("localinfo-box");
  if (!box) {
    box = document.createElement("div");
    box.id = "localinfo-box";
    box.innerHTML = `
      <strong>ℹ️ Info:</strong> Your weighting settings are stored <b>locally</b> in your browser.<br>
      No cookies and no data are sent anywhere.
      <button id="close-localinfo">×</button>
    `;
    document.body.appendChild(box);
    box.querySelector("#close-localinfo")?.addEventListener("click", () => box.remove());
  }

  // Sanft einblenden (zentriert)
  requestAnimationFrame(() => box.classList.add("show"));

  // Langsamer ausblenden (nach 4 s sichtbar, danach 5 s Fade)
  clearTimeout(box._timeout);
  box._timeout = setTimeout(() => box.classList.remove("show"), 4000);
  setTimeout(() => box.remove(), 5000);
}


/* ---------- Last Updated ---------- */
async function fetchLastUpdated() {
  try {
    const r = await fetch("data/fetch_status.json");
    if (!r.ok) return;
    const j = await r.json();
    if (j.last_fetch)
      document.getElementById("last-updated").textContent =
        "Last data update: " + new Date(j.last_fetch).toLocaleDateString();
  } catch {}
}

/* ---------- Start ---------- */
if (typeof onDocumentReady === "function") {
  onDocumentReady(initOverall);
} else {
  window.addEventListener("DOMContentLoaded", initOverall);
}
