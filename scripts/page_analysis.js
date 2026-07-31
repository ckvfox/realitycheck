/**
 * Analysis Page - AI-generated global KPI report loader
 * Loads and renders markdown analysis with marked.js parser
 */

const ANALYSIS_ALLOWED_TAGS = new Set([
  "A", "BLOCKQUOTE", "BR", "CODE", "EM", "H1", "H2", "H3", "H4",
  "H5", "H6", "HR", "LI", "OL", "P", "PRE", "STRONG", "TABLE",
  "TBODY", "TD", "TH", "THEAD", "TR", "UL"
]);

function sanitizeAnalysisHtml(html) {
  const template = document.createElement("template");
  template.innerHTML = html;
  [...template.content.querySelectorAll("*")].forEach(element => {
    if (!ANALYSIS_ALLOWED_TAGS.has(element.tagName)) {
      element.replaceWith(document.createTextNode(element.textContent || ""));
      return;
    }
    [...element.attributes].forEach(attribute => {
      const keepLinkAttribute = element.tagName === "A" && ["href", "title"].includes(attribute.name);
      if (!keepLinkAttribute) element.removeAttribute(attribute.name);
    });
    if (element.tagName === "A") {
      const href = element.getAttribute("href") || "";
      try {
        const url = new URL(href, window.location.href);
        if (!["http:", "https:", "mailto:"].includes(url.protocol) && !href.startsWith("#")) {
          element.removeAttribute("href");
        }
      } catch {
        element.removeAttribute("href");
      }
      element.setAttribute("rel", "noopener noreferrer");
    }
  });
  return template.content;
}

async function loadAnalysis() {
  const section = document.getElementById("analysis-section");
  const container = document.getElementById("analysis-content");
  
  if (!container) {
    console.error("❌ Analysis container not found");
    return;
  }

  try {
    const response = await fetch("data/analysis.md");
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: Analysis file not found`);
    }
    
    const markdown = await response.text();
    
    // Ensure marked.js is loaded
    if (typeof marked === 'undefined') {
      throw new Error("Marked.js library not loaded");
    }
    
    // Parse markdown to HTML
    const html = marked.parse(markdown.trim());
    container.replaceChildren(sanitizeAnalysisHtml(html));
    
    // Mark as loaded for CSS styling
    if (section) {
      section.classList.add("loaded");
    }
    
    console.log("✅ Analysis loaded successfully");
    
  } catch (error) {
    console.error("⚠️ Analysis loading failed:", error);
    
    const errorBox = document.createElement("div");
    errorBox.className = "error-message";
    const heading = document.createElement("h3");
    heading.textContent = "⚠️ Analysis Not Available";
    const guidance = document.createElement("p");
    guidance.append("No analysis found. Please run ");
    const command = document.createElement("code");
    command.textContent = "fetch_data.py";
    guidance.append(command, " to generate a new report.");
    const detail = document.createElement("p");
    detail.className = "error-detail";
    detail.textContent = `Error: ${error.message}`;
    errorBox.append(heading, guidance, detail);
    container.replaceChildren(errorBox);
    
    if (section) {
      section.classList.add("loaded");
    }
  }
}

// Initialize when DOM is ready
if (typeof onDocumentReady === "function") {
  onDocumentReady(loadAnalysis);
} else {
  document.addEventListener("DOMContentLoaded", loadAnalysis);
}
