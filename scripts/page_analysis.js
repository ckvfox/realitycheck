/**
 * Analysis Page - AI-generated global KPI report loader
 * Loads and renders markdown analysis with marked.js parser
 */

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
    container.innerHTML = html;
    
    // Mark as loaded for CSS styling
    if (section) {
      section.classList.add("loaded");
    }
    
    console.log("✅ Analysis loaded successfully");
    
  } catch (error) {
    console.error("⚠️ Analysis loading failed:", error);
    
    container.innerHTML = `
      <div class="error-message">
        <h3>⚠️ Analysis Not Available</h3>
        <p>No analysis found. Please run <code>fetch_data.py</code> to generate a new report.</p>
        <p class="error-detail">Error: ${error.message}</p>
      </div>
    `;
    
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