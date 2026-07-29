(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.RCIncomePyramid = api;
})(typeof window !== "undefined" ? window : null, function () {
  "use strict";
  function isGerman() { return typeof document !== "undefined" && document.documentElement.lang === "de"; }
  function ui(en, de) { return isGerman() ? de : en; }

  function relativeDifference(value, reference) {
    const amount = Number(value); const base = Number(reference);
    if (!Number.isFinite(amount) || !Number.isFinite(base) || base <= 0) return null;
    return (amount - base) / base * 100;
  }

  function classifyHouseholdGross(value, reference, bands) {
    const amount = Number(value); const base = Number(reference);
    if (!Number.isFinite(amount) || amount < 0 || !Number.isFinite(base) || base <= 0 || !Array.isArray(bands)) return null;
    const ratio = amount / base;
    return bands.find(band => (band.minRatio == null || ratio >= band.minRatio) && (band.maxRatio == null || ratio < band.maxRatio)) || null;
  }

  function validatePayload(data) {
    return Boolean(data && data.meta && Array.isArray(data.households) && data.households.length >= 5 && Array.isArray(data.benchmarkBands));
  }

  function formatEuro(value) { return `${Math.round(Number(value)).toLocaleString(isGerman() ? "de-DE" : "en-GB")} €`; }
  function differenceText(value, reference) {
    const difference = relativeDifference(value, reference);
    if (!Number.isFinite(difference)) return "–";
    if (Math.abs(difference) < .05) return ui("almost exactly at the reference average", "fast genau beim Vergleichsdurchschnitt");
    return isGerman()
      ? `${Math.abs(difference).toLocaleString("de-DE", { maximumFractionDigits: 1 })} % ${difference > 0 ? "über" : "unter"} dem Vergleichsdurchschnitt`
      : `${Math.abs(difference).toLocaleString("en-GB", { maximumFractionDigits: 1 })}% ${difference > 0 ? "above" : "below"} the reference average`;
  }

  function boot() {
    const root = document.getElementById("income-pyramid");
    const dataNode = document.getElementById("income-pyramid-data");
    if (!root || !dataNode) return;
    let data;
    try { data = JSON.parse(dataNode.textContent); } catch (_) { data = null; }
    if (!validatePayload(data)) { root.querySelector("[data-income-status]").textContent = ui("Income data is unavailable.", "Einkommensdaten sind nicht verfügbar."); return; }

    const householdSelect = root.querySelector("[data-income-household]");
    const grossInput = root.querySelector("[data-income-gross]");
    const form = root.querySelector(".income-form");
    data.households.forEach(item => {
      const option = document.createElement("option");
      option.value = item.id;
      option.textContent = item.label;
      option.title = item.description || item.label;
      householdSelect.appendChild(option);
    });

    function selectedHousehold() { return data.households.find(item => item.id === householdSelect.value) || data.households[0]; }
    function renderPyramid(activeBand) {
      const pyramid = root.querySelector("[data-income-pyramid]"); pyramid.replaceChildren();
      [...data.benchmarkBands].reverse().forEach(band => {
        const row = document.createElement("div"); row.className = "income-pyramid-row";
        row.style.setProperty("--pyramid-width", `${band.width}%`);
        if (activeBand && activeBand.id === band.id) {
          row.classList.add("is-active");
          row.setAttribute("aria-current", "true");
        }
        const title = document.createElement("strong"); title.textContent = band.label;
        const description = document.createElement("span"); description.textContent = band.description;
        const badges = document.createElement("span"); badges.className = "income-pyramid-badges";
        if (activeBand && activeBand.id === band.id) { const badge = document.createElement("b"); badge.textContent = ui("Your household", "Dein Haushalt"); badges.appendChild(badge); }
        row.append(title, description, badges); pyramid.appendChild(row);
      });
    }
    function render() {
      const household = selectedHousehold(); const amount = Number(grossInput.value);
      householdSelect.title = household.description || household.label;
      const householdHelp = root.querySelector("[data-income-household-help]");
      if (householdHelp) householdHelp.textContent = household.description || "";
      const valid = Number.isFinite(amount) && amount > 0;
      const band = valid ? classifyHouseholdGross(amount, household.grossAverage, data.benchmarkBands) : null;
      renderPyramid(band);
      const result = root.querySelector("[data-income-household-result]");
      if (valid && band) {
        result.innerHTML = isGerman()
          ? `<strong>${band.label}: ${formatEuro(amount)} gesamtes Bruttohaushaltseinkommen pro Jahr</strong><span>Du liegst ${differenceText(amount, household.grossAverage)} für den amtlichen Typ „${household.referenceLabel}“ (${formatEuro(household.grossAverage)}, EU-SILC 2025). Der Vergleich umfasst das durchschnittliche Bruttoeinkommen aller Haushalte dieser Kategorie.</span>`
          : `<strong>${band.label}: ${formatEuro(amount)} total annual household gross</strong><span>You are ${differenceText(amount, household.grossAverage)} for the official category “${household.referenceLabel}” (${formatEuro(household.grossAverage)}, EU-SILC 2025). The reference is the average gross income of all households in this category.</span>`;
      } else result.innerHTML = ui("<strong>Enter the household's total annual gross income</strong><span>Use the combined figure for everyone in the household, including relevant non-employment gross income.</span>", "<strong>Gesamtes jährliches Bruttohaushaltseinkommen eingeben</strong><span>Nutze die gemeinsame Zahl für alle Personen im Haushalt, einschließlich passender Bruttoeinnahmen außerhalb von Beschäftigung.</span>");
      root.querySelector("[data-income-status]").textContent = valid ? ui("Comparison updated.", "Vergleich aktualisiert.") : ui("Please enter total annual household gross income.", "Bitte das gesamte jährliche Bruttohaushaltseinkommen eingeben.");
    }
    form.addEventListener("submit", event => event.preventDefault());
    householdSelect.addEventListener("change", render); grossInput.addEventListener("input", render); render();
  }
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true }); else boot();
  }
  return { classifyHouseholdGross, relativeDifference, validatePayload };
});
