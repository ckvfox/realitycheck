"use strict";

const assert = require("node:assert/strict");
const analysis = require("../scripts/page_real_wages_analysis.js");

const germany = 100;
assert.equal(analysis.classify(94.999, germany), "below");
assert.equal(analysis.classify(95, germany), "similar");
assert.equal(analysis.classify(105, germany), "similar");
assert.equal(analysis.classify(105.001, germany), "above");
assert.equal(analysis.classify(null, germany), "no-data");

const valid = {
  meta: { referenceYear: 2025 },
  trendMeta: { unit: "Reallohnindex (2025 = 100)" },
  germanySeries: [{ year: 2024, value: 100 }, { year: 2025, value: 110 }],
  comparison: { Germany: 110 }
};
assert.equal(analysis.validatePayload(valid), true);
assert.equal(analysis.validatePayload(null), false);
assert.equal(analysis.validatePayload({ ...valid, germanySeries: [] }), false);
assert.equal(analysis.validatePayload({ ...valid, comparison: {} }), false);

const stats = analysis.computeTrendStats(valid.germanySeries);
assert.equal(stats.full, 10);
assert.equal(stats.strongestRise.year, 2025);
assert.ok(Math.abs(analysis.annualizedChange(110, 100, 10) - 0.9577) < .001);
assert.deepEqual(analysis.summarizeWagePosition({ Germany: 100, A: 120, B: 90 }), { germany:100, count:3, higher:1, rank:2 });

const pppRows = Array.from({ length: 120 }, (_, index) => ({ country: `Country ${index}`, year: 2024, value: index + 1 }));
pppRows.push({ country: "Germany", year: 2024, value: 110 });
const ppp = analysis.summarizePppDistribution(pppRows);
assert.equal(ppp.year, 2024);
assert.equal(ppp.count, 121);
assert.equal(ppp.germany, 110);
assert.equal(ppp.rank, 11);
assert.equal(analysis.quantile([1, 2, 3], .5), 2);

console.log("real-wages JS logic: all assertions passed");
