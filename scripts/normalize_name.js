/**
 * Vereinheitlichte Namensfunktion für KPI-Dateien (Frontend).
 * Diese Version ist 1:1 identisch mit normalize_name.py (Backend).
 * Sie sorgt dafür, dass Titel aus available_kpis.json exakt dieselben Dateinamen ergeben
 * wie die vom Backend erzeugten Dateien in /data/.
 */
window.normalizeName = function(title) {
  if (!title) return "unknown_kpi";

  let s = title.toLowerCase().trim();

  // Subskript-Zahlen vereinheitlichen
  const subDigits = { "₀":"0", "₁":"1", "₂":"2", "₃":"3", "₄":"4", "₅":"5", "₆":"6", "₇":"7", "₈":"8", "₉":"9" };
  s = s.replace(/[₀₁₂₃₄₅₆₇₈₉]/g, m => subDigits[m]);

  // CO₂ → co2
  s = s.replace("co₂", "co2");

  // "(% of gdp)" oder "percent of gdp" → "of gdp"
  s = s.replace(/\s*(%|percent)\s*of\s*gdp/, " of gdp");

  // Punkt zwischen Ziffern (2.5) → Unterstrich
  s = s.replace(/(?<=\d)\.(?=\d)/g, "_");

  // "1,000" oder "1.000" → "1_000"
  s = s.replace(/1[.,]000/g, "1_000");

  // Unnötige Zeichen entfernen
  s = s.replace(/[(),]/g, "");

  // Nicht alphanumerische Zeichen → Unterstrich
  s = s.replace(/[^a-z0-9._-]/g, "_");

  // Bindestriche → Unterstriche
  s = s.replace(/-/g, "_");

  // Doppelte Unterstriche reduzieren
  s = s.replace(/_+/g, "_");

  // Führende und abschließende Unterstriche entfernen
  s = s.replace(/^_+|_+$/g, "");

  return s;
};
