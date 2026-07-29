"use strict";

const assert = require("node:assert/strict");
const tabs = require("../scripts/page_germany_dossier.js");
const ids = ["germany-prosperity", "germany-2036", "germany-war-stress-test", "germany-reform-agenda"];

assert.equal(tabs.cleanHash("#germany-2036"), "germany-2036");
assert.equal(tabs.cleanHash("#income%2Dpyramid"), "income-pyramid");
assert.equal(tabs.resolvePanelId("#germany-2036", ids, ""), "germany-2036");
assert.equal(tabs.resolvePanelId("#scenario-method", ids, "germany-2036"), "germany-2036");
assert.equal(tabs.resolvePanelId("#unknown", ids, ""), "germany-prosperity");
assert.equal(tabs.nextTabIndex(0, "ArrowRight", 3), 1);
assert.equal(tabs.nextTabIndex(0, "ArrowLeft", 4), 3);
assert.equal(tabs.nextTabIndex(1, "Home", 3), 0);
assert.equal(tabs.nextTabIndex(1, "End", 4), 3);

console.log("Germany dossier tabs: all assertions passed");
