/* Shared environmental map semantics; gray always means missing observations. */
function environmentalScale(meta, values = []) {
  if (!meta || (!/environment/i.test(meta.cluster || "") && !meta.map_color_direction)) return null;
  const direction = meta.map_color_direction || meta.sort;
  if (!["higher", "lower"].includes(direction)) return null;
  const sorted = values.filter(Number.isFinite).sort((a, b) => a - b);
  return {
    direction,
    fixed: meta.map_color_scale === "spei_drought",
    min: sorted[Math.floor((sorted.length - 1) * 0.05)] ?? 0,
    max: sorted[Math.ceil((sorted.length - 1) * 0.95)] ?? 0,
  };
}

function environmentalColor(scale, value) {
  if (!scale || !Number.isFinite(value)) return "#e6e6e6";
  let goodness;
  if (scale.fixed) {
    // SPEI: <= -2 is extremely dry; >= 0 has no negative moisture anomaly.
    // Green describes drought pressure only, never absence of flood risk.
    goodness = (value + 2) / 2;
  } else if (scale.max === scale.min) {
    goodness = value === 0 && scale.direction === "lower" ? 1 : 0.5;
  } else {
    const log = scale.min >= 0 && scale.max > 50 * Math.max(scale.min, 1);
    const transform = x => log ? Math.log1p(Math.max(0, x)) : x;
    const fraction = (transform(value) - transform(scale.min)) / (transform(scale.max) - transform(scale.min));
    goodness = scale.direction === "higher" ? fraction : 1 - fraction;
  }
  return `hsl(${120 * Math.max(0, Math.min(1, goodness))}, 75%, 42%)`;
}

function environmentalScaleNote(scale) {
  return scale?.fixed
    ? "Red: SPEI ≤ −2 (extremely dry); yellow: −1; green: ≥ 0 (no negative moisture anomaly). Drought pressure only, not flood safety. Gray = no observation."
    : "Red = higher pressure / worse outcome; green = lower pressure / better outcome within the displayed comparison (5th–95th percentile range). Colors are relative, not safety thresholds. Equal nonzero values use neutral yellow. Gray = no observation, not zero.";
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { environmentalScale, environmentalColor, environmentalScaleNote };
}
