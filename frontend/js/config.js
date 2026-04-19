/* Configuration */
const CONFIG = {
    API_BASE: 'http://localhost:8000',
    DEBUG: true
};

// Log helper
function log(...args) {
    if (CONFIG.DEBUG) {
        console.log('[AdaptiveLearn]', ...args);
    }
}
