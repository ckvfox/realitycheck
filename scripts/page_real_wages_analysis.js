(function (root, factory) {
  // Analysis UI version 1.1: annual changes and global PPP context.
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.RCRealWages = api;
})(typeof window !== "undefined" ? window : null, function () {
  "use strict";
  function isGerman() { return typeof document !== "undefined" && document.documentElement.lang === "de"; }
  function ui(en, de) { return isGerman() ? de : en; }

  function classify(value, germanyValue) {
    if (!Number.isFinite(value) || !Number.isFinite(germanyValue) || germanyValue <= 0) return "no-data";
    if (value < germanyValue * 0.95) return "below";
    if (value > germanyValue * 1.05) return "above";
    return "similar";
  }

  function percentChange(current, previous) {
    if (!Number.isFinite(current) || !Number.isFinite(previous) || previous === 0) return null;
    return ((current - previous) / previous) * 100;
  }

  function validatePayload(payload) {
    if (!payload || typeof payload !== "object") return false;
    if (!payload.meta || !payload.trendMeta || !Array.isArray(payload.germanySeries) || !payload.comparison) return false;
    if (!payload.germanySeries.length || typeof payload.comparison !== "object") return false;
    if (!Number.isFinite(Number(payload.comparison.Germany))) return false;
    return payload.germanySeries.every(item => Number.isInteger(item.year) && Number.isFinite(item.value));
  }

  function computeTrendStats(series) {
    const ordered = [...series].sort((a, b) => a.year - b.year);
    const first = ordered[0];
    const last = ordered[ordered.length - 1];
    const findAtOrBefore = target => [...ordered].reverse().find(item => item.year <= target) || null;
    const changes = ordered.slice(1).map((item, index) => ({
      year: item.year,
      change: percentChange(item.value, ordered[index].value)
    }));
    return {
      first,
      last,
      full: percentChange(last.value, first.value),
      five: percentChange(last.value, findAtOrBefore(last.year - 5)?.value),
      ten: percentChange(last.value, findAtOrBefore(last.year - 10)?.value),
      strongestRise: changes.reduce((best, item) => !best || item.change > best.change ? item : best, null),
      strongestDrop: changes.reduce((best, item) => !best || item.change < best.change ? item : best, null)
    };
  }

  function annualizedChange(current, previous, years) {
    if (!Number.isFinite(current) || !Number.isFinite(previous) || previous <= 0 || !Number.isFinite(years) || years <= 0) return null;
    return (Math.pow(current / previous, 1 / years) - 1) * 100;
  }

  function summarizeWagePosition(comparison) {
    if (!comparison || typeof comparison !== "object") return null;
    const germany = Number(comparison.Germany);
    const values = Object.values(comparison).map(Number).filter(Number.isFinite);
    if (!Number.isFinite(germany) || !values.length) return null;
    const higher = values.filter(value => value > germany).length;
    return { germany, count: values.length, higher, rank: higher + 1 };
  }

  function quantile(sortedValues, share) {
    if (!sortedValues.length) return null;
    const index = (sortedValues.length - 1) * share;
    const lower = Math.floor(index);
    const upper = Math.ceil(index);
    if (lower === upper) return sortedValues[lower];
    return sortedValues[lower] + (sortedValues[upper] - sortedValues[lower]) * (index - lower);
  }

  function summarizePppDistribution(rows) {
    if (!Array.isArray(rows)) return null;
    const germanyYears = rows.filter(row => row.country === "Germany" && Number.isFinite(Number(row.value))).map(row => Number(row.year));
    const years = [...new Set(germanyYears)].sort((a, b) => b - a);
    for (const year of years) {
      const current = rows.filter(row => Number(row.year) === year && Number.isFinite(Number(row.value)) && Number(row.value) > 0);
      if (current.length < 100) continue;
      const germany = current.find(row => row.country === "Germany");
      if (!germany) continue;
      const ascending = current.map(row => Number(row.value)).sort((a, b) => a - b);
      const rank = 1 + current.filter(row => Number(row.value) > Number(germany.value)).length;
      return {
        year, count: current.length, germany: Number(germany.value), rank,
        median: quantile(ascending, .5), p75: quantile(ascending, .75), p90: quantile(ascending, .9),
        topShare: rank / current.length * 100
      };
    }
    return null;
  }

  function formatMoney(value, meta) {
    return `${Math.round(value).toLocaleString("de-DE")} ${meta.priceBase}-USD (PPP)`;
  }

  function formatIndex(value) {
    return `${Number(value).toLocaleString(isGerman() ? "de-DE" : "en-GB", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} ${ui("index points", "Indexpunkte")}`;
  }

  function formatPercent(value, signed = true) {
    if (!Number.isFinite(value)) return "–";
    const prefix = signed && value > 0 ? "+" : "";
    return `${prefix}${value.toLocaleString("de-DE", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} %`;
  }

  function setText(id, text) {
    const element = document.getElementById(id);
    if (element) element.textContent = text;
    return element;
  }

  function addStat(container, label, value) {
    const card = document.createElement("div");
    card.className = "real-wages-stat";
    const number = document.createElement("strong");
    number.textContent = value;
    const caption = document.createElement("span");
    caption.textContent = label;
    card.append(number, caption);
    container.appendChild(card);
  }

  function renderTrend(payload) {
    const series = [...payload.germanySeries].sort((a, b) => a.year - b.year);
    const stats = computeTrendStats(series);
    setText("trend-period", `${stats.first.year}–${stats.last.year} · ${ui("source updated", "Quelle aktualisiert")} ${payload.trendMeta.sourceUpdatedAt}`);

    const statsNode = document.getElementById("trend-stats");
    statsNode.replaceChildren();
    addStat(statsNode, `${stats.first.year} to ${stats.last.year}`, formatPercent(stats.full));
    addStat(statsNode, ui("last five years", "letzte fünf Jahre"), formatPercent(stats.five));
    addStat(statsNode, ui("last ten years", "letzte zehn Jahre"), formatPercent(stats.ten));
    addStat(statsNode, `${ui("strongest rise", "stärkster Anstieg")} (${stats.strongestRise.year})`, formatPercent(stats.strongestRise.change));
    addStat(statsNode, `${ui("strongest fall", "stärkster Rückgang")} (${stats.strongestDrop.year})`, formatPercent(stats.strongestDrop.change));

    const prePandemic = series.find(item => item.year === 2019) || null;
    const since2019 = prePandemic ? percentChange(stats.last.value, prePandemic.value) : null;
    setText("trend-summary", isGerman()
      ? `Der langfristige Zuwachs von ${formatPercent(stats.full)} entstand vor allem vor 2019. Im Jahr ${stats.last.year} liegt der Index ${Number.isFinite(since2019) ? `${formatPercent(Math.abs(since2019), false)} ${since2019 >= 0 ? "über" : "unter"}` : "nahe"} dem Niveau von 2019. Die jüngsten Gewinne sind daher zu einem großen Teil Erholung nach dem Einbruch von 2022 und noch kein starker neuer Wachstumstrend.`
      : `The long-term increase of ${formatPercent(stats.full)} was built mainly before 2019. In ${stats.last.year}, the index is ${Number.isFinite(since2019) ? `${formatPercent(Math.abs(since2019), false)} ${since2019 >= 0 ? "above" : "below"}` : "close to"} its 2019 level. Recent gains are therefore largely a recovery from the 2022 fall, not yet a strong new growth trend.`);

    const wagePosition = summarizeWagePosition(payload.comparison);
    const elapsedYears = stats.last.year - stats.first.year;
    const annualized = annualizedChange(stats.last.value, stats.first.value, elapsedYears);
    setText("trend-interpretation-title", ui(
      "High international wage level, but little real progress since 2019",
      "Hohes internationales Lohnniveau, aber seit 2019 kaum realer Fortschritt"
    ));
    setText("trend-interpretation-lead", wagePosition ? (isGerman()
      ? `Deutschland liegt beim kaufkraftbereinigten durchschnittlichen OECD-Jahreslohn auf Rang ${wagePosition.rank} von ${wagePosition.count} Ländern. Nur ${wagePosition.higher} Vergleichsländer melden einen höheren Durchschnitt. Das Ausgangsniveau ist damit weiterhin hoch.`
      : `Germany ranks ${wagePosition.rank} of ${wagePosition.count} countries for the purchasing-power-adjusted average OECD annual wage. Only ${wagePosition.higher} comparison countries report a higher average. The starting level therefore remains high.`) : "");
    const interpretationPoints = document.getElementById("trend-interpretation-points");
    if (interpretationPoints) {
      const points = isGerman() ? [
        `Langfristig stieg die durchschnittliche reale Lohnkaufkraft seit ${stats.first.year} um ${formatPercent(stats.full)}. Auf ${elapsedYears} Jahre verteilt entspricht das aber nur rund ${formatPercent(annualized, false)} pro Jahr.`,
        `Kurzfristig dominiert Stillstand: Über die letzten fünf Jahre beträgt der gesamte Zuwachs nur ${formatPercent(stats.five)}. Der Stand von ${stats.last.year} liegt sogar leicht unter 2019.`,
        `Der Durchschnitt beschreibt nicht den typischen Haushalt. Medianlohn, Steuern, Arbeitszeit, Wohnkosten und Verteilung können dazu führen, dass einzelne Gruppen die Lage deutlich schlechter oder besser erleben.`
      ] : [
        `Over the long term, average real wage purchasing power rose by ${formatPercent(stats.full)} since ${stats.first.year}. Spread over ${elapsedYears} years, however, this is only about ${formatPercent(annualized, false)} per year.`,
        `The recent picture is close to stagnation: the total gain over five years is only ${formatPercent(stats.five)}. The ${stats.last.year} level is even slightly below 2019.`,
        `The average does not describe the typical household. Median wages, taxes, hours worked, housing costs and distribution can make individual groups experience a much weaker or stronger position.`
      ];
      interpretationPoints.replaceChildren(...points.map(text => {
        const item = document.createElement("li");
        item.textContent = text;
        return item;
      }));
    }
    setText("trend-interpretation-conclusion", isGerman()
      ? `Kurz gesagt: Im internationalen Durchschnitt ist die deutsche Debatte teilweise „Jammern auf hohem Niveau“. Die Unzufriedenheit über stagnierende Kaufkraft ist trotzdem sachlich begründet. Hohes Niveau und schwache Dynamik können gleichzeitig wahr sein.`
      : `In short: at the national average, Germany is partly complaining from a high base. Frustration about stagnant purchasing power is nevertheless supported by the data. A high level and weak momentum can both be true.`);
    setText("trend-method-note", payload.trendMeta.methodBreakNote);

    const source = document.getElementById("trend-source");
    source.href = payload.trendMeta.sourceUrl;
    source.textContent = payload.trendMeta.sourceName;

    const canvas = document.getElementById("real-wages-chart");
    if (typeof Chart === "undefined" || !canvas) throw new Error("Chart.js is unavailable.");
    const chart = new Chart(canvas.getContext("2d"), {
      type: "line",
      data: {
        labels: series.map(item => item.year),
        datasets: [{
          label: ui("Germany", "Deutschland"),
          data: series.map(item => item.value),
          borderColor: "#1a355e",
          backgroundColor: "rgba(26, 53, 94, 0.12)",
          pointBackgroundColor: "#1a355e",
          pointRadius: 2.5,
          pointHoverRadius: 5,
          borderWidth: 3,
          tension: 0.15,
          fill: true,
          spanGaps: false,
          yAxisID: "y",
          order: 1
        }, {
          type: "bar",
          label: ui("Change from previous year", "Veränderung zum Vorjahr"),
          data: series.map((item, index) => index === 0 ? null : percentChange(item.value, series[index - 1].value)),
          backgroundColor: series.map((item, index) => index === 0 || item.value >= series[index - 1].value ? "rgba(39, 134, 74, .42)" : "rgba(182, 56, 56, .5)"),
          borderColor: series.map((item, index) => index === 0 || item.value >= series[index - 1].value ? "#27864a" : "#b63838"),
          borderWidth: 1,
          yAxisID: "yChange",
          order: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { display: true },
          tooltip: {
            callbacks: {
              title: items => `Jahr ${items[0].label}`,
              label: context => context.dataset.yAxisID === "yChange"
                ? `${context.dataset.label}: ${formatPercent(context.parsed.y)}`
                : `${context.dataset.label}: ${formatIndex(context.parsed.y)}`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: payload.trendMeta.unit },
            ticks: { callback: value => Number(value).toLocaleString("de-DE") }
          },
          yChange: {
            position: "right",
            grid: { drawOnChartArea: false },
            title: { display: true, text: ui("Change from previous year (%)", "Veränderung zum Vorjahr (%)") },
            ticks: { callback: value => `${value} %` }
          },
          x: { title: { display: true, text: ui("Year", "Jahr") } }
        }
      }
    });
    return chart;
  }

  async function renderPppContext() {
    const rows = await window.loadJSON("data/purchasing_power_parity.json");
    const summary = summarizePppDistribution(rows);
    if (!summary) throw new Error(ui("The global PPP context could not be calculated.", "Der globale Kaufkraftvergleich konnte nicht berechnet werden."));
    setText("ppp-period", `${summary.year} · ${summary.count} ${ui("countries", "Länder")}`);
    const statsNode = document.getElementById("ppp-stats");
    statsNode.replaceChildren();
    const countriesAbove = summary.rank - 1;
    const topGroup = Math.ceil(summary.topShare);
    addStat(statsNode, ui("country rank by GDP per head", "Länderrang nach BIP je Einwohner"), `${summary.rank} ${ui("of", "von")} ${summary.count}`);
    addStat(statsNode, ui("countries with a higher value", "Länder mit höherem Wert"), `${countriesAbove}`);
    addStat(statsNode, ui("Germany among covered countries", "Deutschland unter den erfassten Ländern"), isGerman() ? `oberste ${topGroup} %` : `highest ${topGroup}%`);
    addStat(statsNode, ui("Germany", "Deutschland"), `${Math.round(summary.germany).toLocaleString(isGerman() ? "de-DE" : "en-GB")} int. $`);
    addStat(statsNode, ui("global median", "Median der Länder"), `${Math.round(summary.median).toLocaleString(isGerman() ? "de-DE" : "en-GB")} int. $`);
    setText("ppp-summary", isGerman()
      ? `Deutschland liegt auf Rang ${summary.rank} von ${summary.count} erfassten Ländern. ${countriesAbove} Länder melden ein höheres kaufkraftbereinigtes BIP je Einwohner. „Oberste ${topGroup} %“ bezieht sich nur auf die Länder in diesem Datensatz, nicht auf Menschen oder Haushaltseinkommen. Deutschlands Wert ist etwa ${(summary.germany / summary.median).toLocaleString("de-DE", { maximumFractionDigits: 1 })}-mal so hoch wie der Ländermedian. Das ist ein hohes wirtschaftliches Ausgangsniveau, sagt aber nichts über die Verteilung des Wohlstands oder die Kaufkraft eines einzelnen Haushalts.`
      : `Germany ranks ${summary.rank}th of ${summary.count} covered countries: ${countriesAbove} countries report a higher GDP per person in purchasing-power parity. “Highest ${topGroup}%” refers only to countries in this dataset, not to people or household incomes. Germany's value is about ${(summary.germany / summary.median).toLocaleString("en-GB", { maximumFractionDigits: 1 })} times the country median — a high economic starting level, but no measure of how prosperity is distributed or what an individual household can afford.`);
    setText("ppp-status", "");
    const canvas = document.getElementById("ppp-context-chart");
    return new Chart(canvas.getContext("2d"), {
      type: "bar",
      data: {
        labels: isGerman() ? ["Median der Länder", "Grenze: oberste 25 %", "Deutschland", "Grenze: oberste 10 %"] : ["Median country", "Threshold: highest 25%", "Germany", "Threshold: highest 10%"],
        datasets: [{
          label: `GDP per capita, PPP (${summary.year})`,
          data: [summary.median, summary.p75, summary.germany, summary.p90],
          backgroundColor: ["#9ca3af", "#6f8eae", "#1a355e", "#27864a"]
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `${Math.round(ctx.parsed.y).toLocaleString("en-GB")} current international dollars (PPP)` } } },
        scales: { y: { beginAtZero: true, title: { display: true, text: "current international dollars (PPP)" }, ticks: { callback: value => Number(value).toLocaleString("en-GB") } } }
      }
    });
  }

  function popupContent(country, value, germanyValue, category, payload) {
    const labels = isGerman()
      ? { below:"mehr als 5 % unter Deutschland", similar:"innerhalb von ±5 %", above:"mehr als 5 % über Deutschland", "no-data":"Keine Daten" }
      : { below: "more than 5% below Germany", similar: "within ±5%", above: "more than 5% above Germany", "no-data": "No data" };
    const wrapper = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = country;
    wrapper.appendChild(title);
    const lines = value == null
      ? [ui("No comparable data for the reference year.", "Keine vergleichbaren Daten für das Bezugsjahr."), `${ui("Data year", "Datenjahr")}: ${payload.meta.referenceYear}`, `${ui("Category", "Kategorie")}: ${labels[category]}`]
      : [
          `${ui("Country value", "Länderwert")}: ${formatMoney(value, payload.meta)}`,
          `${ui("Germany", "Deutschland")}: ${formatMoney(germanyValue, payload.meta)}`,
          `${ui("Difference from Germany", "Abweichung von Deutschland")}: ${formatPercent(percentChange(value, germanyValue))}`,
          `${ui("Data year", "Datenjahr")}: ${payload.meta.referenceYear}`,
          `${ui("Category", "Kategorie")}: ${labels[category]}`
        ];
    lines.forEach(line => {
      const paragraph = document.createElement("p");
      paragraph.textContent = line;
      wrapper.appendChild(paragraph);
    });
    const link = document.createElement("a");
    link.href = payload.meta.sourceUrl;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = payload.meta.sourceName;
    wrapper.appendChild(link);
    return wrapper;
  }

  function addLegend(map, payload) {
    const colors = { below: "#c43d3d", similar: "#e3b341", above: "#27864a", "no-data": "#9ca3af" };
    const items = [
      ["below", ui("Average wage < 95% of Germany", "Durchschnittslohn < 95 % von Deutschland")],
      ["similar", ui("Average wage 95% to 105%", "Durchschnittslohn 95 % bis 105 %")],
      ["above", ui("Average wage > 105% of Germany", "Durchschnittslohn > 105 % von Deutschland")],
      ["no-data", ui("No comparable data", "Keine vergleichbaren Daten")]
    ];
    const control = L.control({ position: "bottomright" });
    control.onAdd = function () {
      const box = L.DomUtil.create("div", "real-wages-map-legend");
      const heading = document.createElement("strong");
      heading.textContent = ui(`Average annual wage · ${payload.meta.referenceYear}`, `Durchschnittlicher Jahreslohn · ${payload.meta.referenceYear}`);
      box.appendChild(heading);
      const unit = document.createElement("small");
      unit.textContent = ui(`${payload.meta.priceBase} USD, purchasing-power adjusted`, `${payload.meta.priceBase}-USD, kaufkraftbereinigt`);
      box.appendChild(unit);
      items.forEach(([key, label]) => {
        const row = document.createElement("div");
        const swatch = document.createElement("span");
        swatch.className = `real-wages-swatch real-wages-swatch--${key}`;
        swatch.style.backgroundColor = colors[key];
        const text = document.createElement("span");
        text.textContent = label;
        row.append(swatch, text);
        box.appendChild(row);
      });
      return box;
    };
    control.addTo(map);
  }

  async function renderMap(payload) {
    if (typeof L === "undefined" || !window.RCMap || typeof window.loadJSON !== "function") {
      throw new Error("Leaflet or the shared map library is unavailable.");
    }
    const [geoJson, mappings] = await Promise.all([
      window.RCMap.loadGeoJSON(),
      window.loadJSON("data/meta/country_mappings.json")
    ]);
    if (!geoJson || !Array.isArray(geoJson.features) || !mappings || typeof mappings !== "object") {
      throw new Error("Country geometries or mappings could not be loaded.");
    }

    const map = window.RCMap.createMap("real-wages-map", { center: [20, 8], zoom: 2, minZoom: 1, maxZoom: 6 });
    const germanyValue = Number(payload.comparison.Germany);
    if (!Number.isFinite(germanyValue)) throw new Error("Germany's value is missing for the reference year.");
    setText("map-comparison-baseline", isGerman()
      ? `Deutschland ist mit ${formatMoney(germanyValue, payload.meta)} der 100-Prozent-Bezug. Jede Farbe zeigt die Abweichung des jeweiligen Landesdurchschnitts.`
      : `Germany is the 100% reference at ${formatMoney(germanyValue, payload.meta)}. Each colour shows the difference of the respective country average.`);
    const colors = { below: "#c43d3d", similar: "#e3b341", above: "#27864a", "no-data": "#9ca3af" };
    const featureCountries = new Set();

    window.RCMap.addGeoJSONLayer(
      map,
      geoJson,
      feature => {
        const raw = window.RCMap.getCountryName(feature) || "Unbekannt";
        const country = mappings[raw] || raw;
        const numeric = Number(payload.comparison[country]);
        const value = Number.isFinite(numeric) ? numeric : null;
        const category = classify(value, germanyValue);
        return {
          fillColor: colors[category],
          fillOpacity: category === "no-data" ? 0.45 : 0.72,
          color: country === "Germany" ? "#071d3b" : "#ffffff",
          weight: country === "Germany" ? 3.5 : 0.8,
          opacity: 1,
          dashArray: category === "no-data" ? "4 3" : null
        };
      },
      (feature, layer) => {
        const raw = window.RCMap.getCountryName(feature) || "Unbekannt";
        const country = mappings[raw] || raw;
        featureCountries.add(country);
        const numeric = Number(payload.comparison[country]);
        const value = Number.isFinite(numeric) ? numeric : null;
        const category = classify(value, germanyValue);
        layer.bindTooltip(country, { sticky: true });
        layer.bindPopup(() => popupContent(country, value, germanyValue, category, payload));
      }
    );
    addLegend(map, payload);

    const counts = { below: 0, similar: 0, above: 0 };
    Object.values(payload.comparison).forEach(rawValue => {
      const category = classify(Number(rawValue), germanyValue);
      if (counts[category] !== undefined) counts[category] += 1;
    });
    const comparable = Object.keys(payload.comparison).length;
    const noData = [...featureCountries].filter(country => !Number.isFinite(Number(payload.comparison[country]))).length;
    const statsNode = document.getElementById("map-stats");
    statsNode.replaceChildren();
    addStat(statsNode, ui("comparable national wage averages", "vergleichbare nationale Lohndurchschnitte"), String(comparable));
    addStat(statsNode, ui("average wage >5% below Germany", "Durchschnittslohn >5 % unter Deutschland"), `${counts.below} (${formatPercent(counts.below / comparable * 100, false)})`);
    addStat(statsNode, ui("average wage within ±5%", "Durchschnittslohn innerhalb ±5 %"), `${counts.similar} (${formatPercent(counts.similar / comparable * 100, false)})`);
    addStat(statsNode, ui("average wage >5% above Germany", "Durchschnittslohn >5 % über Deutschland"), `${counts.above} (${formatPercent(counts.above / comparable * 100, false)})`);
    addStat(statsNode, ui("map countries outside the OECD wage dataset", "Kartenländer außerhalb der OECD-Lohnreihe"), String(noData));
    setText(
      "map-summary",
      isGerman() ? `Beim durchschnittlichen kaufkraftbereinigten Jahreslohn liegen ${counts.below} von ${comparable} vergleichbaren Landeswerten mehr als 5 % unter dem deutschen Durchschnitt. ${counts.similar} liegen innerhalb von ±5 %, ${counts.above} mehr als 5 % darüber.` : `For the average purchasing-power-adjusted annual wage, ${counts.below} of ${comparable} comparable country averages are more than 5% below Germany's average, ${counts.similar} are within ±5%, and ${counts.above} are more than 5% above.`
    );
    setText("map-coverage-note", isGerman() ? `Warum nur ${comparable} Länder? Die OECD-Reihe umfasst vor allem OECD-Volkswirtschaften. Dieser strenge Vergleich nutzt nur Länder mit einem Wert im selben Bezugsjahr (${payload.meta.referenceYear}) und derselben konstanten Kaufkrafteinheit. In anderen Jahren enthält die Quelle bis zu ${payload.meta.peakCountryCount} Länder. Der Weltbank-Indikator darüber liefert deshalb den breiteren globalen Kontext.` : `Why only ${comparable} countries? The OECD series mainly covers OECD economies. This strict comparison includes only countries with a value in the same reference year (${payload.meta.referenceYear}) and the same constant-PPP unit; the source contains up to ${payload.meta.peakCountryCount} countries in other years. The World Bank PPP indicator above therefore supplies the broader global context.`);
    setText("real-wages-status", "");
    return map;
  }

  async function boot() {
    const status = document.getElementById("real-wages-status");
    try {
      const dataNode = document.getElementById("real-wages-data");
      const payload = dataNode ? JSON.parse(dataNode.textContent) : null;
      if (!validatePayload(payload)) throw new Error("Analysis data is empty or invalid.");
      setText("map-period", `${payload.meta.referenceYear} · ${payload.meta.countryCount} ${ui("countries with data", "Länder mit Daten")}`);
      const mapSource = document.getElementById("map-source");
      mapSource.href = payload.meta.sourceUrl;
      mapSource.textContent = payload.meta.sourceName;
      const chart = renderTrend(payload);
      const [map, pppChart] = await Promise.all([renderMap(payload), renderPppContext()]);
      window.addEventListener("resize", () => {
        chart.resize();
        pppChart.resize();
        map.invalidateSize();
      }, { passive: true });
    } catch (error) {
      if (status) status.textContent = `Fehler: ${error.message}`;
      console.error("RealityCheck real-wage analysis:", error);
    }
  }

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
    else boot();
  }

  return { classify, percentChange, validatePayload, computeTrendStats, annualizedChange, summarizeWagePosition, quantile, summarizePppDistribution };
});
