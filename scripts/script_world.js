/* ============================================================
   🌍 RealityCheck – World Trends Dashboard (auto from /data)
   ------------------------------------------------------------
   Final Clean Version (2025-11-01)
   • Spinner-Handling über core.js (showSpinner)
   • Einheitliche Nutzung von loadJSON() und loadAllKPIData()
   ============================================================ */

const META_FILE = "data/meta/available_kpis.json";
const DATA_DIR = "data";

let META = [], ALL_DATA = {}; // world-only datasets + metadata

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

    META = (await loadJSON(META_FILE)).filter(kpi => kpi.publication_status !== "pending_first_fetch");
    const worldKpis = META.filter(kpi =>
      (kpi.world_kpi === "y" || kpi.world_kpi === "e") && kpi.filename
    );
    const worldDatasets = await Promise.all(worldKpis.map(kpi => loadKPIData(kpi.filename)));
    ALL_DATA = Object.fromEntries(worldKpis.map((kpi, index) => [kpi.filename, worldDatasets[index]]));

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
let worldMapPopulation = []; // Changed from {} to [] for array operations
let worldMapCountryMappings = {};
let worldMapGdp = [];
let worldMapEmissions = [];
let worldMapArea = [];
let worldMapSelectedKpiData = [];
let worldMapSelectedKpiMeta = null;
let worldMapYearRequestId = 0;
const WORLD_MAP_SUMMABLE_KPIS = new Set([
  "area", "co2_emissions", "electric_vehicle_stock", "gdp", "net_migration",
  "olympic_medals_summer", "olympic_medals_winter", "population", "railway_length", "refugees_hosted",
]);
const WORLD_MAP_PER_CAPITA_KPIS = new Set([
  "co2_emissions", "electric_vehicle_stock", "gdp", "net_migration",
  "olympic_medals_summer", "olympic_medals_winter", "railway_length", "refugees_hosted",
]);
const WORLD_MAP_GROUP_COLORS = {
  a: { fill: "#1976d2", border: "#0d47a1" },
  b: { fill: "#ef6c00", border: "#a84300" },
  overlap: { fill: "#7b1fa2", border: "#4a0866" },
};
const WORLD_MAP_CLIMATE_GROUPING = "climate";
const WORLD_MAP_VALUE_MODE_LABELS = {
  absolute: "Absolute",
  per_capita: "Per capita",
  share_population: "Share of population",
  share_area: "Share of area",
  hazard_class: "Hazard class",
  change: "Change",
  index: "Index / rate",
};
const WORLD_MAP_AGGREGATION_LABELS = {
  median: "Median",
  mean: "Mean",
  sum: "Sum",
  max: "Maximum",
  population_weighted_mean: "Population-weighted mean",
  area_weighted_mean: "Area-weighted mean",
  source_aggregate: "Source-provided aggregate",
};
const WORLD_MAP_CLIMATE_CATEGORIES = {
  multi_hazard_exposure: {
    label: "Multi-Hazard Exposure",
    description:
      "Historical impact data from climate-related disasters (droughts, floods, extreme weather and temperatures, wildfires). This reflects observed impact reporting, not full climate risk.",
    metrics: [
      {
        kpi: "people_affected_by_climate_disasters",
        label: "Population exposed (people affected)",
        valueModes: ["absolute", "per_capita"],
        defaultValueMode: "absolute",
        aggregations: ["sum", "median", "mean", "max"],
        defaultAggregation: "sum",
        measureType: "exposure",
      },
      {
        kpi: "climate_disaster_deaths",
        label: "Deaths",
        valueModes: ["absolute", "per_capita"],
        defaultValueMode: "absolute",
        aggregations: ["sum", "median", "mean", "max"],
        defaultAggregation: "sum",
        measureType: "historical_impact",
      },
      {
        kpi: "climate_disaster_damage_gdp",
        label: "Recorded damage (% of GDP)",
        valueModes: ["index"],
        defaultValueMode: "index",
        aggregations: ["median", "mean", "max"],
        defaultAggregation: "median",
        measureType: "historical_impact",
      },
    ],
  },
  agricultural_drought: {
    label: "Agricultural Drought",
    description:
      "Proxy based on national water-stress pressure. This is not a direct drought-hazard footprint map and should not be interpreted as vulnerability or expected damage.",
    metrics: [
      {
        kpi: "water_stress_level",
        label: "Water stress level (proxy)",
        valueModes: ["index"],
        defaultValueMode: "index",
        aggregations: ["median", "mean", "max"],
        defaultAggregation: "median",
        measureType: "hazard_proxy",
      },
    ],
  },
  emissions_transition: {
    label: "Emissions & Transition",
    description:
      "Climate-pressure and transition indicators from established sources. CO2 reflects territorial emissions; transition metrics show progress proxies, not complete decarbonization pathways.",
    metrics: [
      {
        kpi: "co2_emissions",
        label: "CO2 emissions",
        valueModes: ["absolute", "per_capita"],
        defaultValueMode: "absolute",
        aggregations: ["sum", "median", "mean", "max"],
        defaultAggregation: "sum",
        measureType: "historical_impact",
      },
      {
        kpi: "renewable_energy_share",
        label: "Renewable energy share",
        valueModes: ["index"],
        defaultValueMode: "index",
        aggregations: ["median", "mean", "population_weighted_mean", "max"],
        defaultAggregation: "median",
        measureType: "hazard_proxy",
      },
      {
        kpi: "electric_vehicle_stock",
        label: "Electric vehicle stock",
        valueModes: ["absolute", "per_capita"],
        defaultValueMode: "per_capita",
        aggregations: ["sum", "median", "mean", "max"],
        defaultAggregation: "sum",
        measureType: "hazard_proxy",
      },
    ],
  },
  ecosystem_air_pressure: {
    label: "Ecosystem & Air Pressure",
    description:
      "Environmental pressure indicators with climate relevance. These are partial signals and should be interpreted together with other climate and resilience metrics.",
    metrics: [
      {
        kpi: "air_quality_pm2_5_exposure",
        label: "PM2.5 exposure",
        valueModes: ["index"],
        defaultValueMode: "index",
        aggregations: ["median", "mean", "population_weighted_mean", "max"],
        defaultAggregation: "median",
        measureType: "hazard_proxy",
      },
      {
        kpi: "terrestrial_protected_areas",
        label: "Protected land area",
        valueModes: ["index"],
        defaultValueMode: "index",
        aggregations: ["median", "mean", "area_weighted_mean", "max"],
        defaultAggregation: "median",
        measureType: "hazard_proxy",
      },
    ],
  },
  water_infrastructure_resilience: {
    label: "Water & Infrastructure Resilience",
    description:
      "Foundational service coverage linked to climate resilience and adaptive capacity. High values do not remove hazard exposure but can reduce day-to-day vulnerability.",
    metrics: [
      {
        kpi: "access_to_basic_drinking_water",
        label: "Access to basic drinking water",
        valueModes: ["index"],
        defaultValueMode: "index",
        aggregations: ["median", "mean", "population_weighted_mean", "max"],
        defaultAggregation: "median",
        measureType: "exposure",
      },
      {
        kpi: "basic_sanitation_access",
        label: "Basic sanitation access",
        valueModes: ["index"],
        defaultValueMode: "index",
        aggregations: ["median", "mean", "population_weighted_mean", "max"],
        defaultAggregation: "median",
        measureType: "exposure",
      },
      {
        kpi: "access_to_electricity",
        label: "Access to electricity",
        valueModes: ["index"],
        defaultValueMode: "index",
        aggregations: ["median", "mean", "population_weighted_mean", "max"],
        defaultAggregation: "median",
        measureType: "exposure",
      },
    ],
  },
  storm_impact: {
    label: "Storm Impact (tropical cyclones)",
    description:
      "Named tropical cyclone activity per ocean basin, from NOAA's IBTrACS global best-track archive. This is a region view (ocean basins), not a country view: tropical cyclones form and travel across ocean basins, not within national borders.",
    geoType: "region",
    regionSet: "ocean_basins",
    metrics: [
      {
        kpi: "tropical_cyclone_activity_basin",
        label: "Named storms per year",
        valueModes: ["absolute"],
        defaultValueMode: "absolute",
        aggregations: ["median"],
        defaultAggregation: "median",
        measureType: "historical_impact",
      },
    ],
  },
};
const WORLD_MAP_CLIMATE_PLACEHOLDER_CATEGORIES = {
  wildfire_impact: {
    label: "Wildfire Impact (coming soon)",
    description: "Planned region-based hazard category (IPCC AR6 climate reference regions). A verified, automated, no-login regional data source is not yet connected.",
    geoType: "region",
    regionSet: "ipcc_ar6",
  },
  flood_impact: {
    label: "Flood Impact (coming soon)",
    description: "Planned region-based hazard category (major river basins). A verified, automated, no-login regional data source is not yet connected.",
    geoType: "region",
    regionSet: "river_basins",
  },
  heat_impact: {
    label: "Heat Impact (coming soon)",
    description: "Planned region-based hazard category (IPCC AR6 climate reference regions). A verified, automated, no-login regional data source is not yet connected.",
    geoType: "region",
    regionSet: "ipcc_ar6",
  },
  drought_impact: {
    label: "Drought Impact (coming soon)",
    description: "Planned region-based hazard category (IPCC AR6 climate reference regions). A verified, automated, no-login regional data source is not yet connected.",
    geoType: "region",
    regionSet: "ipcc_ar6",
  },
};

