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
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        title: { display: false }
      },
      scales: {
        y: { beginAtZero: false }
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

/* ========= World Map Gruppierungs-Feature ========= */
let worldMap = null;
let worldMapLayer = null;
let worldMapCountries = {};
let worldMapGroups = {};
let worldMapPopulation = {};
let worldMapCountryMappings = {};

async function initWorldMap() {
  try {
    // Lade Daten
    worldMapCountries = await loadJSON("data/meta/countries.json");
    worldMapGroups = await loadJSON("data/meta/groups.json");
    worldMapCountryMappings = await loadJSON("data/meta/country_mappings.json");
    const populationData = await loadJSON("data/population.json");
    
    // Verarbeite Population-Daten für Tooltips
    populationData.forEach(entry => {
      const key = `${entry.country}_${entry.year}`;
      worldMapPopulation[key] = entry.value;
    });

    // Lade GeoJSON für Länder-Polygone
    await loadWorldGeoJSON();

    // Initialisiere Karte
    const mapElement = document.getElementById('world-map');
    if (!mapElement) return;

    worldMap = L.map('world-map').setView([20, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18
    }).addTo(worldMap);

    // Event Listeners für Dropdowns
    const groupingSelect = document.getElementById('groupingSelect');
    const categorySelect = document.getElementById('categorySelect');
    
    if (groupingSelect) {
      groupingSelect.addEventListener('change', updateCategoryOptions);
    }
    
    if (categorySelect) {
      categorySelect.addEventListener('change', updateWorldMapGeoJSON);
    }

  } catch (err) {
    console.error("🗺️ World Map init failed:", err);
  }
}

async function loadWorldGeoJSON() {
  try {
    // 📦 GeoJSON laden (lokal oder Fallback)
    const res = await fetch("data/meta/world_countries_geo.json", { cache: "no-store" });
    if (!res.ok) throw new Error("Local GeoJSON missing");
    window._worldGeoJSON = await res.json();
    console.log("🌍 world_countries_geo.json loaded for World Map");
  } catch (err) {
    console.warn("⚠️ Fallback: loading GeoJSON from GitHub for World Map");
    try {
      const backup = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson";
      const res2 = await fetch(backup);
      if (!res2.ok) throw new Error("Backup GeoJSON failed");
      window._worldGeoJSON = await res2.json();
      console.log("🌍 Loaded fallback GeoJSON for World Map");
    } catch (err2) {
      console.error("❌ GeoJSON load failed for World Map:", err2);
    }
  }
}

function updateCategoryOptions() {
  const groupingSelect = document.getElementById('groupingSelect');
  const categorySelect = document.getElementById('categorySelect');
  
  if (!groupingSelect || !categorySelect) return;
  
  const grouping = groupingSelect.value;
  categorySelect.innerHTML = '<option value="">Select category...</option>';
  categorySelect.disabled = !grouping;
  
  if (grouping === 'groups') {
    // Füge Groups aus groups.json hinzu
    Object.keys(worldMapGroups).forEach(groupName => {
      const option = document.createElement('option');
      option.value = groupName;
      const members = worldMapGroups[groupName].members || worldMapGroups[groupName];
      const memberCount = Array.isArray(members) ? members.length : 0;
      option.textContent = `${groupName} (${memberCount} countries)`;
      categorySelect.appendChild(option);
    });
  } else if (grouping === 'government' || grouping === 'language') {
    // Sammle einzigartige Werte aus countries.json
    const values = new Set();
    Object.values(worldMapCountries).forEach(country => {
      let value = country[grouping];
      
      // Spezielle Behandlung für languages
      if (grouping === 'language') {
        value = country.languages || country.language;
        
        // Behandle komma-getrennte Sprachen
        if (value && typeof value === 'string' && value.includes(',')) {
          value.split(',').forEach(lang => {
            const trimmed = lang.trim();
            if (trimmed) values.add(trimmed);
          });
          return; // Skip the rest of the processing for this country
        }
      }
      
      if (value && Array.isArray(value)) {
        value.forEach(v => {
          if (v && typeof v === 'string') values.add(v.trim());
        });
      } else if (value && typeof value === 'string') {
        values.add(value.trim());
      }
    });
    
    // Sortiere und füge Optionen hinzu
    Array.from(values).sort().forEach(value => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = value;
      categorySelect.appendChild(option);
    });
  }
  
  categorySelect.disabled = false;
}

