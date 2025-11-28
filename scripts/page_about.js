// RealityCheck About Page Scripts (restored, overshoot removed)
// Handles page-specific animations only

function initAboutPageAnimation() {
  const aboutSection = document.getElementById("about-section");
  if (aboutSection) {
    aboutSection.classList.add("loaded");
  }
}

window.addEventListener("load", () => {
  initAboutPageAnimation();
});