'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const read = name => JSON.parse(fs.readFileSync(path.join(root, name), 'utf8'));
const script = fs.readFileSync(path.join(root, 'scripts/script_world.js'), 'utf8');
const { getWorldSeries, availableRegionYears, regionValuesForYear, regionCoverage } = require('../scripts/script_world.js');
const data = read('data/tropical_cyclone_activity_basin.json');
const geo = read('data/meta/regions_ocean_basins_geo.json');
const sets = read('data/meta/region_sets.json');
const metadata = read('data/meta/available_kpis.json');
const cyclone = metadata.find(k => k.filename === 'tropical_cyclone_activity_basin');

test('committed regional series are usable without inventing a global series', () => {
  assert.equal(data.length, 233);
  assert.deepEqual(getWorldSeries(data), { years: [], values: [] });
  assert.equal(availableRegionYears(data)[0], 2025);
  assert.equal(availableRegionYears(data).at(-1), 1980);
  for (const year of availableRegionYears(data)) {
    const values = regionValuesForYear(data, year);
    const coverage = regionCoverage(geo, 'Acronym', values);
    assert.equal(coverage.total, 7);
    assert.equal(coverage.unmapped.length, 0);
    assert.equal(values.has('NA'), false); // Known separate parsing defect; do not fix here.
    assert.equal(values.get('EP'), data.find(row => row.region === 'EP' && row.year === year).value);
  }
  assert.equal(regionValuesForYear(data, 1980).has('SA'), false);
  assert.equal(regionValuesForYear(data, 2004).has('SA'), true);
});

test('all seven geometries have closed valid rings; South Pacific remains split at dateline', () => {
  assert.deepEqual(geo.features.map(f => f.properties.Acronym).sort(), ['EP', 'NA', 'NI', 'SA', 'SI', 'SP', 'WP']);
  for (const feature of geo.features) {
    const polygons = feature.geometry.type === 'MultiPolygon' ? feature.geometry.coordinates : [feature.geometry.coordinates];
    for (const polygon of polygons) for (const ring of polygon) {
      assert.deepEqual(ring[0], ring.at(-1));
      for (const [lon, lat] of ring) {
        assert.ok(lon >= -180 && lon <= 180 && lat >= -90 && lat <= 90);
      }
      for (let i = 1; i < ring.length; i++) assert.ok(Math.abs(ring[i][0] - ring[i - 1][0]) <= 180);
    }
  }
  assert.equal(geo.features.find(f => f.properties.Acronym === 'SP').geometry.type, 'MultiPolygon');
  assert.match(geo.properties.note, /Not official/);
  for (const config of Object.values(sets)) {
    assert.equal(read('data/meta/' + config.geo_file).type, 'FeatureCollection');
  }
});

test('missing regional values are not zero; real zero and numeric strings remain valid', () => {
  const rows = [null, ...[null, '', ' ', undefined, NaN, Infinity].map(value => ({region: 'NA', year: 2025, value})),
    {region: 'EP', year: '2025', value: '0'}, {region: 'WP', year: null, value: 3}];
  assert.deepEqual(availableRegionYears(rows), [2025]);
  assert.deepEqual([...regionValuesForYear(rows, 2025)], [['EP', 0]]);
  for (const year of [null, '', ' ', undefined]) assert.equal(regionValuesForYear(rows, year).size, 0);
  assert.deepEqual(availableRegionYears({}), []);
  assert.equal(regionValuesForYear([], 2025).size, 0);
  assert.equal(regionCoverage(geo, 'Acronym', new Map([['UNKNOWN', 1]])).unmapped[0], 'UNKNOWN');
});

