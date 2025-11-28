/**
 * RealityCheck About Page Scripts
 * Handles Earth Overshoot Timer and page-specific animations
 */

/**
 * Calculates and displays Earth Overshoot Day status
 * Shows how many days humanity has exceeded Earth's yearly capacity
 */
function updateOvershootTimer() {
  const today = new Date();
  const year = today.getFullYear();
  const overshootDate = new Date(`${year}-07-25T00:00:00`);
  const diff = today - overshootDate;
  const daysAfter = Math.floor(diff / (1000 * 60 * 60 * 24));
  const element = document.getElementById("overshoot-timer");

  if (!element) {
    console.warn("⚠️ Overshoot timer element not found");
    return;
  }

  if (daysAfter < 0) {
    element.innerHTML = `🌱 Humanity is still living <b>within</b> Earth's yearly means – for now.<br>
      <small>Overshoot Day in ${Math.abs(daysAfter)} days (${overshootDate.toDateString()}).</small>`;
  } else if (daysAfter === 0) {
    element.innerHTML = `⚖️ Today is <b>Earth Overshoot Day ${year}</b>.<br>
      <small>From now on, humanity consumes more than Earth can regenerate this year.</small>`;
  } else {
    element.innerHTML = `🔴 Earth Overshoot Day was <b>${daysAfter} days ago</b> (${overshootDate.toDateString()}).<br>
      <small>Humanity is living ${daysAfter} days beyond Earth's yearly capacity.</small>`;
  }
}

/**
 * Initializes fade-in animation for the about section
 */
function initAboutPageAnimation() {
  const aboutSection = document.getElementById("about-section");
  if (aboutSection) {
    aboutSection.classList.add("loaded");
  }
}

// Initialize page functionality when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  updateOvershootTimer();
});

// Initialize animation when page loads
window.addEventListener("load", () => {
  initAboutPageAnimation();
});