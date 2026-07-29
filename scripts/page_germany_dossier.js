(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.RCGermanyDossier = api;
})(typeof window !== "undefined" ? window : null, function () {
  "use strict";

  function cleanHash(hash) {
    if (typeof hash !== "string") return "";
    try { return decodeURIComponent(hash.replace(/^#/, "")); }
    catch (_) { return hash.replace(/^#/, ""); }
  }

  function resolvePanelId(hash, panelIds, containingPanelId) {
    const id = cleanHash(hash);
    if (panelIds.includes(id)) return id;
    if (containingPanelId && panelIds.includes(containingPanelId)) return containingPanelId;
    return panelIds[0] || "";
  }

  function nextTabIndex(current, key, length) {
    if (!Number.isInteger(current) || length < 1) return 0;
    if (key === "Home") return 0;
    if (key === "End") return length - 1;
    if (key === "ArrowRight" || key === "ArrowDown") return (current + 1) % length;
    if (key === "ArrowLeft" || key === "ArrowUp") return (current - 1 + length) % length;
    return current;
  }

  function boot() {
    const frame = document.querySelector("[data-dossier-frame]");
    const tabs = Array.from(document.querySelectorAll("[data-dossier-tab]"));
    const panels = Array.from(document.querySelectorAll("[data-dossier-panel]"));
    if (!frame || tabs.length !== panels.length || tabs.length === 0) return;
    const panelIds = panels.map(panel => panel.id);

    function panelFromHash() {
      const hashId = cleanHash(window.location.hash);
      const target = hashId ? document.getElementById(hashId) : null;
      const containingPanel = target?.closest("[data-dossier-panel]");
      return resolvePanelId(window.location.hash, panelIds, containingPanel?.id || "");
    }

    function activate(panelId, options) {
      const config = options || {};
      if (!panelIds.includes(panelId)) panelId = panelIds[0];
      tabs.forEach(tab => {
        const selected = tab.dataset.dossierTab === panelId;
        tab.setAttribute("aria-selected", String(selected));
        tab.setAttribute("tabindex", selected ? "0" : "-1");
      });
      panels.forEach(panel => {
        const selected = panel.id === panelId;
        panel.hidden = !selected;
        panel.classList.toggle("is-active", selected);
      });
      if (config.updateHash && window.history?.replaceState) {
        window.history.replaceState(null, "", `#${panelId}`);
      }
      requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
    }

    tabs.forEach((tab, index) => {
      tab.addEventListener("click", event => {
        event.preventDefault();
        activate(tab.dataset.dossierTab, { updateHash: true });
      });
      tab.addEventListener("keydown", event => {
        const next = nextTabIndex(index, event.key, tabs.length);
        if (next === index && !["Home", "End"].includes(event.key)) return;
        event.preventDefault();
        tabs[next].focus();
        activate(tabs[next].dataset.dossierTab, { updateHash: true });
      });
    });

    window.addEventListener("hashchange", () => {
      const panelId = panelFromHash();
      activate(panelId);
      const target = document.getElementById(cleanHash(window.location.hash));
      if (target && target.id !== panelId) requestAnimationFrame(() => target.scrollIntoView({ block: "start" }));
    });
    const initialPanelId = panelFromHash();
    activate(initialPanelId);
    const initialTarget = document.getElementById(cleanHash(window.location.hash));
    if (initialTarget) requestAnimationFrame(() => initialTarget.scrollIntoView({ block: "start" }));
    frame.dataset.dossierReady = "true";
  }

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
    else boot();
  }
  return { cleanHash, resolvePanelId, nextTabIndex };
});
