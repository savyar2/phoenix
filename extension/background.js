/**
 * Phoenix Protocol - Background Service Worker
 * 
 * Minimal background worker for extension lifecycle.
 * Most functionality is handled directly in popup.js and content.js.
 */

const ROUTER_URL = 'http://127.0.0.1:8787';

// ============================================
// INSTALLATION
// ============================================

chrome.runtime.onInstalled.addListener(async (details) => {
  console.log('Phoenix Protocol extension installed/updated');
  
  // Initialize default settings
  try {
    const existing = await chrome.storage.sync.get(['phoenixEnabled', 'currentPersona']);
    
    const defaults = {};
    if (existing.phoenixEnabled === undefined) defaults.phoenixEnabled = true;
    if (existing.currentPersona === undefined) defaults.currentPersona = 'Personal';
    
    if (Object.keys(defaults).length > 0) {
      await chrome.storage.sync.set(defaults);
    }
  } catch (e) {
    console.warn('Failed to initialize settings:', e);
  }
});

// ============================================
// BADGE UPDATES
// ============================================

async function updateBadge(connected) {
  try {
    if (connected) {
      await chrome.action.setBadgeText({ text: '' });
    } else {
      await chrome.action.setBadgeText({ text: '!' });
      await chrome.action.setBadgeBackgroundColor({ color: '#ff4757' });
    }
  } catch (e) {
    // Ignore badge errors
  }
}

// Check router connection periodically
async function checkRouter() {
  try {
    const response = await fetch(`${ROUTER_URL}/health`);
    const data = await response.json();
    updateBadge(data.status === 'healthy');
  } catch (e) {
    updateBadge(false);
  }
}

// Initial check after 3 seconds
setTimeout(checkRouter, 3000);

// Periodic check every 60 seconds
setInterval(checkRouter, 60000);

console.log('Phoenix Protocol background service ready');