function isClimateGrouping(grouping) {
  return grouping === WORLD_MAP_CLIMATE_GROUPING;
}

function getKpiMetaByFilename(filename) {
  return META.find(kpi => kpi.filename === filename) || null;
}

function getClimateCategoryConfig(categoryKey) {
  return WORLD_MAP_CLIMATE_CATEGORIES[categoryKey]
    || WORLD_MAP_CLIMATE_PLACEHOLDER_CATEGORIES[categoryKey]
    || null;
}

function getClimateMetricOptions(categoryKey) {
  const category = getClimateCategoryConfig(categoryKey);
  if (!category || !Array.isArray(category.metrics)) return [];
  return category.metrics.filter(metric => Boolean(getKpiMetaByFilename(metric.kpi)));
}

function getActiveClimateMetricConfig() {
  const grouping = document.getElementById("groupingSelect")?.value || "";
  if (!isClimateGrouping(grouping)) return null;
  const categoryKey = document.getElementById("categorySelect")?.value || "";
  const selectedKpi = document.getElementById("worldMapKpiSelect")?.value || "";
  return getClimateMetricOptions(categoryKey).find(metric => metric.kpi === selectedKpi) || null;
}

function setSelectOptions(select, options, preferredValue, fallbackValue = "") {
  if (!select) return "";
  const previous = select.value;
  select.textContent = "";
  options.forEach(optionDef => {
    const option = document.createElement("option");
    option.value = optionDef.value;
    option.textContent = optionDef.label;
    if (optionDef.disabled) option.disabled = true;
    select.appendChild(option);
  });
  const allowed = new Set(options.map(item => item.value));
  const resolved = [preferredValue, previous, fallbackValue].find(value => value && allowed.has(value)) || options[0]?.value || "";
  if (resolved) select.value = resolved;
  return resolved;
}

function updateWorldMapGeographyAvailability() {
  const grouping = document.getElementById("groupingSelect")?.value || "";
  const wrapper = document.getElementById("worldMapGeographyWrapper");
  const select = document.getElementById("worldMapGeographyMode");
  if (!wrapper || !select) return;
  const categoryKey = document.getElementById("categorySelect")?.value || "";
  const categoryConfig = getClimateCategoryConfig(categoryKey);
  const isRegionCategory = isClimateGrouping(grouping) && categoryConfig?.geoType === "region";
  wrapper.hidden = !isRegionCategory;
  if (isRegionCategory) {
    // Hazard categories backed by region data (basins, IPCC AR6 regions, ...) have
    // no country-level equivalent, so this is informational rather than a toggle.
    select.value = "regions";
    select.disabled = true;
  } else {
    select.value = "countries";
    select.disabled = false;
  }
}

function describeMeasureType(type) {
  if (type === "hazard_proxy") {
    return "Hazard proxy: a physical pressure indicator, not direct exposure, vulnerability or expected damage.";
  }
  if (type === "historical_impact") {
    return "Historical impact: recorded outcomes from events, not a direct hazard probability or full risk estimate.";
  }
  return "Exposure: people or value proxies within affected zones; this does not by itself measure vulnerability or risk.";
}

function getAggregationLabel(key) {
  return WORLD_MAP_AGGREGATION_LABELS[key] || key;
}

function worldMapRealCountryNames() {
  return new Set(Object.keys(worldMapCountries));
}

function availableCountryYears(dataset, countryUniverse = worldMapRealCountryNames()) {
  return [...new Set((dataset || [])
    .filter(row => countryUniverse.has(row.country) && Number.isFinite(Number(row.year)) && Number.isFinite(row.value))
    .map(row => Number(row.year)))]
    .sort((a, b) => b - a);
}

function resolveDataYear(dataset, requestedYear, countryUniverse = worldMapRealCountryNames()) {
  const years = availableCountryYears(dataset, countryUniverse);
  if (!years.length) return null;
  const requested = Number(requestedYear);
  if (!Number.isFinite(requested)) return years[0];
  return years.find(year => year <= requested) ?? years[years.length - 1];
}

function countryValuesForYear(dataset, year, allowedCountries) {
  const values = new Map();
  if (!Number.isFinite(Number(year))) return values;
  (dataset || []).forEach(row => {
    if (Number(row.year) !== Number(year) || !allowedCountries.has(row.country) || !Number.isFinite(row.value)) return;
    values.set(row.country, Number(row.value));
  });
  return values;
}

function calculateAdditiveShare(dataset, members, requestedYear, countryUniverse) {
  const year = resolveDataYear(dataset, requestedYear, countryUniverse);
  if (year === null) return { year: null, share: null, covered: 0, total: members.length };
  const worldValues = countryValuesForYear(dataset, year, countryUniverse);
  const memberSet = new Set(members);
  const coveredValues = [...worldValues.entries()].filter(([country]) => memberSet.has(country));
  const numerator = coveredValues.reduce((sum, [, value]) => sum + value, 0);
  const denominator = [...worldValues.values()].reduce((sum, value) => sum + value, 0);
  return {
    year,
    share: denominator > 0 ? numerator / denominator : null,
    covered: coveredValues.length,
    total: members.length,
  };
}

function calculateMedianMetric(dataset, members, requestedYear) {
  const memberSet = new Set(members);
  const values = (dataset || [])
    .filter(row => Number(row.year) === Number(requestedYear) && memberSet.has(row.country) && Number.isFinite(row.value))
    .map(row => Number(row.value))
    .sort((a, b) => a - b);
  if (!values.length) return { value: null, covered: 0, total: members.length };
  const middle = Math.floor(values.length / 2);
  const value = values.length % 2 ? values[middle] : (values[middle - 1] + values[middle]) / 2;
  return { value, covered: values.length, total: members.length };
}

function classifyGroupMembership(country, groupA, groupB = new Set()) {
  const inA = groupA.has(country);
  const inB = groupB.has(country);
  if (inA && inB) return "overlap";
  if (inA) return "a";
  if (inB) return "b";
  return "other";
}

function percentileIntensities(valueMap) {
  const sorted = [...valueMap.values()].filter(Number.isFinite).sort((a, b) => a - b);
  const result = new Map();
  if (!sorted.length) return result;
  valueMap.forEach((value, country) => {
    if (!Number.isFinite(value)) return;
    const lower = sorted.findIndex(candidate => candidate === value);
    const upper = sorted.length - 1 - [...sorted].reverse().findIndex(candidate => candidate === value);
    result.set(country, sorted.length === 1 ? 0.65 : ((lower + upper) / 2) / (sorted.length - 1));
  });
  return result;
}

function mixWithWhite(hex, intensity) {
  const normalized = hex.replace("#", "");
  const rgb = [0, 2, 4].map(offset => parseInt(normalized.slice(offset, offset + 2), 16));
  const strength = 0.24 + Math.max(0, Math.min(1, intensity)) * 0.76;
  return `rgb(${rgb.map(channel => Math.round(255 - (255 - channel) * strength)).join(", ")})`;
}

// === Region-based climate hazard rendering (basins, IPCC AR6 regions, ...) ===
// Kept separate from the country rendering path above so the country map
// (groups/government/language + the country-level climate categories) stays
// untouched. Only categories with geoType "region" (see
// WORLD_MAP_CLIMATE_CATEGORIES / _PLACEHOLDER_CATEGORIES) use this path.
let _worldMapRegionSetsMeta = null;
const _worldMapRegionGeoJSONCache = {};

async function loadRegionSetsMeta() {
  if (!_worldMapRegionSetsMeta) {
    _worldMapRegionSetsMeta = await loadJSON("data/meta/region_sets.json");
  }
  return _worldMapRegionSetsMeta;
}

