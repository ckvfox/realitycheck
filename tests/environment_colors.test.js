const test = require('node:test');
const assert = require('node:assert/strict');
const {environmentalScale, environmentalColor, environmentalScaleNote} = require('../scripts/environment_colors.js');
const meta = {cluster: 'Environment & Sustainability', sort: 'lower'};
test('lower environmental burdens are green and higher burdens red', () => {
  const scale = environmentalScale(meta, [0, 50, 100]);
  assert.equal(environmentalColor(scale, 0), 'hsl(120, 75%, 42%)');
  assert.equal(environmentalColor(scale, 100), 'hsl(0, 75%, 42%)');
  assert.equal(environmentalColor(scale, null), '#e6e6e6');
  assert.equal(environmentalColor(scale, NaN), '#e6e6e6');
});
test('positive environmental outcomes reverse the direction; other metrics remain unclassified', () => {
  const scale = environmentalScale({...meta, sort:'higher'}, [0,100]);
  assert.equal(environmentalColor(scale, 100), 'hsl(120, 75%, 42%)');
  assert.equal(environmentalColor(scale, 0), 'hsl(0, 75%, 42%)');
  assert.equal(environmentalScale({cluster:'Economy', sort:'higher'}, [0,100]), null);
  assert.equal(environmentalScale({cluster:'Infrastructure',sort:'higher',map_color_direction:'higher'}, [0,100]).direction,'higher');
  assert.equal(environmentalScale({...meta, sort:'target'}, [0,100]), null);
});
test('SPEI has stable drought thresholds independent of selected countries', () => {
  const scale = environmentalScale({...meta,sort:'higher',map_color_scale:'spei_drought'}, [-4,-3]);
  assert.equal(environmentalColor(scale, -3), 'hsl(0, 75%, 42%)');
  assert.equal(environmentalColor(scale, -1), 'hsl(60, 75%, 42%)');
  assert.equal(environmentalColor(scale, 0), 'hsl(120, 75%, 42%)');
  assert.equal(environmentalColor(scale, 2), 'hsl(120, 75%, 42%)');
  assert.match(environmentalScaleNote(scale), /not flood safety/);
});
test('ties and negative anomalies stay finite and do not imply safety', () => {
  const tied = environmentalScale(meta, [10,10]);
  assert.equal(environmentalColor(tied, 10), 'hsl(60, 75%, 42%)');
  assert.equal(environmentalColor(environmentalScale(meta,[0,0]),0),'hsl(120, 75%, 42%)');
  const signed = environmentalScale(meta, [-2,0,2]);
  assert.equal(environmentalColor(signed, 0),'hsl(60, 75%, 42%)');
  assert.match(environmentalScaleNote(signed), /not safety thresholds/);
});
