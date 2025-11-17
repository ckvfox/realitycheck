/**
 * RealityCheck Index Page Redirect
 * Automatically redirects to the main countries page
 */

/**
 * Performs immediate redirect to countries.html
 * This ensures the application starts at the main interface
 */
function redirectToCountries() {
  window.location.replace('countries.html');
}

// Execute redirect immediately
redirectToCountries();