async function loadRegionGeoJSON(regionSet) {
  if (_worldMapRegionGeoJSONCache[regionSet]) return _worldMapRegionGeoJSONCache[regionSet];
  const sets = await loadRegionSetsMeta();
  const config = sets?.[regionSet];
  if (!config?.geo_file) return null;
  const geojson = await loadJSON(`data/meta/${config.geo_file}`);
  _worldMapRegionGeoJSONCache[regionSet] = geojson;
  return geojson;
}

function availableRegionYears(dataset) {
  return [...new Set((dataset || [])
    .filter(row => row.region && Number.isFinite(Number(row.year)) && Number.isFinite(Number(row.value)))
    .map(row => Number(row.year)))]
    .sort((a, b) => b - a);
}

function regionValuesForYear(dataset, year) {
  const values = new Map();
  if (!Number.isFinite(Number(year))) return values;
  (dataset || []).forEach(row => {
    if (Number(row.year) !== Number(year) || !row.region || !Number.isFinite(Number(row.value))) return;
    values.set(row.region, Number(row.value));
  });
  return values;
}

async function renderWorldMapRegionLayer(categoryConfig, category) {
  clearWorldMapSelection();
  const regionSet = categoryConfig.regionSet;
  const [regionSets, geojson] = await Promise.all([loadRegionSetsMeta(), loadRegionGeoJSON(regionSet)]);
  const regionMeta = regionSets?.[regionSet];
  const modeNote = document.getElementById('world-map-mode-note');
  if (!worldMap || !geojson || !regionMeta) {
    if (modeNote) modeNote.textContent = `${categoryConfig.label}: region geometry could not be loaded.`;
    return;
  }

  const codeProperty = regionMeta.code_property || "Acronym";
  const nameProperty = regionMeta.name_property || "Name";
  const selectedYear = Number(document.getElementById('worldMapYearSelect')?.value);
  const values = regionValuesForYear(worldMapSelectedKpiData, selectedYear);
  const intensities = percentileIntensities(values);
  const baseColor = WORLD_MAP_GROUP_COLORS.a.fill;
  const borderColor = WORLD_MAP_GROUP_COLORS.a.border;

  worldMapLayer = L.geoJSON(geojson, {
    style: feature => {
      const code = feature?.properties?.[codeProperty];
      const intensity = intensities.get(code);
      return {
        fillColor: Number.isFinite(intensity) ? mixWithWhite(baseColor, intensity) : '#e8edf2',
        weight: 1.5,
        opacity: 1,
        color: borderColor,
        fillOpacity: Number.isFinite(intensity) ? 0.82 : 0.25,
      };
    },
    onEachFeature: (feature, layer) => {
      const code = feature?.properties?.[codeProperty];
      const name = feature?.properties?.[nameProperty] || code || "Region";
      const value = values.get(code);
      const meta = worldMapSelectedKpiMeta;
      const displayValue = Number.isFinite(value) ? formatWorldMapNumber(value, meta?.unit || "") : "no data";
      const tooltip = `
        <div class="map-tooltip">
          <div class="map-tooltip__header">
            <div class="map-tooltip__title">${name}</div>
          </div>
          <div class="map-tooltip__value">${meta?.title || "Selected metric"}: ${displayValue}</div>
          <div class="map-tooltip__meta">
            <div class="map-tooltip__meta-row">Year: ${Number.isFinite(selectedYear) ? selectedYear : "–"}</div>
          </div>
        </div>
      `;
      layer.bindTooltip(tooltip, { sticky: true });
      layer.on({
        mouseover: e => e.target.setStyle({ weight: 2.5, fillOpacity: 0.95 }),
        mouseout: e => worldMapLayer.resetStyle(e.target),
      });
    },
  }).addTo(worldMap);

  const legendBox = document.getElementById('world-map-legend');
  const legendTitle = document.getElementById('legend-title');
  const legendContent = document.getElementById('legend-content');
  if (legendBox && legendTitle && legendContent) {
    legendTitle.textContent = `${categoryConfig.label} (${regionMeta.label || regionSet})`;
    legendContent.textContent = `${categoryConfig.description} Metric: ${worldMapSelectedKpiMeta?.title || "–"}. Year: ${Number.isFinite(selectedYear) ? selectedYear : "–"}. Source: ${regionMeta.attribution || ""}`;
    legendBox.classList.remove('hidden');
  }
  updateWorldMapVisualLegend(category, "");
  if (modeNote) {
    modeNote.textContent = `${categoryConfig.label} uses a region view (${regionMeta.label}) because this hazard is naturally reported per region, not per country. ${regionMeta.attribution || ""}`;
  }
  document.getElementById('world-group-summary')?.setAttribute('hidden', '');
  syncWorldMapUrl();
}

function calculateGroupMetric(dataset, members, requestedYear, options = {}) {
  const memberSet = new Set(members);
  const population = countryValuesForYear(options.populationData || [], requestedYear, memberSet);
  const area = countryValuesForYear(options.areaData || [], requestedYear, memberSet);
  const values = (dataset || [])
    .filter(row => Number(row.year) === Number(requestedYear) && memberSet.has(row.country) && Number.isFinite(row.value))
    .map(row => {
      const raw = Number(row.value);
      let converted = raw;
      if (options.valueMode === "per_capita") {
        const denominator = population.get(row.country);
        converted = Number.isFinite(denominator) && denominator > 0 ? raw / denominator : null;
      }
      return {
        country: row.country,
        value: Number.isFinite(converted) ? converted : null,
        populationWeight: population.get(row.country),
        areaWeight: area.get(row.country),
      };
    })
    .filter(item => Number.isFinite(item.value));

  if (!values.length) return { value: null, covered: 0, total: members.length };

  const sorted = values.map(item => item.value).sort((a, b) => a - b);
  const median = sorted.length % 2
    ? sorted[Math.floor(sorted.length / 2)]
    : (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2;

  let value = median;
  if (options.aggregation === "sum") {
    value = values.reduce((sum, item) => sum + item.value, 0);
  } else if (options.aggregation === "mean" || options.aggregation === "source_aggregate") {
    value = values.reduce((sum, item) => sum + item.value, 0) / values.length;
  } else if (options.aggregation === "max") {
    value = Math.max(...values.map(item => item.value));
  } else if (options.aggregation === "population_weighted_mean") {
    const weighted = values
      .filter(item => Number.isFinite(item.populationWeight) && item.populationWeight > 0)
      .reduce((acc, item) => {
        acc.weighted += item.value * item.populationWeight;
        acc.totalWeight += item.populationWeight;
        return acc;
      }, { weighted: 0, totalWeight: 0 });
    value = weighted.totalWeight > 0 ? weighted.weighted / weighted.totalWeight : null;
  } else if (options.aggregation === "area_weighted_mean") {
    const weighted = values
      .filter(item => Number.isFinite(item.areaWeight) && item.areaWeight > 0)
      .reduce((acc, item) => {
        acc.weighted += item.value * item.areaWeight;
        acc.totalWeight += item.areaWeight;
        return acc;
      }, { weighted: 0, totalWeight: 0 });
    value = weighted.totalWeight > 0 ? weighted.weighted / weighted.totalWeight : null;
  }

  return { value: Number.isFinite(value) ? value : null, covered: values.length, total: members.length };
}

function formatWorldMapNumber(value, unit = "") {
  if (!Number.isFinite(value)) return "No data";
  const absolute = Math.abs(value);
  const formatted = absolute >= 1e12
    ? `${(value / 1e12).toFixed(2)}T`
    : absolute >= 1e9
      ? `${(value / 1e9).toFixed(2)}B`
      : absolute >= 1e6
        ? `${(value / 1e6).toFixed(2)}M`
        : new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value);
  return unit ? `${formatted} ${unit}` : formatted;
}

function formatCoverage(covered, total) {
  const percentage = total ? Math.round((covered / total) * 100) : 0;
  return `${covered}/${total} countries (${percentage}%)`;
}

function getWorldMapGroupTitle(groupName) {
  const group = worldMapGroups[groupName];
  const title = group?.title || groupName;
  const parser = document.createElement('template');
  parser.innerHTML = title;
  return (parser.content.textContent || groupName).trim();
}

