(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.RCWarStressTest = api;
})(typeof window !== "undefined" ? window : null, function () {
  "use strict";
  function isGerman() { return typeof document !== "undefined" && document.documentElement.lang === "de"; }
  function ui(en, de) { return isGerman() ? de : en; }

  function validatePayload(data) {
    return Boolean(data && data.meta && data.evidenceTypes && Array.isArray(data.phases) && data.phases.length === 7 &&
      Array.isArray(data.hours72) && Array.isArray(data.households) && Array.isArray(data.objections) &&
      data.people && Array.isArray(data.people.models) && data.people.serviceDebate &&
      Array.isArray(data.people.serviceDebate.models) && data.people.refusalParadox && data.strategicDoctrine && data.conscriptionMap &&
      Array.isArray(data.conscriptionMap.democratic) && Array.isArray(data.conscriptionMap.nonDemocratic) &&
      Array.isArray(data.conscriptionMap.noInformation) && data.conscriptionMap.countryNotes &&
      Array.isArray(data.preventionMeasures) && Array.isArray(data.sources));
  }

  function sourceIndex(data) {
    return Object.fromEntries(data.sources.map(source => [source.id, source]));
  }

  function conscriptionCategory(mapData, country) {
    if (mapData.noInformation.includes(country)) return "no-info";
    if (mapData.democratic.includes(country)) return "democratic";
    if (mapData.nonDemocratic.includes(country)) return "non-democratic";
    return "none";
  }

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  function evidenceBadge(data, type) {
    const item = data.evidenceTypes[type] || data.evidenceTypes.unknown;
    const badge = element("span", `war-evidence war-evidence--${item.class}`, item.label);
    badge.title = item.description;
    return badge;
  }

  function sourceLink(source, label) {
    const link = element("a", "war-source-link", label || source.title);
    link.href = source.url; link.target = "_blank"; link.rel = "noopener noreferrer";
    return link;
  }

  function appendDefinitionList(container, rows) {
    const list = element("dl", "war-phase-facts");
    rows.forEach(([term, value]) => {
      const row = element("div"); row.append(element("dt", "", term), element("dd", "", value)); list.appendChild(row);
    });
    container.appendChild(list);
  }

  function renderPhase(data, sources, phase) {
    const details = element("details", "war-phase");
    const summary = element("summary", "war-phase-summary");
    summary.append(element("span", "war-phase-number", String(phase.id)), element("span", "war-phase-title", phase.title), evidenceBadge(data, phase.evidence));
    const body = element("div", "war-phase-body");
    appendDefinitionList(body, [
      [ui("Event / assumption", "Ereignis / Annahme"), phase.event], [ui("Adversary's objective", "Ziel des Gegners"), phase.aim], [ui("Germany and NATO", "Deutschland und NATO"), phase.response],
      [ui("Consequences for citizens", "Folgen für die Bevölkerung"), phase.citizens], [ui("Escalation risk", "Eskalationsrisiko"), phase.risk], [ui("Where it could still be prevented", "Wo die Kette noch gestoppt werden könnte"), phase.prevention]
    ]);
    const links = element("p", "war-phase-sources"); links.append(ui("Evidence context: ", "Evidenzkontext: "));
    phase.sources.map(id => sources[id]).filter(Boolean).forEach((source, index) => {
      if (index) links.append(" · "); links.appendChild(sourceLink(source, source.organisation));
    });
    body.appendChild(links); details.append(summary, body); return details;
  }

  function renderHours(root, data) {
    const box = root.querySelector("[data-war-hours]");
    data.hours72.forEach(item => {
      const card = element("article", "war-72-card");
      card.append(element("p", "war-72-time", item.time), element("h4", "", item.title));
      const list = element("ul"); item.items.forEach(text => list.appendChild(element("li", "", text)));
      const authority = element("p", "war-72-authority"); authority.append(element("strong", "", ui("Authorities: ", "Behörden: ")), document.createTextNode(item.authority));
      card.append(list, authority); box.appendChild(card);
    });
    const prep = root.querySelector("[data-war-preparedness]");
    prep.append(element("h4", "", data.preparedness.title), element("p", "", data.preparedness.text));
    const source = data.sources.find(item => item.id === data.preparedness.source);
    if (source) prep.appendChild(sourceLink(source, ui("Open the BBK guide", "BBK-Ratgeber öffnen")));
  }

  function renderHouseholds(root, data) {
    const select = root.querySelector("[data-war-household]");
    const output = root.querySelector("[data-war-household-result]");
    data.households.forEach(item => { const option = element("option", "", item.label); option.value = item.id; select.appendChild(option); });
    function render() {
      const household = data.households.find(item => item.id === select.value) || data.households[0];
      output.replaceChildren();
      appendDefinitionList(output, [[ui("Immediate daily life", "Unmittelbarer Alltag"),household.immediate],[ui("Economic pressure", "Wirtschaftlicher Druck"),household.economic],[ui("Supply risk", "Versorgungsrisiko"),household.supply],[ui("Work", "Arbeit"),household.work],[ui("Public support", "Öffentliche Unterstützung"),household.support],[ui("Special protection needs", "Besonderer Schutzbedarf"),household.needs]]);
    }
    select.addEventListener("change", render); render();
  }

  function renderDebate(root, data, sources) {
    const box = root.querySelector("[data-war-debate]");
    data.debate.theses.forEach(thesis => {
      const card = element("article", "war-debate-card"); card.append(element("h4", "", thesis.title));
      appendDefinitionList(card, [[ui("Argument", "Argument"),thesis.argument],[ui("Evidence", "Evidenz"),thesis.evidence],[ui("Remaining uncertainty", "Verbleibende Unsicherheit"),thesis.uncertainty]]);
      if (sources[thesis.source]) card.appendChild(sourceLink(sources[thesis.source], ui("Further source", "Weitere Quelle"))); box.appendChild(card);
    });
    root.querySelector("[data-war-debate-conclusion]").textContent = data.debate.conclusion;
  }

  function renderObjections(root, data, sources) {
    const box = root.querySelector("[data-war-objections]");
    data.objections.forEach(item => {
      const details = element("details", "war-objection"); details.appendChild(element("summary", "", item.title));
      const body = element("div", "war-objection-body");
      appendDefinitionList(body, [[ui("Legitimate core", "Berechtigter Kern"),item.core],[ui("Counterargument", "Gegenargument"),item.reply],[ui("Evidence", "Evidenz"),item.evidence],[ui("Remaining uncertainty", "Verbleibende Unsicherheit"),item.uncertainty]]);
      const sourceIds = Array.isArray(item.sources) ? item.sources : [item.source];
      const sourceRow = element("p", "war-objection-sources");
      sourceIds.forEach((sourceId, index) => {
        if (!sources[sourceId]) return;
        if (sourceRow.childNodes.length > 0) sourceRow.appendChild(document.createTextNode(" · "));
        sourceRow.appendChild(sourceLink(sources[sourceId], index === 0 ? ui("Further source", "Weitere Quelle") : sources[sourceId].organisation));
      });
      if (sourceRow.childNodes.length > 0) body.appendChild(sourceRow);
      details.appendChild(body); box.appendChild(details);
    });
  }

  function renderPeople(root, data, sources) {
    const roles = root.querySelector("[data-war-roles]"); data.people.roles.forEach(role => roles.appendChild(element("li", "", role)));
    const debate = data.people.serviceDebate;
    root.querySelector("[data-war-service-title]").textContent = debate.title;
    root.querySelector("[data-war-service-intro]").textContent = debate.intro;
    root.querySelector("[data-war-service-learning]").textContent = debate.learning;
    const comparison = root.querySelector("[data-war-service-comparison]");
    debate.models.forEach(item => {
      const card = element("article", "war-service-model-card"); card.appendChild(element("h5", "", item.title));
      appendDefinitionList(card, [[ui("Who serves?", "Wer dient?"),item.scope],[ui("Primary purpose", "Hauptzweck"),item.purpose],[ui("Potential benefit", "Möglicher Nutzen"),item.benefit],[ui("Risks and implementation problems", "Risiken und Umsetzungsprobleme"),item.risk],[ui("Legal feasibility", "Rechtliche Machbarkeit"),item.law],[ui("Assessment", "Bewertung"),item.judgement]]);
      comparison.appendChild(card);
    });
    root.querySelector("[data-war-service-enforcement-title]").textContent = debate.enforcementTitle;
    const enforcement = root.querySelector("[data-war-service-enforcement]"); debate.enforcement.forEach(item => enforcement.appendChild(element("li", "", item)));
    root.querySelector("[data-war-service-conclusion]").textContent = debate.conclusion;
    const refusal = data.people.refusalParadox;
    root.querySelector("[data-war-refusal-title]").textContent = refusal.title;
    root.querySelector("[data-war-refusal-text]").textContent = refusal.text;
    root.querySelector("[data-war-refusal-evidence]").textContent = refusal.evidence;
    root.querySelector("[data-war-refusal-limit]").textContent = refusal.limit;
    const refusalSources = root.querySelector("[data-war-refusal-sources]");
    refusal.sources.forEach((sourceId, index) => {
      if (!sources[sourceId]) return;
      if (index > 0) refusalSources.appendChild(document.createTextNode(" · "));
      refusalSources.appendChild(sourceLink(sources[sourceId], sources[sourceId].organisation));
    });
    const body = root.querySelector("[data-war-service-models]");
    data.people.models.forEach(item => {
      const row = element("tr"); ["model","effect","speed","cost","freedom","fairness","specialists","reserve","labour"].forEach(key => row.appendChild(element("td", "", item[key]))); body.appendChild(row);
    });
    const safeguards = root.querySelector("[data-war-safeguards]"); data.people.safeguards.forEach(item => safeguards.appendChild(element("li", "", item)));
  }

  function addConscriptionLegend(map, data) {
    const colors = { "no-info":"#9ca3af", none:"#2f6fab", democratic:"#27864a", "non-democratic":"#d6a726" };
    const labels = {
      "no-info":ui("No information / unresolved territory", "Keine Information / ungeklärtes Gebiet"),
      none:ui("No active conscription", "Keine aktive Wehrpflicht"),
      democratic:ui("Active conscription · democracy", "Aktive Wehrpflicht · Demokratie"),
      "non-democratic":ui("Active conscription · not classified as democracy", "Aktive Wehrpflicht · nicht als Demokratie eingeordnet")
    };
    const control = L.control({ position:"bottomright" });
    control.onAdd = function () {
      const box = L.DomUtil.create("div", "war-conscription-legend real-wages-map-legend");
      const heading = document.createElement("strong"); heading.textContent = data.statusDate; box.appendChild(heading);
      Object.keys(labels).forEach(key => {
        const row = document.createElement("div");
        const swatch = document.createElement("span"); swatch.className = "real-wages-swatch"; swatch.style.backgroundColor = colors[key];
        row.append(swatch, document.createTextNode(labels[key])); box.appendChild(row);
      });
      return box;
    };
    control.addTo(map);
  }

  async function renderConscriptionMap(root, data) {
    const status = root.querySelector("[data-war-conscription-status]");
    if (typeof L === "undefined" || !window.RCMap || typeof window.loadJSON !== "function") {
      status.textContent = ui("The map library is unavailable.", "Die Kartenbibliothek ist nicht verfügbar."); return null;
    }
    try {
      status.textContent = ui("Loading worldwide conscription comparison …", "Weltweiter Wehrpflichtvergleich wird geladen …");
      const [geoJson, mappings] = await Promise.all([window.RCMap.loadGeoJSON(), window.loadJSON("data/meta/country_mappings.json")]);
      if (!geoJson || !Array.isArray(geoJson.features) || !mappings) throw new Error("Country geometries are unavailable.");
      const mapData = data.conscriptionMap;
      const colors = { "no-info":"#9ca3af", none:"#2f6fab", democratic:"#27864a", "non-democratic":"#d6a726" };
      const labels = {
        "no-info":ui("No information / unresolved territory", "Keine Information / ungeklärtes Gebiet"),
        none:ui("No active conscription identified", "Keine aktive Wehrpflicht festgestellt"),
        democratic:ui("Active conscription · V-Dem democracy", "Aktive Wehrpflicht · V-Dem-Demokratie"),
        "non-democratic":ui("Active conscription · not classified as a V-Dem democracy", "Aktive Wehrpflicht · von V-Dem nicht als Demokratie eingeordnet")
      };
      const map = window.RCMap.createMap("war-conscription-map", { center:[20,8], zoom:2, minZoom:1, maxZoom:6 });
      window.RCMap.addGeoJSONLayer(map, geoJson, feature => {
        const raw = window.RCMap.getCountryName(feature) || "Unknown";
        const country = mappings[raw] || raw;
        const category = conscriptionCategory(mapData, country);
        return { fillColor:colors[category], fillOpacity:.78, color:"#fff", weight:.7, opacity:1, dashArray:category === "no-info" ? "4 3" : null };
      }, (feature, layer) => {
        const raw = window.RCMap.getCountryName(feature) || "Unknown";
        const country = mappings[raw] || raw;
        const category = conscriptionCategory(mapData, country);
        layer.bindTooltip(country, { sticky:true });
        layer.bindPopup(() => {
          const box = element("div"); box.append(element("strong", "", country), element("p", "", labels[category]));
          if (mapData.countryNotes[country]) box.appendChild(element("p", "", mapData.countryNotes[country]));
          return box;
        });
      });
      Object.entries(mapData.pointCountries || {}).forEach(([country, coordinates]) => {
        const category = conscriptionCategory(mapData, country);
        const marker = L.circleMarker(coordinates, { radius:6, fillColor:colors[category], fillOpacity:.9, color:"#fff", weight:1.5 }).addTo(map);
        marker.bindTooltip(country, { sticky:true });
        marker.bindPopup(() => {
          const box = element("div"); box.append(element("strong", "", country), element("p", "", labels[category])); return box;
        });
      });
      addConscriptionLegend(map, mapData);
      const stats = root.querySelector("[data-war-conscription-stats]");
      [
        [mapData.democratic.length, ui("countries with active conscription classified as democracies", "Länder mit aktiver Wehrpflicht, die als Demokratien eingeordnet sind")],
        [mapData.nonDemocratic.length, ui("countries with active conscription not classified as democracies", "Länder mit aktiver Wehrpflicht, die nicht als Demokratien eingeordnet sind")],
        [mapData.democratic.length + mapData.nonDemocratic.length, ui("countries with active or currently enforced conscription in this synthesis", "Länder mit aktiver oder aktuell durchgesetzter Wehrpflicht in diesem Überblick")]
      ].forEach(([value, label]) => {
        const card = element("div", "real-wages-stat"); card.append(element("strong", "", String(value)), element("span", "", label)); stats.appendChild(card);
      });
      status.textContent = mapData.statusDate;
      setTimeout(() => map.invalidateSize(), 100);
      window.addEventListener("resize", () => map.invalidateSize(), { passive:true });
      return map;
    } catch (error) {
      status.textContent = `${ui("The conscription map could not be loaded", "Die Wehrpflichtkarte konnte nicht geladen werden")}: ${error.message}`;
      return null;
    }
  }

  function renderHistory(root, data) {
    const box = root.querySelector("[data-war-history]");
    data.historicalCases.forEach(item => { const card = element("article"); card.append(element("h4", "", item.case), element("p", "", item.use), element("p", "war-history-limit", `${ui("Limit", "Grenze")}: ${item.limit}`)); box.appendChild(card); });
  }

  function renderPrevention(root, data) {
    const box = root.querySelector("[data-war-prevention]");
    data.preventionMeasures.forEach(group => {
      const card = element("article", `war-prevention-card war-prevention-card--${group.category.toLowerCase().replaceAll(" ", "-")}`);
      card.appendChild(element("h4", "", group.category));
      const list = element("ul"); group.items.forEach(item => list.appendChild(element("li", "", item))); card.appendChild(list); box.appendChild(card);
    });
  }

  function renderSources(root, data) {
    const body = root.querySelector("[data-war-sources]");
    data.sources.forEach(source => {
      const row = element("tr"); row.append(element("td", "", data.evidenceTypes[source.type]?.label || source.type), element("td", "", source.organisation));
      const linkCell = element("td"); linkCell.appendChild(sourceLink(source)); row.append(linkCell, element("td", "", source.finding)); body.appendChild(row);
    });
  }

  function boot() {
    const root = document.getElementById("germany-war-stress-test");
    const dataNode = document.getElementById("germany-war-stress-data");
    if (!root || !dataNode) return;
    let data; try { data = JSON.parse(dataNode.textContent); } catch (_) { data = null; }
    if (!validatePayload(data)) return;
    const sources = sourceIndex(data);

    const legend = root.querySelector("[data-war-evidence-legend]");
    Object.keys(data.evidenceTypes).forEach(type => legend.appendChild(evidenceBadge(data, type)));
    const timeline = root.querySelector("[data-war-timeline]"); data.phases.forEach(phase => timeline.appendChild(renderPhase(data, sources, phase)));
    renderPrevention(root, data); renderHours(root, data); renderHouseholds(root, data); renderDebate(root, data, sources); renderObjections(root, data, sources); renderPeople(root, data, sources); renderHistory(root, data); renderSources(root, data);

    root.querySelector("[data-war-conscription-title]").textContent = data.conscriptionMap.title;
    root.querySelector("[data-war-conscription-definition]").textContent = data.conscriptionMap.definition;
    root.querySelector("[data-war-conscription-conclusion]").textContent = data.conscriptionMap.conclusion;
    root.querySelector("[data-war-conscription-method]").textContent = data.conscriptionMap.democracyMethod;

    const closing = root.querySelector("[data-war-closing]");
    closing.append(element("h3", "", data.closing.headline), element("p", "", data.closing.explanation), element("strong", "", data.closing.balance));

    const button = root.querySelector("[data-war-activate]"); const content = root.querySelector("[data-war-content]");
    let conscriptionMapPromise = null;
    button.addEventListener("click", () => {
      const opening = content.hidden; content.hidden = !opening; button.setAttribute("aria-expanded", String(opening));
      button.textContent = opening ? ui("Hide stress test", "Stresstest ausblenden") : ui("Run the stress test", "Stresstest starten");
      if (opening) {
        content.querySelector(".war-phase")?.setAttribute("open", ""); content.focus({ preventScroll:true }); content.scrollIntoView({ behavior:"smooth", block:"start" });
        requestAnimationFrame(() => {
          if (!conscriptionMapPromise) conscriptionMapPromise = renderConscriptionMap(root, data);
          else conscriptionMapPromise.then(map => map?.invalidateSize());
        });
      }
    });
  }

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once:true }); else boot();
  }
  return { validatePayload, sourceIndex, conscriptionCategory };
});
