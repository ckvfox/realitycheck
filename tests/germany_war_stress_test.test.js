"use strict";

const assert = require("node:assert/strict");
const moduleApi = require("../scripts/page_germany_war_stress_test.js");

const payload = {
  meta:{}, evidenceTypes:{extreme:{label:"Extreme",class:"extreme"}},
  phases:Array.from({length:7}, (_, index) => ({id:index + 1})),
  hours72:[{}], households:[{}], objections:[{}],
  people:{models:[{}],serviceDebate:{models:[{}]},refusalParadox:{}}, strategicDoctrine:{headline:"Defence"},
  conscriptionMap:{democratic:["Finland"],nonDemocratic:["Russia"],noInformation:["W. Sahara"],countryNotes:{}},
  preventionMeasures:[{category:"Military",items:[]}], sources:[{id:"nato",title:"NATO"}]
};

assert.equal(moduleApi.validatePayload(payload), true);
assert.equal(moduleApi.validatePayload({...payload, phases:payload.phases.slice(0,6)}), false);
assert.equal(moduleApi.validatePayload({...payload, people:null}), false);
assert.deepEqual(moduleApi.sourceIndex(payload), {nato:payload.sources[0]});
assert.equal(moduleApi.conscriptionCategory(payload.conscriptionMap, "Finland"), "democratic");
assert.equal(moduleApi.conscriptionCategory(payload.conscriptionMap, "Russia"), "non-democratic");
assert.equal(moduleApi.conscriptionCategory(payload.conscriptionMap, "Germany"), "none");
assert.equal(moduleApi.conscriptionCategory(payload.conscriptionMap, "W. Sahara"), "no-info");

console.log("Germany war stress-test JS logic: all assertions passed");
