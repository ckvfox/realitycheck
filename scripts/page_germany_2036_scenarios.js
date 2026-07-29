(function (root, factory) {
  // Model UI version 1.1: household selection and citizen-action extension.
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.RCGermany2036 = factory();
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const SCORE_LABELS = {
    prosperity: "Prosperity", income: "Real income", employment: "Employment",
    energySecurity: "Energy security", technology: "Technology sovereignty",
    state: "State capacity", climateResilience: "Climate resilience", social: "Social cohesion"
  };
  const SCORE_LABELS_DE = {
    prosperity: "Wohlstand", income: "Realeinkommen", employment: "Beschäftigung",
    energySecurity: "Energiesicherheit", technology: "Technologische Eigenständigkeit",
    state: "Staatliche Handlungsfähigkeit", climateResilience: "Klimaresilienz", social: "Sozialer Zusammenhalt"
  };
  function isGerman() { return typeof document !== "undefined" && document.documentElement.lang === "de"; }
  function ui(en, de) { return isGerman() ? de : en; }

  function clamp(value, min, max) { return Math.min(max, Math.max(min, Number(value))); }
  function midpoint(band) { return (Number(band[0]) + Number(band[1])) / 2; }
  function orderedBand(low, high) {
    const values = [Number(low), Number(high)].sort((a, b) => a - b);
    return values.map(value => Math.round(value * 10) / 10);
  }

  function validatePayload(data) {
    if (!data || !data.meta || !data.scenarios || !data.metrics || !data.influences) return false;
    const keys = ["renewal", "pressure", "loss"];
    return keys.every(key => {
      const item = data.scenarios[key];
      return item && typeof item.story === "string" && item.story.length > 0 && item.bands && item.scores && item.sliderBase &&
        data.metrics.every(metric => Array.isArray(item.bands[metric.id]) && item.bands[metric.id].length === 2);
    });
  }

  function calculateModel(data, scenarioKey, settings) {
    if (!validatePayload(data) || !data.scenarios[scenarioKey]) throw new Error("Invalid scenario model.");
    const scenario = data.scenarios[scenarioKey];
    const normalized = {};
    Object.keys(scenario.sliderBase).forEach(id => { normalized[id] = clamp(settings[id], -2, 2); });
    const bands = {};
    data.metrics.forEach(metric => {
      let delta = 0;
      Object.keys(normalized).forEach(id => {
        delta += (normalized[id] - scenario.sliderBase[id]) * Number(data.influences[id][metric.id] || 0);
      });
      const original = scenario.bands[metric.id];
      bands[metric.id] = orderedBand(clamp(original[0] + delta, 50, 250), clamp(original[1] + delta, 50, 250));
    });
    return { scenarioKey, settings: normalized, bands };
  }

  function interpolateBand(band, year, baseYear, targetYear) {
    const share = clamp((year - baseYear) / (targetYear - baseYear), 0, 1);
    return orderedBand(100 + (band[0] - 100) * share, 100 + (band[1] - 100) * share);
  }

  function householdOutcome(model, household) {
    const b = model.bands;
    const s = household.sensitivity;
    const benefit = (midpoint(b.income) - 100) * s.income + (midpoint(b.employment) - 100) * s.employment;
    const burden = (midpoint(b.energy) - 100) * s.energy * .35 + (midpoint(b.climate) - 100) * s.climate * .16;
    const state = (midpoint(b.state) - 100) * s.state * .35;
    const center = clamp(100 + (benefit - burden + state) / (s.income + s.employment + s.energy + s.climate + s.state), 65, 135);
    return orderedBand(center - 4, center + 4);
  }

  function isCustom(settings, base) {
    return Object.keys(base).some(id => Number(settings[id]) !== Number(base[id]));
  }

  function formatBand(band) { return `${band[0].toLocaleString("en-GB")}–${band[1].toLocaleString("en-GB")}`; }
  function escapeText(value) { return String(value == null ? "" : value); }

  function boot() {
    const node = document.getElementById("germany-2036-data");
    const root = document.getElementById("germany-2036");
    if (!node || !root) return;
    let data;
    try { data = JSON.parse(node.textContent); } catch (_) { data = null; }
    if (!validatePayload(data)) {
      root.querySelector("[data-scenario-status]").textContent = ui("Scenario data is unavailable.", "Szenariodaten sind nicht verfügbar.");
      return;
    }

    let active = data.meta.defaultScenario;
    let settings = { ...data.scenarios[active].sliderBase };
    let charts = {};
    const scenarioKeys = Array.isArray(data.meta.scenarioOrder)
      ? data.meta.scenarioOrder.filter(key => data.scenarios[key])
      : Object.keys(data.scenarios);

    const tabs = root.querySelector("[data-scenario-tabs]");
    scenarioKeys.forEach(key => {
      const scenario = data.scenarios[key];
      const button = document.createElement("button");
      button.type = "button";
      button.className = `scenario-tab scenario-tab--${scenario.class}`;
      button.dataset.scenario = key;
      button.textContent = scenario.label;
      button.addEventListener("click", () => selectScenario(key));
      tabs.appendChild(button);
    });

    const sliderBox = root.querySelector("[data-scenario-sliders]");
    data.sliders.forEach(item => {
      const wrapper = document.createElement("div");
      wrapper.className = "scenario-slider";
      const label = document.createElement("label");
      label.htmlFor = `scenario-${item.id}`;
      label.innerHTML = `<span>${escapeText(item.label)}</span><output data-output="${item.id}"></output>`;
      const input = document.createElement("input");
      input.type = "range"; input.min = "-2"; input.max = "2"; input.step = "1";
      input.id = `scenario-${item.id}`; input.dataset.slider = item.id;
      const scale = document.createElement("div");
      scale.className = "scenario-slider-scale";
      scale.innerHTML = `<span>${escapeText(item.left)}</span><span>${escapeText(item.right)}</span>`;
      input.addEventListener("input", () => { settings[item.id] = Number(input.value); render(); });
      wrapper.append(label, input, scale); sliderBox.appendChild(wrapper);
    });

    const householdSelect = root.querySelector("[data-household-select]");
    data.households.forEach(item => {
      const option = document.createElement("option"); option.value = item.id; option.textContent = item.label;
      householdSelect.appendChild(option);
    });
    householdSelect.addEventListener("change", () => renderHousehold());
    root.querySelector("[data-reset]").addEventListener("click", () => {
      settings = { ...data.scenarios[active].sliderBase }; render();
    });

    function selectScenario(key) {
      active = key; settings = { ...data.scenarios[key].sliderBase }; render();
    }

    function updateChart(name, config) {
      const canvas = root.querySelector(`[data-chart="${name}"]`);
      if (typeof Chart === "undefined" || !canvas) return;
      if (charts[name]) charts[name].destroy();
      charts[name] = new Chart(canvas.getContext("2d"), config);
    }

    function renderHousehold(modelOverride) {
      const model = modelOverride || calculateModel(data, active, settings);
      const household = data.households.find(item => item.id === householdSelect.value) || data.households[0];
      const band = householdOutcome(model, household);
      root.querySelector("[data-household-result]").innerHTML =
        `<strong>${ui("Household headroom 2036", "Finanzieller Haushaltsspielraum 2036")}: ${formatBand(band)}</strong><span>${ui("Index range, 2026 = 100 · modelled sensitivity", "Indexbereich, 2026 = 100 · modellierte Empfindlichkeit")}</span>`;
      root.querySelector("[data-household-daily]").textContent = household.daily;
      root.querySelector("[data-household-tax]").textContent = household.tax;
      root.querySelector("[data-household-energy]").textContent = household.energyText;
      root.querySelector("[data-household-housing]").textContent = household.housing;
      root.querySelector("[data-household-transfers]").textContent = household.transfers;
      root.querySelector("[data-household-risk]").textContent = household.risk;
      root.querySelector("[data-household-training]").textContent = household.training;
      root.querySelector("[data-household-help]").textContent = household.help;
    }

    function render() {
      const scenario = data.scenarios[active];
      const model = calculateModel(data, active, settings);
      root.querySelectorAll("[data-scenario]").forEach(button => {
        const selected = button.dataset.scenario === active;
        button.classList.toggle("is-active", selected);
        button.setAttribute("aria-pressed", selected ? "true" : "false");
      });
      root.querySelector("[data-scenario-name]").textContent = isCustom(settings, scenario.sliderBase) ? ui("Custom scenario", "Eigenes Szenario") : scenario.label;
      root.querySelector("[data-scenario-story]").textContent = scenario.story;
      root.querySelector("[data-scenario-premise]").textContent = scenario.premise;
      root.querySelector("[data-scenario-status]").textContent = data.meta.warning;
      const driverLabels = isGerman()
        ? {climate:"Klima",security:"Sicherheit",economy:"Wirtschaft",technology:"Technologie",society:"Gesellschaft und Demokratie"}
        : {climate:"Climate",security:"Security",economy:"Economy",technology:"Technology",society:"Society and democracy"};
      root.querySelector("[data-drivers]").innerHTML = Object.entries(scenario.drivers).map(([key, value]) => `<li><strong>${driverLabels[key]}:</strong> ${escapeText(value)}</li>`).join("");
      root.querySelectorAll("[data-slider]").forEach(input => {
        input.value = String(settings[input.dataset.slider]);
        root.querySelector(`[data-output="${input.dataset.slider}"]`).textContent = settings[input.dataset.slider] > 0 ? `+${settings[input.dataset.slider]}` : String(settings[input.dataset.slider]);
      });
      const cards = root.querySelector("[data-metric-cards]"); cards.replaceChildren();
      data.metrics.forEach(metric => {
        const card = document.createElement("div"); card.className = "scenario-metric";
        card.innerHTML = `<span>${escapeText(metric.label)}</span><strong>${formatBand(model.bands[metric.id])}</strong><small>${escapeText(metric.unit)}, 2026 = 100 · ${metric.direction === "lower" ? ui("lower is better", "niedriger ist besser") : ui("higher is better", "höher ist besser")}</small>`;
        cards.appendChild(card);
      });

      const colors = { renewal:"#27864a", pressure:"#d18a00", loss:"#b63838" };
      updateChart("comparison", {type:"bar",data:{labels:data.metrics.map(m => m.label),datasets:scenarioKeys.map(key => {const item=data.scenarios[key];return {label:item.short,data:data.metrics.map(m => midpoint(item.bands[m.id])),backgroundColor:colors[key]};})},options:{responsive:true,maintainAspectRatio:false,plugins:{tooltip:{callbacks:{afterLabel:ctx => `${ui("Range", "Bereich")}: ${formatBand(data.scenarios[scenarioKeys[ctx.datasetIndex]].bands[data.metrics[ctx.dataIndex].id])}`}}},scales:{y:{title:{display:true,text:ui("2036 index (2026 = 100)", "Index 2036 (2026 = 100)")}}}}});
      updateChart("timeline", {type:"line",data:{labels:data.timelineYears,datasets:[{label:ui("Real disposable income", "Reales verfügbares Einkommen"),data:data.timelineYears.map(year => midpoint(interpolateBand(model.bands.income, year, data.meta.baseYear, data.meta.targetYear))),borderColor:"#1a355e",backgroundColor:"#1a355e",borderDash:[7,4],tension:.15},{label:ui("Prosperity per capita", "Wohlstand je Einwohner"),data:data.timelineYears.map(year => midpoint(interpolateBand(model.bands.prosperity, year, data.meta.baseYear, data.meta.targetYear))),borderColor:"#27864a",backgroundColor:"#27864a",borderDash:[7,4],tension:.15}]},options:{responsive:true,maintainAspectRatio:false,plugins:{tooltip:{callbacks:{afterLabel:ctx => {const id=ctx.datasetIndex===0?"income":"prosperity";return `${ui("Range", "Bereich")}: ${formatBand(interpolateBand(model.bands[id], Number(ctx.label), data.meta.baseYear, data.meta.targetYear))}`;}}}},scales:{y:{title:{display:true,text:ui("schematic index path", "schematischer Indexverlauf")}}}}});
      const scoreLabels = isGerman() ? SCORE_LABELS_DE : SCORE_LABELS;
      updateChart("radar", {type:"radar",data:{labels:Object.keys(scoreLabels).map(k=>scoreLabels[k]),datasets:[{label:scenario.short,data:Object.keys(scoreLabels).map(k=>scenario.scores[k]),borderColor:colors[active],backgroundColor:`${colors[active]}33`,pointBackgroundColor:colors[active]}]},options:{responsive:true,maintainAspectRatio:false,scales:{r:{min:0,max:100,ticks:{stepSize:20}}}}});
      renderHousehold(model);
    }

    render();
  }

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
    else boot();
  }
  return { clamp, midpoint, orderedBand, validatePayload, calculateModel, interpolateBand, householdOutcome, isCustom };
});
