"use strict";

const assert = require("node:assert/strict");
const model = require("../scripts/page_germany_2036_scenarios.js");
const metricIds = ["prosperity", "income", "employment", "energy", "climate", "state"];
const bands = { prosperity:[99,108], income:[98,107], employment:[94,101], energy:[96,114], climate:[126,168], state:[94,105] };
const sliderBase = { climateStress:1, renewables:1, fragmentation:1, dependencies:0, technology:1, productivity:0, migration:0, investment:1 };
const scenario = { story:"A tested scenario narrative.", bands, scores:{prosperity:50}, sliderBase };
const data = {
  meta:{scenarioOrder:["pressure","renewal","loss"]}, metrics:metricIds.map(id => ({id})),
  scenarios:{ renewal:scenario, pressure:scenario, loss:scenario },
  influences:{
    climateStress:{prosperity:-1.2,income:-.8,employment:-.4,energy:1,climate:5,state:-1},
    renewables:{energy:-3}, fragmentation:{prosperity:-1.8}, dependencies:{prosperity:-1},
    technology:{prosperity:1.4}, productivity:{prosperity:1.8,income:1.3},
    migration:{employment:1.2}, investment:{state:1.5}
  },
  households:[{sensitivity:{income:1,employment:1,energy:1,climate:1,state:1}}]
};

assert.equal(model.validatePayload(data), true);
assert.equal(model.validatePayload(null), false);
assert.deepEqual(model.orderedBand(110, 90), [90, 110]);
assert.equal(model.clamp(7, -2, 2), 2);

for (const key of Object.keys(data.scenarios)) {
  const baseline = data.scenarios[key];
  const result = model.calculateModel(data, key, baseline.sliderBase);
  assert.deepEqual(result.bands, baseline.bands, `${key}: baseline must remain unchanged`);
  assert.deepEqual(model.calculateModel(data, key, baseline.sliderBase), result, `${key}: deterministic`);
  for (const band of Object.values(result.bands)) assert.ok(band[0] <= band[1], `${key}: ordered band`);
}

const base = data.scenarios.pressure.sliderBase;
const lowProductivity = model.calculateModel(data, "pressure", { ...base, productivity: -2 });
const highProductivity = model.calculateModel(data, "pressure", { ...base, productivity: 2 });
assert.ok(model.midpoint(highProductivity.bands.prosperity) > model.midpoint(lowProductivity.bands.prosperity));
assert.ok(model.midpoint(highProductivity.bands.income) > model.midpoint(lowProductivity.bands.income));

const lowClimate = model.calculateModel(data, "pressure", { ...base, climateStress: -2 });
const highClimate = model.calculateModel(data, "pressure", { ...base, climateStress: 2 });
assert.ok(model.midpoint(highClimate.bands.climate) > model.midpoint(lowClimate.bands.climate));

const start = model.interpolateBand([80, 120], 2026, 2026, 2036);
const end = model.interpolateBand([80, 120], 2036, 2026, 2036);
assert.deepEqual(start, [100, 100]);
assert.deepEqual(end, [80, 120]);

for (const household of data.households) {
  const outcome = model.householdOutcome(model.calculateModel(data, "pressure", base), household);
  assert.ok(outcome[0] <= outcome[1]);
  assert.ok(outcome[0] >= 50 && outcome[1] <= 150);
}

assert.equal(model.isCustom(base, base), false);
assert.equal(model.isCustom({ ...base, investment: -2 }, base), true);
console.log("Germany 2036 scenario logic: all assertions passed");