function updateWorldMapGeoJSON() {
  const groupingSelect = document.getElementById('groupingSelect');
  const categorySelect = document.getElementById('categorySelect');
  
  if (!groupingSelect || !categorySelect || !worldMap || !window._worldGeoJSON) return;
  
  const grouping = groupingSelect.value;
  const category = categorySelect.value;
  
  // Entferne bestehende GeoJSON Layer
  if (worldMapLayer) {
    worldMap.removeLayer(worldMapLayer);
    worldMapLayer = null;
  }
  
  if (!grouping || !category) return;
  
  // Finde relevante Länder
  let relevantCountries = [];
  
  if (grouping === 'groups' && worldMapGroups[category]) {
    // Groups haben eine 'members' Eigenschaft
    relevantCountries = worldMapGroups[category].members || worldMapGroups[category];
    console.log(`🗺️ Group ${category}: ${relevantCountries.length} countries`, relevantCountries);
  } else if (grouping === 'government' || grouping === 'language') {
    relevantCountries = Object.keys(worldMapCountries).filter(countryName => {
      const country = worldMapCountries[countryName];
      let value = country[grouping];
      
      // Spezielle Behandlung für languages
      if (grouping === 'language') {
        value = country.languages || country.language;
        
        // Behandle komma-getrennte Sprachen
        if (value && typeof value === 'string' && value.includes(',')) {
          const languages = value.split(',').map(lang => lang.trim());
          return languages.includes(category);
        }
      }
      
      if (Array.isArray(value)) {
        return value.some(v => v && v.toString().trim() === category);
      }
      return value && value.toString().trim() === category;
    });
    
    console.log(`Found ${relevantCountries.length} countries for ${grouping}=${category}:`, relevantCountries);
  }
  
  // Erstelle Set für schnelle Lookup
  const relevantCountriesSet = new Set(relevantCountries.map(c => c.toLowerCase()));
  
  // Erstelle ISO-Lookup für relevante Länder (wie in countries.html)
  const isoByName = {};
  Object.entries(worldMapCountries).forEach(([name, data]) => {
    if (data.iso2) isoByName[name.toLowerCase()] = data.iso2.toUpperCase();
    if (data.iso3) isoByName[name.toLowerCase()] = data.iso3.toUpperCase();
  });
  
  // Erstelle GeoJSON Layer mit Styling
  worldMapLayer = L.geoJSON(window._worldGeoJSON, {
    style: feature => {
      // 🧩 ISO-Fallbacks aus diversen GeoJSON-Feldern (wie in countries.html)
      const iso = (
        feature.properties.iso_a3_eh || feature.properties.ISO_A3_EH ||
        feature.properties.ISO_A3 || feature.properties.iso_a3 ||
        feature.properties.ADM0_A3 || feature.properties.adm0_a3 ||
        feature.properties.SOV_A3 || feature.properties.sov_a3 ||
        feature.properties.WB_A3 || feature.properties.wb_a3 ||
        feature.properties.gu_a3 || feature.properties.su_a3 ||
        feature.id || ""
      ).toUpperCase();
      
      // Versuche über ISO zu matchen
      let isRelevant = false;
      const name = (
        feature.properties.name ||
        feature.properties.NAME ||
        feature.properties.ADMIN ||
        feature.properties.COUNTRY ||
        feature.properties.SOVEREIGNT ||
        ""
      ).trim();
      
      if (name) {
        const canonical = worldMapCountryMappings[name] || name;
        isRelevant = relevantCountriesSet.has(canonical.toLowerCase());
        
      // Erweiterte Fallback-Strategien
      if (!isRelevant) {
        // 1. Direkte Name-Suche (case-insensitive)
        isRelevant = relevantCountries.some(country => 
          country.toLowerCase() === name.toLowerCase() ||
          country.toLowerCase() === canonical.toLowerCase()
        );
        
        // 2. ISO-Code Lookup
        if (!isRelevant) {
          const isoFromName = isoByName[canonical.toLowerCase()];
          if (isoFromName) {
            isRelevant = relevantCountries.some(country => {
              const countryData = worldMapCountries[country];
              return countryData && (countryData.iso2 === isoFromName || countryData.iso3 === isoFromName);
            });
          }
        }
        
        // 3. Partial Name Matching für komplexe Namen (DISABLED - caused Oman/Romania bug)
        // Removed: Was matching "Oman" inside "Romania" for EU group
        // if (!isRelevant && name.length > 3) {
        //   isRelevant = relevantCountries.some(country => {
        //     const countryLower = country.toLowerCase();
        //     const nameLower = name.toLowerCase();
        //     return countryLower.includes(nameLower) || nameLower.includes(countryLower);
        //   });
        // }
        
        // 4. Erweiterte GeoJSON-Name-Mappings
        if (!isRelevant) {
          const geoJsonMappings = {
            'United States of America': 'United States',
            'United Kingdom of Great Britain and Northern Ireland': 'United Kingdom',
            'Russian Federation': 'Russia',
            'Iran (Islamic Republic of)': 'Iran',
            'Korea, Republic of': 'South Korea',
            'Venezuela (Bolivarian Republic of)': 'Venezuela',
            'Bolivia (Plurinational State of)': 'Bolivia',
            'Republic of the Congo': 'Congo',
            'Democratic Republic of the Congo': 'Democratic Republic of Congo',
            'Lao People\'s Democratic Republic': 'Laos',
            'Syrian Arab Republic': 'Syria',
            'Republic of Serbia': 'Serbia',
            'Czech Republic': 'Czechia',
            'Slovak Republic': 'Slovakia'
          };
          const mappedName = geoJsonMappings[name];
          if (mappedName) {
            isRelevant = relevantCountriesSet.has(mappedName.toLowerCase());
          }
        }
        
        // 5. Spezielle ISO-3 Codes für häufige Probleme
        if (!isRelevant && iso) {
          const specialMappings = {
            'USA': 'United States',
            'GBR': 'United Kingdom',
            'DEU': 'Germany',
            'FRA': 'France',
            'ITA': 'Italy',
            'ESP': 'Spain',
            'NLD': 'Netherlands',
            'BEL': 'Belgium',
            'CHE': 'Switzerland',
            'AUT': 'Austria'
          };
          
          const mappedName = specialMappings[iso];
          if (mappedName) {
            isRelevant = relevantCountries.includes(mappedName);
          }
        }
      }        // Debug-Logging für Matching-Probleme
        if (isRelevant) {
          console.log(`✅ Matched: ${name} → ${canonical}`);
        }
      }
      
      return {
        fillColor: isRelevant ? '#2196F3' : '#ddd',
        weight: isRelevant ? 2 : 1,
        opacity: 1,
        color: isRelevant ? '#1976D2' : '#999',
        fillOpacity: isRelevant ? 0.7 : 0.3
      };
    },
    onEachFeature: (feature, layer) => {
      const name = (
        feature.properties.name ||
        feature.properties.NAME ||
        feature.properties.ADMIN ||
        feature.properties.COUNTRY ||
        ""
      ).trim();
      
      if (name) {
        const canonical = worldMapCountryMappings[name] || name;
        
        // Nur Tooltip für Hauptländer, nicht für Überseegebiete
        const isMainland = !feature.properties.type || 
                          feature.properties.type === 'Sovereign country' ||
                          feature.properties.type === 'Country' ||
                          (feature.properties.homepart && feature.properties.homepart === 1);
                          
        // Spezielle Behandlung für bekannte Überseegebiete
        const isOverseasTerritory = 
          name.includes('French Guiana') || name.includes('Guyana') ||
          name.includes('Martinique') || name.includes('Guadeloupe') ||
          name.includes('Réunion') || name.includes('Mayotte') ||
          name.includes('New Caledonia') || name.includes('Polynesia') ||
          feature.properties.admin !== feature.properties.sovereignt;
          
        if (isMainland && !isOverseasTerritory) {
          // Hole Population für Tooltip
          const currentYear = new Date().getFullYear();
          let population = 'N/A';
          for (let year = currentYear; year >= currentYear - 5; year--) {
            const popKey = `${canonical}_${year}`;
            if (worldMapPopulation[popKey]) {
              population = (worldMapPopulation[popKey] / 1000000).toFixed(1) + 'M';
              break;
            }
          }
          
          // Flaggen-URL: Use ISO-2 code from GeoJSON (like countries.html)
          const iso2 = feature.properties.iso_a2 || feature.properties.ISO_A2;
          const flagUrl = iso2 
            ? `images/flag/${iso2.toLowerCase()}.svg`
            : `images/flag/question.svg`;
          
          layer.bindTooltip(`
            <div style="text-align: center;">
              <img src="${flagUrl}" alt="${canonical}" style="width: 24px; height: auto; margin-bottom: 5px;" onerror="this.src='images/flag/question.svg'">
              <br><strong>${canonical}</strong>
              <br>Population: ${population}
            </div>
          `, {
            direction: 'top',
            offset: [0, -10]
          });
        }
      }
    }
  }).addTo(worldMap);
  
  // Update context legend
  updateMapLegend(grouping, category, relevantCountries.length);
}

