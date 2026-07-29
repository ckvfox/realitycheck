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
  const announcedDates = { 2026: "2026-07-30" };
  const year = today.getFullYear();
  const latestYear = Math.max(...Object.keys(announcedDates).map(Number));
  const dateString = announcedDates[year] || announcedDates[latestYear];
  const displayYear = announcedDates[year] ? year : latestYear;
  const overshootDate = new Date(`${dateString}T00:00:00`);
  const diff = today - overshootDate;
  const daysAfter = Math.floor(diff / (1000 * 60 * 60 * 24));
  const element = document.getElementById("overshoot-timer");

  if (!element) {
    console.warn("⚠️ Overshoot timer element not found");
    return;
  }

  if (daysAfter < 0) {
    element.dataset.state = "before";
    element.innerHTML = `<strong>${Math.abs(daysAfter)} days until Earth Overshoot Day</strong>
      <small>${overshootDate.toLocaleDateString("en-GB", { day:"numeric", month:"long", year:"numeric" })} · Humanity is still within Earth's yearly regenerative budget — for now.</small>`;
  } else if (daysAfter === 0) {
    element.dataset.state = "today";
    element.innerHTML = `<strong>Earth Overshoot Day is today</strong>
      <small>From now on, humanity consumes more than Earth can regenerate this year.</small>`;
  } else {
    element.dataset.state = "after";
    element.innerHTML = `<strong>${daysAfter} days beyond Earth Overshoot Day</strong>
      <small>${overshootDate.toLocaleDateString("en-GB", { day:"numeric", month:"long", year:"numeric" })} · Humanity is now using more than Earth can regenerate this year.</small>`;
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
