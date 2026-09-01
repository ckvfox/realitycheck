"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const {
  calculateAdditiveShare,
  calculateMedianMetric,
  calculateGroupMetric,
  classifyGroupMembership,
  countryValuesForYear,
  formatCoverage,
  percentileIntensities,
} = require("../scripts/script_world.js");

test("group additive shares use real-country totals and report coverage", () => {
  const data = [
    { country: "A", year: 2023, value: 60 },
    { country: "B", year: 2023, value: 40 },
    { country: "C", year: 2023, value: 100 },
    { country: "World", year: 2023, value: 999 },
  ];
  const result = calculateAdditiveShare(data, ["A", "B"], 2024, new Set(["A", "B", "C"]));
  assert.equal(result.year, 2023);
  assert.equal(result.share, 0.5);
  assert.equal(result.covered, 2);
  assert.equal(result.total, 2);
});

test("comparison membership distinguishes both groups and their overlap", () => {
  const a = new Set(["France", "Germany"]);
  const b = new Set(["Germany", "United States"]);
  assert.equal(classifyGroupMembership("France", a, b), "a");
  assert.equal(classifyGroupMembership("United States", a, b), "b");
  assert.equal(classifyGroupMembership("Germany", a, b), "overlap");
  assert.equal(classifyGroupMembership("Japan", a, b), "other");
});

test("group metric supports absolute sums and per-capita medians", () => {
  const values = [
    { country: "A", year: 2024, value: 100 },
    { country: "B", year: 2024, value: 600 },
  ];
  const population = [
    { country: "A", year: 2024, value: 10 },
    { country: "B", year: 2024, value: 20 },
  ];
  assert.equal(calculateGroupMetric(values, ["A", "B"], 2024, { aggregation: "sum" }).value, 700);
  assert.deepEqual(calculateGroupMetric(values, ["A", "B"], 2024, {
    aggregation: "median", valueMode: "per_capita", populationData: population,
  }), { value: 20, covered: 2, total: 2 });
});

test("group metric supports mean and max aggregations", () => {
  const values = [
    { country: "A", year: 2024, value: 2 },
    { country: "B", year: 2024, value: 8 },
    { country: "C", year: 2024, value: 20 },
  ];
  assert.equal(calculateGroupMetric(values, ["A", "B", "C"], 2024, { aggregation: "mean" }).value, 10);
  assert.equal(calculateGroupMetric(values, ["A", "B", "C"], 2024, { aggregation: "max" }).value, 20);
});

test("group metric supports population and area weighted means", () => {
  const values = [
    { country: "A", year: 2024, value: 2 },
    { country: "B", year: 2024, value: 8 },
  ];
  const population = [
    { country: "A", year: 2024, value: 1 },
    { country: "B", year: 2024, value: 3 },
  ];
  const area = [
    { country: "A", year: 2024, value: 2 },
    { country: "B", year: 2024, value: 1 },
  ];
  const popWeighted = calculateGroupMetric(values, ["A", "B"], 2024, {
    aggregation: "population_weighted_mean",
    populationData: population,
    areaData: area,
  });
  const areaWeighted = calculateGroupMetric(values, ["A", "B"], 2024, {
    aggregation: "area_weighted_mean",
    populationData: population,
    areaData: area,
  });
  assert.equal(popWeighted.value, 6.5);
  assert.equal(areaWeighted.value, 4);
});

test("choropleth percentile intensity is stable for ties", () => {
  const intensities = percentileIntensities(new Map([["A", 1], ["B", 3], ["C", 3]]));
  assert.equal(intensities.get("A"), 0);
  assert.equal(intensities.get("B"), 0.75);
  assert.equal(intensities.get("C"), 0.75);
});

test("selected KPI summary uses an unweighted country median", () => {
  const data = [
    { country: "A", year: 2024, value: 1 },
    { country: "B", year: 2024, value: 3 },
    { country: "C", year: 2024, value: 100 },
  ];
  assert.deepEqual(calculateMedianMetric(data, ["A", "B"], 2024), {
    value: 2,
    covered: 2,
    total: 2,
  });
  assert.equal(formatCoverage(2, 4), "2/4 countries (50%)");
  assert.equal(countryValuesForYear(data, 2024, new Set(["A", "B"])).size, 2);
});