// === Update Context Legend Box ===
function updateMapLegend(grouping, category, countryCount) {
  const legendBox = document.getElementById('world-map-legend');
  const legendTitle = document.getElementById('legend-title');
  const legendContent = document.getElementById('legend-content');
  
  if (!legendBox || !legendTitle || !legendContent) return;
  
  let title = '';
  let content = '';
  
  if (grouping === 'groups') {
    const groupDescriptions = {
      'EU': 'The European Union is a political and economic union of 27 member states primarily located in Europe. It operates through a system of supranational institutions and intergovernmental negotiated decisions, with a common market allowing free movement of people, goods, services, and capital.',
      'G7': 'The Group of Seven is an intergovernmental forum consisting of Canada, France, Germany, Italy, Japan, the United Kingdom, and the United States. These countries are among the world\'s largest advanced economies and democracies, representing about 40% of global GDP.',
      'G20': 'The Group of Twenty is an intergovernmental forum comprising 19 countries, the European Union, and the African Union. It represents the world\'s major economies, accounting for approximately 85% of global GDP, over 75% of global trade, and about two-thirds of the world population.',
      'BRICS': 'BRICS is an intergovernmental organization comprising Brazil, Russia, India, China, and South Africa. These emerging economies represent over 40% of the world\'s population and are characterized by their significant influence on regional and global affairs.',
      'OECD': 'The Organisation for Economic Co-operation and Development promotes policies to improve economic and social well-being worldwide. Its 38 member countries span the globe and include many of the world\'s most advanced economies as well as emerging countries.',
      'NATO': 'The North Atlantic Treaty Organization is an intergovernmental military alliance of 31 member states. Founded in 1949, NATO constitutes a system of collective security whereby its member states agree to mutual defense in response to an attack by any external party.',
      'OPEC': 'The Organization of the Petroleum Exporting Countries coordinates petroleum policies among member countries to secure fair and stable prices for petroleum producers, ensure an efficient and regular supply to consumers, and provide a fair return on capital for investors.',
      'Arab League': 'The Arab League is a regional organization of Arab countries in the Middle East and North Africa. It aims to strengthen ties among member states, coordinate policies, and promote Arab interests and unity.',
      'ASEAN': 'The Association of Southeast Asian Nations is a regional organization promoting intergovernmental cooperation and facilitating economic, political, security, military, educational, and sociocultural integration among its members and other countries in Asia.',
      'Commonwealth': 'The Commonwealth of Nations is a political association of 56 member states, most of which are former territories of the British Empire. Members cooperate on shared goals like development, democracy, and peace.'
    };
    
    title = `${category} (${countryCount} countries)`;
    content = groupDescriptions[category] || `${category} is an international grouping of ${countryCount} countries.`;
    
  } else if (grouping === 'language') {
    // Calculate speakers (simplified - would need actual data)
    const speakerEstimates = {
      'English': '1.5 billion',
      'Mandarin Chinese': '1.1 billion',
      'Hindi': '600 million',
      'Spanish': '550 million',
      'French': '300 million',
      'Arabic': '420 million',
      'Portuguese': '260 million',
      'Russian': '260 million',
      'German': '130 million',
      'Japanese': '125 million'
    };
    
    const speakers = speakerEstimates[category] || 'millions of';
    title = `${category} Language`;
    content = `${category} is spoken in ${countryCount} countries by approximately ${speakers} people worldwide.`;
    
  } else if (grouping === 'government') {
    const govDescriptions = {
      'Full Democracy': 'Full democracies feature free and fair elections, strong institutions that protect civil liberties and fundamental rights, separation of powers with effective checks and balances, and independent judiciary systems that ensure the rule of law.',
      'Flawed Democracy': 'Flawed democracies maintain democratic elections but face challenges including media freedom restrictions, political polarization, corruption issues, or weakened democratic institutions that prevent them from functioning as full democracies.',
      'Hybrid Regime': 'Hybrid regimes conduct elections that are neither fully free nor fair, feature a very strong executive branch with weak checks and balances, have compromised rule of law, and often suppress opposition voices and civil society.',
      'Authoritarian Regime': 'Authoritarian regimes lack genuine democratic elections, actively suppress political opposition and dissent, severely restrict civil liberties and fundamental rights, and concentrate power in the hands of a single leader or small elite group.'
    };
    
    title = `${category} (${countryCount} countries)`;
    content = govDescriptions[category] || `${category} governance system is present in ${countryCount} countries.`;
  }
  
  if (title && content) {
    legendTitle.textContent = title;
    legendContent.textContent = content;
    legendBox.classList.remove('hidden');
  } else {
    legendBox.classList.add('hidden');
  }
}

// === Seite initialisieren ===
async function initWorldPageWithMap() {
  await initWorldPage();
  await initWorldMap();
}

if (typeof onDocumentReady === "function") {
  onDocumentReady(initWorldPageWithMap);
} else {
  document.addEventListener("DOMContentLoaded", initWorldPageWithMap);
}