// Exercise the production renderer and selection handlers with a small DOM/Leaflet boundary.
function harness(loader = async url => url.endsWith('region_sets.json') ? sets : geo) {
  const elements = new Map();
  function element(tag = 'div') {
    const el = { tagName: tag.toUpperCase(), value: '', disabled: false, hidden: false, children: [],
      appendChild(child) { this.children.push(child); return child; },
      prepend(child) { this.children.unshift(child); },
      setAttribute(name) { if (name === 'hidden') this.hidden = true; },
      removeAttribute(name) { if (name === 'hidden') this.hidden = false; },
      toggleAttribute(name, force) { if (name === 'hidden') this.hidden = force; },
      querySelector() { return null; }, querySelectorAll() { return []; },
    };
    let text = '';
    Object.defineProperty(el, 'textContent', { get: () => text, set(v) { text = v; el.children = []; } });
    el.classList = { add() {}, remove() {} };
    return el;
  }
  const document = { createElement: element, getElementById(id) { if (!elements.has(id)) elements.set(id, element()); return elements.get(id); }, addEventListener() {} };
  const added = [];
  const context = vm.createContext({ document, URL, console, loadJSON: loader,
    loadKPIData: async () => data, renderKpiAnalysis() {},
    window: { location: { href: 'https://example.test/world.html' }, history: { replaceState() {} }, _worldGeoJSON: {} },
    L: { geoJSON(json, options) {
      const group = { features: [], resetStyle() {}, addTo() { added.push(this); return this; } };
      for (const feature of json.features) {
        const layer = { feature, style: options.style(feature), bindTooltip(content) { this.tooltip = content; }, on(events) { this.events = events; }, setStyle() {} };
        options.onEachFeature(feature, layer); group.features.push(layer);
      }
      return group;
    } },
  });
  vm.runInContext(script, context);
  context.testMeta = metadata;
  context.testData = data;
  vm.runInContext('META = testMeta; worldMapSelectedKpiMeta = META.find(k => k.filename === "tropical_cyclone_activity_basin"); worldMapSelectedKpiData = testData; worldMap = {removeLayer() {}};', context);
  document.getElementById('groupingSelect').value = 'climate';
  document.getElementById('categorySelect').value = 'storm_impact';
  document.getElementById('worldMapKpiSelect').value = cyclone.filename;
  document.getElementById('worldMapYearSelect').value = '2025';
  return { context, document, added, run: source => vm.runInContext(source, context) };
}

test('regional layer renders all basins with correct values, missing states and distinct source information', async () => {
  const h = harness();
  await h.run('renderWorldMapRegionLayer(getClimateCategoryConfig("storm_impact"), "storm_impact")');
  assert.equal(h.added[0].features.length, 7);
  const missing = h.added[0].features.find(layer => layer.feature.properties.Acronym === 'NA');
  assert.equal(missing.style.fillColor, '#e8edf2');
  assert.match(missing.tooltip.innerHTML, /No regional data for selected year/);
  const ep = h.added[0].features.find(layer => layer.feature.properties.Acronym === 'EP');
  assert.match(ep.tooltip.innerHTML, new RegExp(String(regionValuesForYear(data, 2025).get('EP'))));
  assert.match(ep.tooltip.innerHTML, /2025/);
  assert.match(ep.tooltip.innerHTML, /www.ncei.noaa.gov/);
  const legend = h.document.getElementById('legend-content');
  assert.match(legend.textContent, /Coverage: 5\/7/);
  assert.match(legend.children[0].textContent, /Not official/);
  assert.match(legend.children[1].textContent, /Measurement source/);
  assert.match(legend.children[2].textContent, /Geometry source/);
  assert.match(legend.children[2].textContent, /License:/);
  assert.match(h.document.getElementById('legend-other-label').textContent, /Region without/);
  assert.equal(h.document.getElementById('legend-group-a-item').hidden, true);
  h.run('updateWorldMapModeAvailability()');
  assert.equal(h.document.getElementById('worldMapAggregationMode').value, 'none');
  assert.equal(h.document.getElementById('worldMapAggregationMode').disabled, true);
});

test('placeholder clears stale year/data and never displays country fallback or a countries legend', async () => {
  const h = harness();
  h.document.getElementById('categorySelect').value = 'wildfire_impact';
  h.document.getElementById('worldMapKpiSelect').value = '';
  await h.run('updateWorldMapYearOptions()');
  h.run('updateWorldMapModeAvailability(); updateWorldMapGeoJSON()');
  assert.equal(h.document.getElementById('worldMapYearSelect').disabled, true);
  assert.equal(h.document.getElementById('worldMapYearSelect').children.length, 0);
  assert.equal(h.run('worldMapSelectedKpiData.length'), 0);
  assert.equal(h.added.length, 0);
  assert.equal(h.document.getElementById('world-map-visual-legend').hidden, true);
  assert.match(h.document.getElementById('world-map-mode-note').textContent, /not yet connected/);
});

