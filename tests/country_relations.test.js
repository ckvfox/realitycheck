const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const script = fs.readFileSync("scripts/script.js", "utf8");
const logic = script.slice(script.indexOf("const relationUnits"), script.indexOf("/* ========= View"));
const input = { value: "percapita" };
const observations = new Map([
  ["Germany", new Map([[2022, { year: 2022, value: 27 }]])],
  ["Norway", new Map([[2022, { year: 2022, value: 37 }]])]
]);
const context = vm.createContext({
  document: { getElementById: () => input },
  currentValueLookup: observations,
  isKnownCountry: () => true,
  normalizeYear: Number,
  relationKey: (country, year) => `${country}/${year}`,
  relationLookups: {
    percapita: new Map([["Germany/2022", 84e6], ["Norway/2022", 5.5e6]]),
    pergdp: new Map([["Germany/2022", 4e12], ["Norway/2022", 6e11]])
  }
});
vm.runInContext(logic, context);
const meta = { relation: "*", unit: "count" };

const population = context.relationDisplay(meta);
assert.equal(population.unit, "count per 1 million people");
assert.equal(context.formatRelationValue(context.applyRelation(27, "Germany", 2022, population)), "0.32");
assert.equal(context.applyRelation(27, "Germany", 2026, population), null);
assert.equal(context.applyRelation(0, "Germany", 2022, population), 0);
assert.equal(context.formatRelationValue(0.00012345), "0.00012");

input.value = "pergdp";
const gdp = context.relationDisplay(meta);
assert.equal(gdp.unit, "count per 1 trillion USD GDP");
assert.equal(context.applyRelation(27, "Germany", 2022, gdp), 6.75);
assert.equal(context.applyRelation(27, "Germany", 2022, context.relationDisplay({ unit: "count" })), 27);
assert.equal(context.aggregateRelation([{ value: 2, relationWeight: 3 }, { value: 6, relationWeight: 1 }]), 3);
assert.equal(context.aggregateRelation([{ value: null, relationWeight: 1 }]), null);

// Exercise the two render steps that run during dashboard initialization.
const yearSelect = { value: "2022" };
const coverage = {};
context.document.getElementById = id => ({
  relationSelect: input,
  yearSelect,
  "kpi-chart": {},
  "data-coverage": coverage,
  country1Select: { value: "Germany" }
})[id];
Object.assign(context, {
  currentYearList: [2022],
  getMetaForCurrent: () => meta,
  getColorForCountry: () => "#000000",
  chartInstance: null,
  renderLineChart: (_, options) => options
});
for (const name of ["populateYearSelect", "updateChart"]) {
  const start = script.indexOf(`function ${name}(`);
  vm.runInContext(script.slice(start, script.indexOf("\n}", start) + 2), context);
}
context.populateYearSelect();
context.updateChart();
assert.match(yearSelect.innerHTML, /2022/);
assert.match(coverage.textContent, /2 countries/);
assert.equal(context.chartInstance.unit, gdp.unit);
assert.equal(context.chartInstance.datasets[0].data[0], 6.75);
