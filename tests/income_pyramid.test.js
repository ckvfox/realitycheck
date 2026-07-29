"use strict";

const assert = require("node:assert/strict");
const income = require("../scripts/page_income_pyramid.js");

const bands = [
  { id:"farBelow", maxRatio:.5 }, { id:"below", minRatio:.5, maxRatio:.75 },
  { id:"around", minRatio:.75, maxRatio:1.1 }, { id:"above", minRatio:1.1 }
];
assert.equal(income.classifyHouseholdGross(49999, 100000, bands).id, "farBelow");
assert.equal(income.classifyHouseholdGross(50000, 100000, bands).id, "below");
assert.equal(income.classifyHouseholdGross(100000, 100000, bands).id, "around");
assert.equal(income.classifyHouseholdGross(110000, 100000, bands).id, "above");
assert.equal(income.classifyHouseholdGross(-1, 100000, bands), null);
assert.equal(income.relativeDifference(110, 100), 10);
assert.equal(income.validatePayload({meta:{},households:[1,2,3,4,5],benchmarkBands:[]}), true);
assert.equal(income.validatePayload({meta:{},households:[1,2,3,4,5,6],benchmarkBands:[]}), true);
console.log("income-pyramid logic: all assertions passed");