async function initWorldMap() {
  try {
    // Lade Daten
    [
      worldMapCountries,
      worldMapGroups,
      worldMapCountryMappings,
      worldMapPopulation,
      worldMapGdp,
      worldMapEmissions,
      worldMapArea,
    ] = await Promise.all([
      loadJSON("data/meta/countries.json"),
      loadJSON("data/meta/groups.json"),
      loadJSON("data/meta/country_mappings.json"),
      loadKPIData("population"),
      loadKPIData("gdp"),
      loadKPIData("co2_emissions"),
      loadKPIData("area"),
    ]);

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
    const comparisonSelect = document.getElementById('comparisonGroupSelect');
    const kpiSelect = document.getElementById('worldMapKpiSelect');
    const yearSelect = document.getElementById('worldMapYearSelect');
    const valueModeSelect = document.getElementById('worldMapValueMode');
    const aggregationSelect = document.getElementById('worldMapAggregationMode');
    const geographySelect = document.getElementById('worldMapGeographyMode');
    
    if (groupingSelect) {
      groupingSelect.addEventListener('change', async () => {
        updateCategoryOptions();
        updateWorldMapGeographyAvailability();
        populateWorldMapKpiOptions();
        await updateWorldMapYearOptions();
        updateWorldMapModeAvailability();
        updateWorldMapGeoJSON();
      });
    }
    
    if (categorySelect) {
      categorySelect.addEventListener('change', async () => {
        updateWorldMapGeographyAvailability();
        updateComparisonGroupOptions();
        populateWorldMapKpiOptions();
        await updateWorldMapYearOptions();
        updateWorldMapModeAvailability();
        updateWorldMapGeoJSON();
      });
    }

    comparisonSelect?.addEventListener('change', updateWorldMapGeoJSON);

    if (kpiSelect) {
      kpiSelect.addEventListener('change', async () => {
        await updateWorldMapYearOptions();
        updateWorldMapModeAvailability();
        updateWorldMapGeoJSON();
      });
    }

    if (yearSelect) {
      yearSelect.addEventListener('change', updateWorldMapGeoJSON);
    }

    valueModeSelect?.addEventListener('change', () => {
      updateWorldMapModeAvailability();
      updateWorldMapGeoJSON();
    });
    aggregationSelect?.addEventListener('change', updateWorldMapGeoJSON);
    geographySelect?.addEventListener('change', updateWorldMapGeoJSON);

    populateWorldMapKpiOptions();
    updateWorldMapGeographyAvailability();
    await restoreWorldMapUrlState();

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

function populateWorldMapKpiOptions(preferredKpi = null) {
  const select = document.getElementById('worldMapKpiSelect');
  if (!select) return;
  const grouping = document.getElementById('groupingSelect')?.value || "";
  const category = document.getElementById('categorySelect')?.value || "";

  let options = [];
  if (isClimateGrouping(grouping) && category) {
    const metrics = getClimateMetricOptions(category);
    if (!metrics.length) {
      select.textContent = "";
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "Coming soon: no connected hazard dataset yet";
      select.appendChild(option);
      select.disabled = true;
      return;
    }
    options = metrics.map(metric => {
      const meta = getKpiMetaByFilename(metric.kpi);
      const unitText = meta?.unit ? ` (${meta.unit})` : "";
      return {
        value: metric.kpi,
        label: `${metric.label}${unitText}`,
      };
    });
  } else {
    const countryKpis = META
      .filter(kpi => kpi.filename && kpi.world_kpi !== "e" && kpi.geo_type !== "region")
      .sort((a, b) => (a.title || a.filename).localeCompare(b.title || b.filename));
    options = countryKpis.map(kpi => ({
      value: kpi.filename,
      label: kpi.title || kpi.filename,
    }));
  }

  if (!options.length) {
    select.textContent = "";
    const option = document.createElement("option");
    option.value = "";
    option.textContent = isClimateGrouping(grouping)
      ? "No climate KPI available for this category"
      : "No KPI available";
    select.appendChild(option);
    select.disabled = true;
    return;
  }

  select.disabled = false;
  const fallback = isClimateGrouping(grouping)
    ? options[0]?.value
    : (options.some(option => option.value === "gdp") ? "gdp" : options[0]?.value);
  setSelectOptions(select, options, preferredKpi, fallback);
}

async function updateWorldMapYearOptions(preferredYear = null) {
  const kpiSelect = document.getElementById('worldMapKpiSelect');
  const yearSelect = document.getElementById('worldMapYearSelect');
  if (!kpiSelect || !yearSelect || !kpiSelect.value) return;
  const requestId = ++worldMapYearRequestId;
  yearSelect.disabled = true;
  worldMapSelectedKpiMeta = META.find(kpi => kpi.filename === kpiSelect.value) || null;
  worldMapSelectedKpiData = await loadKPIData(kpiSelect.value);
  if (requestId !== worldMapYearRequestId) return;
  const years = worldMapSelectedKpiMeta?.geo_type === "region"
    ? availableRegionYears(worldMapSelectedKpiData)
    : availableCountryYears(worldMapSelectedKpiData);
  yearSelect.textContent = "";
  years.forEach(year => {
    const option = document.createElement('option');
    option.value = String(year);
    option.textContent = String(year);
    yearSelect.appendChild(option);
  });
  const requested = Number(preferredYear);
  yearSelect.value = years.includes(requested) ? String(requested) : String(years[0] || "");
  yearSelect.disabled = years.length === 0;
}

function updateWorldMapModeAvailability() {
  const grouping = document.getElementById('groupingSelect')?.value || "";
  const kpi = document.getElementById('worldMapKpiSelect')?.value || "";
  const valueMode = document.getElementById('worldMapValueMode');
  const aggregation = document.getElementById('worldMapAggregationMode');
  const note = document.getElementById('world-map-mode-note');
  if (!valueMode || !aggregation) return;

  if (isClimateGrouping(grouping)) {
    const metric = getActiveClimateMetricConfig();
    if (!metric) {
      setSelectOptions(valueMode, [{ value: "index", label: "Index / rate" }], "index", "index");
      setSelectOptions(aggregation, [{ value: "median", label: "Median" }], "median", "median");
      valueMode.disabled = true;
      aggregation.disabled = true;
      if (note) {
        const category = document.getElementById('categorySelect')?.value || "";
        const config = getClimateCategoryConfig(category);
        note.textContent = `${config?.label || "Climate category"}: ${config?.description || "Hazard category is not connected to production data yet."} Regional layer is planned; current map remains country-based fallback only.`;
      }
      return;
    }

    valueMode.disabled = false;
    aggregation.disabled = false;
    const allowedValueModes = (metric?.valueModes || ["absolute"])
      .map(mode => ({ value: mode, label: WORLD_MAP_VALUE_MODE_LABELS[mode] || mode }));
    const selectedValueMode = setSelectOptions(
      valueMode,
      allowedValueModes,
      metric?.defaultValueMode,
      allowedValueModes[0]?.value,
    );

    const allowedAggregations = (metric?.aggregations || ["median"])
      .map(mode => ({ value: mode, label: getAggregationLabel(mode) }));
    setSelectOptions(
      aggregation,
      allowedAggregations,
      metric?.defaultAggregation,
      allowedAggregations[0]?.value,
    );

    if (note) {
      const meta = getKpiMetaByFilename(kpi);
      const category = document.getElementById('categorySelect')?.value || "";
      const categoryLabel = getClimateCategoryConfig(category)?.label || "Climate category";
      note.textContent = `${categoryLabel}: ${meta?.title || "Selected metric"}. ${describeMeasureType(metric?.measureType || "exposure")} Values: ${WORLD_MAP_VALUE_MODE_LABELS[selectedValueMode] || selectedValueMode}. Summary: ${getAggregationLabel(aggregation.value)}.`;
    }
    return;
  }

  setSelectOptions(valueMode, [
    { value: "absolute", label: "Absolute" },
    { value: "per_capita", label: "Per capita" },
  ], valueMode.value, "absolute");
  setSelectOptions(aggregation, [
    { value: "median", label: "Median" },
    { value: "sum", label: "Sum" },
  ], aggregation.value, "median");

  const summable = WORLD_MAP_SUMMABLE_KPIS.has(kpi);
  const perCapitaSupported = WORLD_MAP_PER_CAPITA_KPIS.has(kpi);
  valueMode.disabled = !perCapitaSupported;
  if (!perCapitaSupported) valueMode.value = "absolute";
  const sumOption = [...aggregation.options].find(option => option.value === "sum");
  const sumAllowed = summable && valueMode.value === "absolute";
  if (sumOption) sumOption.disabled = !sumAllowed;
  if (!sumAllowed && aggregation.value === "sum") aggregation.value = "median";
  if (note) note.textContent = perCapitaSupported
    ? "Absolute and per-capita views are available. Sum is available for absolute additive values; per-capita comparisons use the country median."
    : summable
      ? "This total can be summed across members, but an additional per-capita conversion is not meaningful for this KPI."
      : "This KPI is a rate, score, index or already normalised value. It is compared by country median; totals and an additional per-capita conversion would be misleading.";
}

function readWorldMapUrlState() {
  const params = new URLSearchParams(window.location.search);
  return {
    grouping: params.get("grouping") || "",
    category: params.get("group") || "",
    comparison: params.get("compare") || "",
    kpi: params.get("kpi") || "",
    year: params.get("year") || "",
    valueMode: params.get("value") || "absolute",
    aggregation: params.get("aggregate") || "median",
    geography: params.get("geo") || "countries",
  };
}

function syncWorldMapUrl() {
  const grouping = document.getElementById('groupingSelect')?.value || "";
  const category = document.getElementById('categorySelect')?.value || "";
  const comparison = document.getElementById('comparisonGroupSelect')?.value || "";
  const kpi = document.getElementById('worldMapKpiSelect')?.value || "";
  const year = document.getElementById('worldMapYearSelect')?.value || "";
  const valueMode = document.getElementById('worldMapValueMode')?.value || "absolute";
  const aggregation = document.getElementById('worldMapAggregationMode')?.value || "median";
  const geography = document.getElementById('worldMapGeographyMode')?.value || "countries";
  const url = new URL(window.location.href);
  const values = { grouping, group: category, compare: comparison, kpi, year, value: valueMode, aggregate: aggregation, geo: geography };
  Object.entries(values).forEach(([key, value]) => {
    if (value) url.searchParams.set(key, value);
    else url.searchParams.delete(key);
  });
  window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
}

async function restoreWorldMapUrlState() {
  const state = readWorldMapUrlState();
  const groupingSelect = document.getElementById('groupingSelect');
  const categorySelect = document.getElementById('categorySelect');
  const comparisonSelect = document.getElementById('comparisonGroupSelect');
  const kpiSelect = document.getElementById('worldMapKpiSelect');
  const geographySelect = document.getElementById('worldMapGeographyMode');
  if (groupingSelect && [...groupingSelect.options].some(option => option.value === state.grouping)) {
    groupingSelect.value = state.grouping;
  }
  updateCategoryOptions();
  updateWorldMapGeographyAvailability();
  if (categorySelect && [...categorySelect.options].some(option => option.value === state.category)) {
    categorySelect.value = state.category;
  }
  updateWorldMapGeographyAvailability();
  updateComparisonGroupOptions();
  if (comparisonSelect && [...comparisonSelect.options].some(option => option.value === state.comparison)) {
    comparisonSelect.value = state.comparison;
  }
  populateWorldMapKpiOptions(state.kpi);
  if (kpiSelect && [...kpiSelect.options].some(option => option.value === state.kpi)) kpiSelect.value = state.kpi;
  await updateWorldMapYearOptions(state.year);
  const valueMode = document.getElementById('worldMapValueMode');
  const aggregation = document.getElementById('worldMapAggregationMode');
  if (geographySelect && [...geographySelect.options].some(option => option.value === state.geography)) geographySelect.value = state.geography;
  if (valueMode && [...valueMode.options].some(option => option.value === state.valueMode)) valueMode.value = state.valueMode;
  if (aggregation && [...aggregation.options].some(option => option.value === state.aggregation)) aggregation.value = state.aggregation;
  updateWorldMapModeAvailability();
  if (groupingSelect?.value && categorySelect?.value) updateWorldMapGeoJSON();
  else syncWorldMapUrl();
}

function clearWorldMapSelection() {
  if (worldMapLayer && worldMap) {
    worldMap.removeLayer(worldMapLayer);
    worldMapLayer = null;
  }
  document.getElementById('world-group-summary')?.setAttribute('hidden', '');
  document.getElementById('world-map-legend')?.classList.add('hidden');
}

function updateCategoryOptions() {
  const groupingSelect = document.getElementById('groupingSelect');
  const categorySelect = document.getElementById('categorySelect');
  
  if (!groupingSelect || !categorySelect) return;
  
  const grouping = groupingSelect.value;
  categorySelect.innerHTML = '<option value="">Select category...</option>';
  categorySelect.disabled = !grouping;
  
  if (grouping === WORLD_MAP_CLIMATE_GROUPING) {
    Object.entries(WORLD_MAP_CLIMATE_CATEGORIES).forEach(([categoryKey, config]) => {
      if (!getClimateMetricOptions(categoryKey).length) return;
      const option = document.createElement('option');
      option.value = categoryKey;
      option.textContent = config.label;
      categorySelect.appendChild(option);
    });
    Object.entries(WORLD_MAP_CLIMATE_PLACEHOLDER_CATEGORIES).forEach(([categoryKey, config]) => {
      const option = document.createElement('option');
      option.value = categoryKey;
      option.textContent = config.label;
      categorySelect.appendChild(option);
    });
  } else if (grouping === 'groups') {
    // Füge Groups aus groups.json hinzu
    Object.keys(worldMapGroups).sort((a, b) => getWorldMapGroupTitle(a).localeCompare(getWorldMapGroupTitle(b))).forEach(groupName => {
      const option = document.createElement('option');
      option.value = groupName;
      const members = worldMapGroups[groupName].members || worldMapGroups[groupName];
      const memberCount = Array.isArray(members) ? members.length : 0;
      option.textContent = `${getWorldMapGroupTitle(groupName)} (${memberCount} countries)`;
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
  
  categorySelect.disabled = !grouping;
  updateComparisonGroupOptions();
}

function updateComparisonGroupOptions() {
  const grouping = document.getElementById('groupingSelect')?.value || "";
  const primary = document.getElementById('categorySelect')?.value || "";
  const select = document.getElementById('comparisonGroupSelect');
  const wrapper = document.getElementById('comparisonGroupWrapper');
  if (!select) return;
  const previous = select.value;
  select.textContent = "";
  const empty = document.createElement('option');
  empty.value = "";
  empty.textContent = "No comparison";
  select.appendChild(empty);
  if (grouping === "groups") {
    Object.keys(worldMapGroups)
      .filter(groupName => groupName !== primary)
      .sort((a, b) => getWorldMapGroupTitle(a).localeCompare(getWorldMapGroupTitle(b)))
      .forEach(groupName => {
        const option = document.createElement('option');
        option.value = groupName;
        option.textContent = getWorldMapGroupTitle(groupName);
        select.appendChild(option);
      });
  }
  select.disabled = grouping !== "groups" || !primary;
  if ([...select.options].some(option => option.value === previous)) select.value = previous;
  if (wrapper) wrapper.hidden = grouping !== "groups";
}

function resolveWorldMapCountry(feature) {
  const properties = feature?.properties || {};
  const iso = (
    properties.iso_a3_eh || properties.ISO_A3_EH || properties.ISO_A3 || properties.iso_a3 ||
    properties.ADM0_A3 || properties.adm0_a3 || properties.SOV_A3 || properties.sov_a3 ||
    properties.WB_A3 || properties.wb_a3 || properties.gu_a3 || properties.su_a3 || feature?.id || ""
  ).toUpperCase();
  const isoMatch = Object.entries(worldMapCountries).find(([, country]) =>
    [country.iso_a3, country.iso3, country.ISO_A3].some(code => String(code || "").toUpperCase() === iso)
  )?.[0];
  if (isoMatch) return isoMatch;
  const rawName = properties.name || properties.NAME || properties.ADMIN || properties.COUNTRY || properties.SOVEREIGNT || iso;
  const aliases = {
    "United States of America": "United States",
    "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
    "Russian Federation": "Russia",
    "Iran (Islamic Republic of)": "Iran",
    "Korea, Republic of": "South Korea",
    "Venezuela (Bolivarian Republic of)": "Venezuela",
    "Bolivia (Plurinational State of)": "Bolivia",
    "Lao People's Democratic Republic": "Laos",
    "Syrian Arab Republic": "Syria",
    "Republic of Serbia": "Serbia",
    "Czech Republic": "Czechia",
    "Slovak Republic": "Slovakia",
  };
  const mapped = worldMapCountryMappings[rawName] || aliases[rawName] || rawName;
  return Object.keys(worldMapCountries).find(country => country.toLowerCase() === String(mapped).toLowerCase()) || mapped;
}

function selectedWorldMapValues(year, countries, valueMode) {
  const values = countryValuesForYear(worldMapSelectedKpiData, year, countries);
  if (valueMode !== "per_capita") return values;
  const population = countryValuesForYear(worldMapPopulation, year, countries);
  const perCapita = new Map();
  values.forEach((value, country) => {
    const denominator = population.get(country);
    if (Number.isFinite(denominator) && denominator > 0) perCapita.set(country, value / denominator);
  });
  return perCapita;
}

function updateWorldMapGeoJSON() {
  const groupingSelect = document.getElementById('groupingSelect');
  const categorySelect = document.getElementById('categorySelect');
  const comparisonSelect = document.getElementById('comparisonGroupSelect');
  
  if (!groupingSelect || !categorySelect || !worldMap || !window._worldGeoJSON) return;
  
  const grouping = groupingSelect.value;
  const category = categorySelect.value;
  const comparison = grouping === "groups" ? comparisonSelect?.value || "" : "";
  const categoryConfig = isClimateGrouping(grouping) ? getClimateCategoryConfig(category) : null;

  if (isClimateGrouping(grouping) && !getActiveClimateMetricConfig()) {
    clearWorldMapSelection();
    const modeNote = document.getElementById('world-map-mode-note');
    if (modeNote) {
      modeNote.textContent = `${categoryConfig?.label || "Climate category"}: ${categoryConfig?.description || "Hazard category is not connected to production data yet."}`;
    }
    updateMapLegend(grouping, category, 0, comparison, 0);
    syncWorldMapUrl();
    return;
  }

  if (isClimateGrouping(grouping) && categoryConfig?.geoType === "region") {
    if (worldMapLayer) {
      worldMap.removeLayer(worldMapLayer);
      worldMapLayer = null;
    }
    renderWorldMapRegionLayer(categoryConfig, category);
    return;
  }
  
  // Entferne bestehende GeoJSON Layer
  if (worldMapLayer) {
    worldMap.removeLayer(worldMapLayer);
    worldMapLayer = null;
  }
  
  if (!grouping || !category) {
    clearWorldMapSelection();
    syncWorldMapUrl();
    return;
  }
  
  // Finde relevante Länder
  let relevantCountries = [];
  
  if (isClimateGrouping(grouping)) {
    const selectedYear = Number(document.getElementById('worldMapYearSelect')?.value);
    const realCountries = worldMapRealCountryNames();
    relevantCountries = (worldMapSelectedKpiData || [])
      .filter(row => Number(row.year) === selectedYear && realCountries.has(row.country) && Number.isFinite(row.value))
      .map(row => row.country);
    relevantCountries = [...new Set(relevantCountries)];
  } else if (grouping === 'groups' && worldMapGroups[category]) {
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
  const comparisonCountries = comparison && worldMapGroups[comparison]
    ? worldMapGroups[comparison].members || worldMapGroups[comparison]
    : [];
  const relevantCountriesSet = new Set(relevantCountries.map(c => c.toLowerCase()));
  const groupASet = new Set(relevantCountries);
  const groupBSet = new Set(comparisonCountries);
  const selectedYear = Number(document.getElementById('worldMapYearSelect')?.value);
  const valueMode = document.getElementById('worldMapValueMode')?.value || "absolute";
  const selectedCountries = new Set([...groupASet, ...groupBSet]);
  const choroplethValues = selectedWorldMapValues(selectedYear, selectedCountries, valueMode);
  const intensities = percentileIntensities(choroplethValues);
  
  // Erstelle ISO-Lookup für relevante Länder (wie in countries.html)
  const isoByName = {};
  Object.entries(worldMapCountries).forEach(([name, data]) => {
    if (data.iso2) isoByName[name.toLowerCase()] = data.iso2.toUpperCase();
    if (data.iso3) isoByName[name.toLowerCase()] = data.iso3.toUpperCase();
  });
  
  // Erstelle GeoJSON Layer mit Styling
  worldMapLayer = L.geoJSON(window._worldGeoJSON, {
    style: feature => {
      const resolvedCountry = resolveWorldMapCountry(feature);
      const membership = classifyGroupMembership(resolvedCountry, groupASet, groupBSet);
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
      
      const groupColor = WORLD_MAP_GROUP_COLORS[membership];
      const intensity = intensities.get(resolvedCountry);
      return {
        fillColor: groupColor
          ? (Number.isFinite(intensity) ? mixWithWhite(groupColor.fill, intensity) : '#e8edf2')
          : '#ddd',
        weight: groupColor ? 2 : 1,
        opacity: 1,
        color: groupColor ? groupColor.border : '#999',
        dashArray: membership === "overlap" ? "5 3" : null,
        fillOpacity: groupColor ? 0.82 : 0.25
      };
    },
    onEachFeature: (f, layer) => {
      // 🧩 ISO-Resolver (same as countries.html)
      const iso = (
        f.properties.iso_a3_eh || f.properties.ISO_A3_EH ||
        f.properties.ISO_A3 || f.properties.iso_a3 ||
        f.properties.ADM0_A3 || f.properties.adm0_a3 ||
        f.properties.SOV_A3 || f.properties.sov_a3 ||
        f.properties.WB_A3 || f.properties.wb_a3 ||
        f.properties.gu_a3 || f.properties.su_a3 ||
        f.id || ""
      ).toUpperCase();

      // 🧭 Fallback to name resolution
      const cname = resolveWorldMapCountry(f);

      // Get population value
      const selectedKpiRow = worldMapSelectedKpiData.find(
        row => row.country === cname && Number(row.year) === selectedYear && Number.isFinite(row.value)
      );
      const currentYear = Number.isFinite(selectedYear) ? selectedYear : new Date().getFullYear();
      let popValue = null;
      for (let year = currentYear; year >= currentYear - 5; year--) {
        const popData = worldMapPopulation.find(p => p.country === cname && p.year === year);
        if (popData && popData.value) {
          popValue = popData.value;
          break;
        }
      }

      const info = worldMapCountries[cname] || {};
      const flagSrc = info.flag ||
        (info.iso_a2
          ? `images/flag/${String(info.iso_a2).toLowerCase()}.svg`
          : "images/flag/question.svg");
      
      const displayedKpiValue = choroplethValues.get(cname);
      const displayedUnit = valueMode === "per_capita"
        ? `${worldMapSelectedKpiMeta?.unit || "units"} per person`
        : worldMapSelectedKpiMeta?.unit || "";
      const selectedKpiValue = Number.isFinite(displayedKpiValue)
        ? formatWorldMapNumber(displayedKpiValue, displayedUnit)
        : "no data";
      const displayValue = `${worldMapSelectedKpiMeta?.title || "Selected KPI"}: ${selectedKpiValue}`;
      const populationText = Number.isFinite(popValue) ? `${(popValue / 1000000).toFixed(1)}M` : "no data";

      const tooltip = `
        <div class="map-tooltip">
          <div class="map-tooltip__header">
            <img class="map-tooltip__flag" src="${flagSrc}" alt="Flag of ${cname}" loading="lazy" />
            <div class="map-tooltip__title">${cname}</div>
          </div>
          <div class="map-tooltip__value">${displayValue}</div>
          <div class="map-tooltip__meta">
            <div class="map-tooltip__meta-row">Year: ${Number.isFinite(selectedYear) ? selectedYear : "–"}</div>
            <div class="map-tooltip__meta-row">Population: ${populationText}</div>
            <div class="map-tooltip__meta-row">Capital: ${info.capital || "–"}</div>
            <div class="map-tooltip__meta-row">Gov: ${info.government || "–"}</div>
            <div class="map-tooltip__meta-row">Languages: ${info.languages || "–"}</div>
          </div>
        </div>
      `;
      layer.bindTooltip(tooltip, { sticky: true });
      layer.on("tooltipopen", e => {
        const flag = e.tooltip.getElement()?.querySelector(".map-tooltip__flag");
        if (!flag) return;
        const useFallbackFlag = () => {
          flag.src = "images/flag/question.svg";
        };
        flag.addEventListener("error", useFallbackFlag, { once: true });
        if (flag.complete && flag.naturalWidth === 0) {
          useFallbackFlag();
        }
      });

      layer.on({
        mouseover: e => e.target.setStyle({ weight: 2.5, fillOpacity: 0.95 }),
        mouseout: e => worldMapLayer.resetStyle(e.target)
      });
    }
  }).addTo(worldMap);
  
  // Update context legend
  updateMapLegend(grouping, category, relevantCountries.length, comparison, comparisonCountries.length);
  renderWorldGroupSummary(grouping, category, relevantCountries, comparison, comparisonCountries);
  updateWorldMapVisualLegend(category, comparison);
  syncWorldMapUrl();
}

function appendWorldSummaryCard(container, label, value, meta, modifier = "") {
  const card = document.createElement('article');
  card.className = 'world-group-summary__card';
  if (modifier) card.classList.add(`world-group-summary__card--${modifier}`);
  const labelElement = document.createElement('span');
  labelElement.className = 'world-group-summary__label';
  labelElement.textContent = label;
  const valueElement = document.createElement('strong');
  valueElement.className = 'world-group-summary__value';
  valueElement.textContent = value;
  const metaElement = document.createElement('small');
  metaElement.className = 'world-group-summary__meta';
  metaElement.textContent = meta;
  card.append(labelElement, valueElement, metaElement);
  container.appendChild(card);
}

function appendWorldComparisonCard(container, label, groupA, groupB) {
  const card = document.createElement('article');
  card.className = 'world-group-summary__card';
  const labelElement = document.createElement('span');
  labelElement.className = 'world-group-summary__label';
  labelElement.textContent = label;
  const comparison = document.createElement('div');
  comparison.className = 'world-group-summary__comparison';
  [groupA, groupB].forEach(group => {
    const column = document.createElement('span');
    const title = document.createElement('b');
    title.textContent = group.label;
    const value = document.createElement('strong');
    value.className = 'world-group-summary__value';
    value.textContent = group.value;
    const meta = document.createElement('small');
    meta.textContent = group.meta;
    column.append(title, value, meta);
    comparison.appendChild(column);
  });
  card.append(labelElement, comparison);
  container.appendChild(card);
}

function renderWorldGroupSummary(grouping, category, members, comparison = "", comparisonMembers = []) {
  const summary = document.getElementById('world-group-summary');
  const title = document.getElementById('world-group-summary-title');
  const context = document.getElementById('world-group-summary-context');
  const cards = document.getElementById('world-group-summary-cards');
  const note = document.getElementById('world-group-summary-note');
  const year = Number(document.getElementById('worldMapYearSelect')?.value);
  if (!summary || !title || !context || !cards || !note || !members.length || !Number.isFinite(year)) return;

  const realCountries = worldMapRealCountryNames();
  const population = calculateAdditiveShare(worldMapPopulation, members, year, realCountries);
  const gdp = calculateAdditiveShare(worldMapGdp, members, year, realCountries);
  const emissions = calculateAdditiveShare(worldMapEmissions, members, year, realCountries);
  const valueMode = document.getElementById('worldMapValueMode')?.value || "absolute";
  const aggregation = document.getElementById('worldMapAggregationMode')?.value || "median";
  const selectedMetric = calculateGroupMetric(worldMapSelectedKpiData, members, year, {
    valueMode, aggregation, populationData: worldMapPopulation, areaData: worldMapArea,
  });
  const groupLabel = grouping === 'groups' ? getWorldMapGroupTitle(category) : category;
  const comparisonLabel = comparison ? getWorldMapGroupTitle(comparison) : "";
  const metricTitle = worldMapSelectedKpiMeta?.title || worldMapSelectedKpiMeta?.filename || "Selected KPI";
  const metricUnit = worldMapSelectedKpiMeta?.unit || "";

  title.textContent = comparisonLabel ? `${groupLabel} vs ${comparisonLabel}` : `${groupLabel} summary`;
  summary.classList.toggle('world-group-summary--comparison', Boolean(comparisonMembers.length));
  context.textContent = `Selected country KPI: ${metricTitle}, ${year} · ${WORLD_MAP_VALUE_MODE_LABELS[valueMode] || valueMode} · ${getAggregationLabel(aggregation)}.`;
  cards.textContent = "";
  if (!comparisonMembers.length) {
    appendWorldSummaryCard(cards, "Members", String(members.length), "Defined members / matching countries");
    appendWorldSummaryCard(cards, "World population share", Number.isFinite(population.share) ? `${(population.share * 100).toFixed(1)}%` : "No data", `Year ${population.year ?? "–"} · coverage ${formatCoverage(population.covered, population.total)}`);
    appendWorldSummaryCard(cards, "World GDP share", Number.isFinite(gdp.share) ? `${(gdp.share * 100).toFixed(1)}%` : "No data", `Current USD · year ${gdp.year ?? "–"} · coverage ${formatCoverage(gdp.covered, gdp.total)}`);
    appendWorldSummaryCard(cards, "World CO₂ share", Number.isFinite(emissions.share) ? `${(emissions.share * 100).toFixed(1)}%` : "No data", `Territorial emissions · year ${emissions.year ?? "–"} · coverage ${formatCoverage(emissions.covered, emissions.total)}`);
    appendWorldSummaryCard(cards, `${getAggregationLabel(aggregation)}: ${metricTitle}`, formatWorldMapNumber(selectedMetric.value, valueMode === "per_capita" ? `${metricUnit || "units"} per person` : metricUnit), `Year ${year} · coverage ${formatCoverage(selectedMetric.covered, selectedMetric.total)}`);
  } else {
    const comparisonPopulation = calculateAdditiveShare(worldMapPopulation, comparisonMembers, year, realCountries);
    const comparisonGdp = calculateAdditiveShare(worldMapGdp, comparisonMembers, year, realCountries);
    const comparisonEmissions = calculateAdditiveShare(worldMapEmissions, comparisonMembers, year, realCountries);
    const comparisonMetric = calculateGroupMetric(worldMapSelectedKpiData, comparisonMembers, year, { valueMode, aggregation, populationData: worldMapPopulation, areaData: worldMapArea });
    const pair = (aValue, aMeta, bValue, bMeta) => [
      { label: groupLabel, value: aValue, meta: aMeta },
      { label: comparisonLabel, value: bValue, meta: bMeta },
    ];
    appendWorldComparisonCard(cards, "Members", ...pair(String(members.length), "Defined members", String(comparisonMembers.length), "Defined members"));
    appendWorldComparisonCard(cards, "World population share", ...pair(Number.isFinite(population.share) ? `${(population.share * 100).toFixed(1)}%` : "No data", `Year ${population.year ?? "–"} · ${formatCoverage(population.covered, population.total)}`, Number.isFinite(comparisonPopulation.share) ? `${(comparisonPopulation.share * 100).toFixed(1)}%` : "No data", `Year ${comparisonPopulation.year ?? "–"} · ${formatCoverage(comparisonPopulation.covered, comparisonPopulation.total)}`));
    appendWorldComparisonCard(cards, "World GDP share", ...pair(Number.isFinite(gdp.share) ? `${(gdp.share * 100).toFixed(1)}%` : "No data", `Year ${gdp.year ?? "–"} · ${formatCoverage(gdp.covered, gdp.total)}`, Number.isFinite(comparisonGdp.share) ? `${(comparisonGdp.share * 100).toFixed(1)}%` : "No data", `Year ${comparisonGdp.year ?? "–"} · ${formatCoverage(comparisonGdp.covered, comparisonGdp.total)}`));
    appendWorldComparisonCard(cards, "World CO₂ share", ...pair(Number.isFinite(emissions.share) ? `${(emissions.share * 100).toFixed(1)}%` : "No data", `Year ${emissions.year ?? "–"} · ${formatCoverage(emissions.covered, emissions.total)}`, Number.isFinite(comparisonEmissions.share) ? `${(comparisonEmissions.share * 100).toFixed(1)}%` : "No data", `Year ${comparisonEmissions.year ?? "–"} · ${formatCoverage(comparisonEmissions.covered, comparisonEmissions.total)}`));
    const displayUnit = valueMode === "per_capita" ? `${metricUnit || "units"} per person` : metricUnit;
    appendWorldComparisonCard(cards, `${getAggregationLabel(aggregation)}: ${metricTitle}`, ...pair(formatWorldMapNumber(selectedMetric.value, displayUnit), `Year ${year} · ${formatCoverage(selectedMetric.covered, selectedMetric.total)}`, formatWorldMapNumber(comparisonMetric.value, displayUnit), `Year ${year} · ${formatCoverage(comparisonMetric.covered, comparisonMetric.total)}`));
    const overlap = members.filter(country => new Set(comparisonMembers).has(country)).length;
    appendWorldSummaryCard(cards, "Overlap", `${overlap} countries`, `${groupLabel} ∩ ${comparisonLabel}`, "overlap");
  }
  note.textContent = "Population, GDP and CO₂ are additive shares of recognised-country totals. KPI colour intensity and the selected summary use the displayed value mode; missing members remain visible in coverage.";
  if (isClimateGrouping(grouping)) {
    const climateMetric = getActiveClimateMetricConfig();
    note.textContent = `${describeMeasureType(climateMetric?.measureType || "exposure")} Aggregation: ${getAggregationLabel(aggregation)}. Coverage and year depend on the selected climate metric.`;
  }
  summary.removeAttribute('hidden');
}

// === Update Context Legend Box ===
function updateWorldMapVisualLegend(category, comparison) {
  const grouping = document.getElementById('groupingSelect')?.value || "";
  const labelA = document.getElementById('legend-group-a-label');
  const labelB = document.getElementById('legend-group-b-label');
  const itemB = document.getElementById('legend-group-b-item');
  const overlap = document.getElementById('legend-overlap-item');
  const categoryLabel = isClimateGrouping(grouping)
    ? (getClimateCategoryConfig(category)?.label || "Climate selection")
    : getWorldMapGroupTitle(category);
  if (labelA) labelA.textContent = categoryLabel;
  if (labelB) labelB.textContent = comparison ? getWorldMapGroupTitle(comparison) : "Group B";
  if (itemB) itemB.hidden = !comparison;
  if (overlap) overlap.hidden = !comparison;
}

function updateMapLegend(grouping, category, countryCount, comparison = "", comparisonCount = 0) {
  const legendBox = document.getElementById('world-map-legend');
  const legendTitle = document.getElementById('legend-title');
  const legendContent = document.getElementById('legend-content');
  
  if (!legendBox || !legendTitle || !legendContent) return;
  
  let title = '';
  let content = '';
  
  if (isClimateGrouping(grouping)) {
    const config = getClimateCategoryConfig(category);
    const selectedMetric = getKpiMetaByFilename(document.getElementById('worldMapKpiSelect')?.value || "");
    const year = document.getElementById('worldMapYearSelect')?.value || "–";
    const valueMode = document.getElementById('worldMapValueMode')?.value || "absolute";
    const aggregation = document.getElementById('worldMapAggregationMode')?.value || "median";
    const geography = document.getElementById('worldMapGeographyMode')?.value || "countries";
    title = `${config?.label || "Climate Hazards & Exposure"} (${countryCount} countries)`;
    content = `${config?.description || "Climate hazard/exposure view."} Metric: ${selectedMetric?.title || "–"}. Unit: ${selectedMetric?.unit || "n/a"}. Year: ${year}. Values: ${WORLD_MAP_VALUE_MODE_LABELS[valueMode] || valueMode}. Summary: ${getAggregationLabel(aggregation)}. Geography: ${geography}.`;
  } else if (grouping === 'groups') {
    const groupDescriptions = {
      'EU': 'The European Union seeks to ensure peace, stability, and shared prosperity in Europe. It creates a single market with free movement of goods, people, services, and capital. The EU coordinates policies on trade, climate, agriculture, and consumer protection. It supports democracy, human rights, and the rule of law among its members. The EU also provides funding for regional development. Its mission is deeper integration and long-term cooperation across Europe.',
      'G7': 'The G7 unites advanced industrial democracies to coordinate global economic policy. It focuses on financial stability, sustainable growth, and international security. The group discusses challenges such as climate change, development, and geopolitical tensions. G7 meetings help align positions before major global negotiations. The group has no formal treaties but influences global governance through joint statements. Its mission is to promote a stable and rules-based international order.',
      'G20': 'The G20 brings together the world\'s largest economies to address global financial and economic challenges. It promotes international cooperation on trade, investment, and fiscal policy. Members work to stabilize markets during crises and support sustainable development. The G20 also addresses climate change, health threats, and digital transformation. Although not a formal organization, it shapes major economic decisions worldwide. Its goal is to strengthen global economic resilience.',
      'BRICS': 'BRICS brings together major emerging economies to promote cooperation outside traditional Western-led institutions. The group focuses on economic development, trade, and financial coordination. It aims to increase the global influence of member states. BRICS created its own development bank to support infrastructure and growth projects. Members also discuss geopolitical issues and alternative governance models. The goal is a more balanced and multipolar world order.',
      'OECD': 'The OECD promotes economic growth, good governance, and social well-being. It provides research, policy recommendations, and data to help countries improve their economies. Members cooperate on taxation, education, trade, and environmental issues. The organization encourages transparent and evidence-based policymaking. It also monitors global trends and supports fair and sustainable development. The OECD\'s mission is to build better policies for better lives.',
      'NATO': 'NATO is a collective defense alliance committed to protecting the security of its members. An attack on one is considered an attack on all. The alliance promotes military cooperation, joint exercises, and crisis management. It also engages in peacekeeping and stabilizing missions worldwide. NATO supports democratic values and helps partners modernize their armed forces. Its core purpose is to ensure peace and security across the North Atlantic region.',
      'UNSecurityCouncilPermanent': 'The permanent members of the United Nations Security Council are China, France, Russia, the United Kingdom, and the United States. They hold permanent seats and veto power in decisions on international peace and security. This status gives them a central role in authorizing peacekeeping missions, sanctions, and the use of force under the UN Charter. The group reflects the post-World War II order and remains one of the most influential structures in global governance.',
      'ASEAN': 'ASEAN seeks to strengthen political and economic cooperation in Southeast Asia. It supports regional stability, conflict prevention, and peaceful dialogue. The group works to integrate economies through trade agreements and shared development goals. ASEAN also cooperates on education, health, and environmental issues. It promotes cultural exchange and regional identity. Its long-term aim is a more unified and resilient Southeast Asia.',
      'Mercosur': 'Mercosur promotes economic integration among South American countries. It aims to create a free-trade area with reduced tariffs and common external policies. Members cooperate on infrastructure, industry, and agricultural development. The bloc also works to coordinate foreign policy positions. Mercosur supports regional mobility and cultural exchange. Its mission is a more unified and competitive South American market.',
      'APEC': 'APEC works to promote free and open trade across the Asia-Pacific region. It aims to reduce barriers to commerce and support sustainable economic growth. The group emphasizes cooperation rather than binding treaties. APEC also supports innovation, digital transformation, and economic integration. Its projects help improve productivity and strengthen supply chains. The core mission is to create a stable, prosperous Asia-Pacific community.',
      'AfricanUnion': 'The African Union promotes unity and cooperation among African states. It aims to support economic development, peace, and political stability across the continent. The AU works to coordinate policies on trade, infrastructure, and security. It also plays a major role in conflict resolution and peacekeeping. The organization advocates for Africa\'s interests on the global stage. Its long-term mission is to build a more integrated and prosperous Africa.'
    };
    
    const groupTitle = getWorldMapGroupTitle(category);
    title = comparison
      ? `${groupTitle} (${countryCount}) vs ${getWorldMapGroupTitle(comparison)} (${comparisonCount})`
      : `${groupTitle} (${countryCount} countries)`;
    content = comparison
      ? `Compare ${groupTitle} and ${getWorldMapGroupTitle(comparison)}. Blue and orange identify exclusive members; purple identifies overlap. Colour intensity shows the selected country KPI.`
      : worldMapGroups[category]?.description ||
      groupDescriptions[category] ||
      `${groupTitle} is an international grouping of ${countryCount} countries.`;
    
  } else if (grouping === 'language') {
    // Calculate total speakers from actual population data
    let totalPopulation = 0;
    
    // Get all countries where this language is spoken
    const languageCountries = Object.keys(worldMapCountries).filter(country => {
      const langs = worldMapCountries[country].languages || '';
      return langs.split(',').map(l => l.trim()).includes(category);
    });
    
    // Sum up their populations (use latest year available)
    languageCountries.forEach(country => {
      const popData = worldMapPopulation.find(p => p.country === country && p.year >= 2020);
      if (popData && popData.value) {
        totalPopulation += popData.value;
      }
    });
    
    // Format population nicely
    let speakers = '';
    if (totalPopulation >= 1000000000) {
      speakers = (totalPopulation / 1000000000).toFixed(1) + ' billion';
    } else if (totalPopulation >= 1000000) {
      speakers = (totalPopulation / 1000000).toFixed(0) + ' million';
    } else {
      speakers = totalPopulation.toLocaleString();
    }
    
    title = `${category} Language`;
    content = `${category} is an official language in ${countryCount} countries with a combined population of approximately ${speakers} people.`;
    
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
} else if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", initWorldPageWithMap);
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    calculateAdditiveShare,
    calculateMedianMetric,
    calculateGroupMetric,
    classifyGroupMembership,
    countryValuesForYear,
    formatCoverage,
    percentileIntensities,
  };
}
