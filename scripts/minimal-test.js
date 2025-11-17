// Minimal Test Script - Only startInit function
console.log('💫 MINIMAL TEST: Loading script.js functions...');

try {
    // Test if basic functions are available from core.js
    console.log('loadJSON:', typeof loadJSON);
    console.log('showSpinner:', typeof showSpinner);
    console.log('whenDocumentReady:', typeof whenDocumentReady);
    
    // Define minimal init function
    async function init() {
        console.log('✅ MINIMAL INIT: Started');
        if (typeof loadJSON !== 'function') {
            console.error('❌ loadJSON not available');
            return;
        }
        console.log('✅ MINIMAL INIT: loadJSON available, testing...');
        const kpis = await loadJSON("data/meta/available_kpis.json");
        console.log('✅ MINIMAL INIT: KPIs loaded:', kpis ? 'SUCCESS' : 'FAILED');
    }
    
    // Define startInit function
    function startInit() {
        console.log('✅ MINIMAL startInit: Called');
        init().catch(err => {
            console.error('❌ MINIMAL init failed:', err);
        });
    }
    
    // Auto-start
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startInit);
    } else {
        startInit();
    }
    
    console.log('✅ MINIMAL TEST: Setup complete');
    
} catch (error) {
    console.error('❌ MINIMAL TEST: Setup failed:', error);
}