test('late regional geometry cannot repaint after switching to a placeholder', async () => {
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  const h = harness(async url => { await gate; return url.endsWith('region_sets.json') ? sets : geo; });
  const pending = h.run('renderWorldMapRegionLayer(getClimateCategoryConfig("storm_impact"), "storm_impact")');
  h.document.getElementById('categorySelect').value = 'heat_impact';
  h.document.getElementById('worldMapKpiSelect').value = '';
  await h.run('updateWorldMapYearOptions()');
  h.run('updateWorldMapGeoJSON()');
  release(); await pending;
  assert.equal(h.added.length, 0);
});

test('regional chart card explains scope and keeps a map link and measurement source', async () => {
  const h = harness();
  h.context.container = h.document.createElement('section');
  h.run('ALL_DATA = {tropical_cyclone_activity_basin: testData}');
  await h.run('renderWorldKpi(container, worldMapSelectedKpiMeta)');
  const block = h.context.container.children[0];
  assert.match(block.children.find(el => el.className === 'kpi-message').textContent, /Regional data are available/);
  assert.ok(block.children.some(el => el.href?.includes('group=storm_impact')));
  assert.ok(block.children.some(el => el.className === 'chart-source'));
  assert.equal(block.children.some(el => el.tagName === 'CANVAS'), false);
});

test('year changes replace regional values and unsupported year stays missing', async () => {
  const h = harness();
  for (const year of ['1980', '2004', '2025', '1979', '']) {
    h.document.getElementById('worldMapYearSelect').value = year;
    await h.run('renderWorldMapRegionLayer(getClimateCategoryConfig("storm_impact"), "storm_impact")');
    const layers = h.added.at(-1).features;
    const expected = regionValuesForYear(data, year);
    for (const layer of layers) {
      const value = expected.get(layer.feature.properties.Acronym);
      if (!Number.isFinite(value)) assert.match(layer.tooltip.innerHTML, /No regional data/);
      else assert.match(layer.tooltip.innerHTML, new RegExp(String(value)));
    }
    if (year === '1979') assert.match(h.document.getElementById('world-map-mode-note').textContent, /No regional observations for 1979/);
  }
});

test('late KPI data cannot restore stale years after selecting an unconnected category', async () => {
  const h = harness();
  let release;
  h.context.loadKPIData = () => new Promise(resolve => { release = resolve; });
  const pending = h.run('updateWorldMapYearOptions()');
  h.document.getElementById('worldMapKpiSelect').value = '';
  await h.run('updateWorldMapYearOptions()');
  release(data); await pending;
  assert.equal(h.run('worldMapSelectedKpiData.length'), 0);
  assert.equal(h.document.getElementById('worldMapYearSelect').children.length, 0);
});

test('geometry loading failure is distinct from missing measurements', async () => {
  const h = harness(async () => { throw new Error('unavailable'); });
  await h.run('renderWorldMapRegionLayer(getClimateCategoryConfig("storm_impact"), "storm_impact")');
  assert.equal(h.added.length, 0);
  assert.match(h.document.getElementById('world-map-mode-note').textContent, /Data availability cannot be inferred/);
  assert.equal(h.run('worldMapSelectedKpiData.length'), 233);
});

test('tooltip text escapes dataset markup and existing global aliases retain their series', () => {
  const { escapeRegionText } = require('../scripts/script_world.js');
  assert.equal(escapeRegionText('<img onerror="x">'), '&lt;img onerror=&quot;x&quot;&gt;');
  assert.deepEqual(getWorldSeries([{ country: 'World', year: 2025, value: 3 }, { country: 'Welt', year: 2023, value: 1 }, { country: 'Global', year: 2024, value: 2 }, { region: 'EP', year: 2025, value: 90 }]), { years: [2023, 2024, 2025], values: [1, 2, 3] });
});
