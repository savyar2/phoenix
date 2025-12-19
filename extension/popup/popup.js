/**
 * Phoenix Protocol - Popup Script
 * 
 * Handles popup UI interactions, settings, and context preview.
 * Uses direct fetch to router - no background worker dependency.
 */

const ROUTER_URL = 'http://127.0.0.1:8787';

// State
let currentSettings = {
  phoenixEnabled: true,
  currentPersona: 'Personal'
};

// ============================================
// INITIALIZATION
// ============================================

async function initialize() {
  try {
    // Load settings first
    await loadSettings();
    
    // Then load other data
    await Promise.all([
      checkConnection(),
      loadContextPreview(),
      loadStats()
    ]);
    
    // Setup event listeners
    setupEventListeners();
  } catch (error) {
    console.error('Initialization error:', error);
  }
}

// ============================================
// SETTINGS
// ============================================

async function loadSettings() {
  try {
    const settings = await chrome.storage.sync.get(['phoenixEnabled', 'currentPersona']);
    currentSettings = {
      phoenixEnabled: settings.phoenixEnabled !== false,
      currentPersona: settings.currentPersona || 'Personal'
    };
    
    // Update UI
    const toggle = document.getElementById('main-toggle');
    if (toggle) {
      if (currentSettings.phoenixEnabled) {
        toggle.classList.add('active');
      } else {
        toggle.classList.remove('active');
      }
    }
    
    // Update persona buttons
    document.querySelectorAll('.persona-btn').forEach(btn => {
      if (btn.dataset.persona === currentSettings.currentPersona) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  } catch (error) {
    console.warn('Settings load error (using defaults):', error.message);
    // Use defaults - already set in currentSettings
  }
}

async function updateSetting(key, value) {
  try {
    await chrome.storage.sync.set({ [key]: value });
    currentSettings[key] = value;
  } catch (error) {
    console.warn('Setting update error:', error.message);
  }
}

// ============================================
// CONNECTION CHECK
// ============================================

async function checkConnection() {
  const statusDot = document.getElementById('status-dot');
  const statusText = document.getElementById('status-text');
  
  if (!statusDot || !statusText) return;
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);
    
    const response = await fetch(`${ROUTER_URL}/health`, {
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    
    const data = await response.json();
    
    if (data.status === 'healthy') {
      statusDot.classList.add('connected');
      statusDot.classList.remove('disconnected');
      statusText.textContent = 'Router Connected';
    } else {
      statusDot.classList.add('disconnected');
      statusDot.classList.remove('connected');
      statusText.textContent = 'Router Issue';
    }
  } catch (error) {
    statusDot.classList.add('disconnected');
    statusDot.classList.remove('connected');
    statusText.textContent = 'Router Offline';
  }
}

// ============================================
// CONTEXT PREVIEW
// ============================================

async function loadContextPreview() {
  const previewEl = document.getElementById('context-preview');
  if (!previewEl) return;
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    
    const response = await fetch(
      `${ROUTER_URL}/api/context-pack/preview?persona=${encodeURIComponent(currentSettings.currentPersona || 'Personal')}`,
      { signal: controller.signal }
    );
    clearTimeout(timeoutId);
    
    const data = await response.json();
    
    if (data && data.cards && data.cards.length > 0) {
      previewEl.innerHTML = data.cards.map(card => `
        <div class="context-card">
          <div class="context-card-type">${escapeHtml(card.type)}</div>
          <div class="context-card-text">${escapeHtml(card.text)}</div>
        </div>
      `).join('');
    } else {
      previewEl.innerHTML = `
        <div class="empty-state">
          <div style="font-size: 24px; margin-bottom: 8px;">📭</div>
          <div>No memory cards yet</div>
          <div style="margin-top: 4px; font-size: 11px; color: #555;">Add cards in the Dashboard</div>
        </div>
      `;
    }
  } catch (error) {
    previewEl.innerHTML = `
      <div class="empty-state">
        <div>Could not load preview</div>
        <div style="margin-top: 4px; font-size: 11px; color: #555;">Router may be offline</div>
      </div>
    `;
  }
}

// ============================================
// STATS
// ============================================

async function loadStats() {
  const statCards = document.getElementById('stat-cards');
  const statInjections = document.getElementById('stat-injections');
  const statExtracts = document.getElementById('stat-extracts');
  
  // Load card count from router
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);
    
    const response = await fetch(
      `${ROUTER_URL}/api/memory-cards/list?persona=${encodeURIComponent(currentSettings.currentPersona || 'Personal')}`,
      { signal: controller.signal }
    );
    clearTimeout(timeoutId);
    
    const data = await response.json();
    
    if (statCards) {
      statCards.textContent = data?.cards?.length ?? 0;
    }
  } catch (error) {
    if (statCards) statCards.textContent = '-';
  }
  
  // Load session stats from local storage
  try {
    const stats = await chrome.storage.local.get(['injectionCount', 'extractCount']);
    if (statInjections) statInjections.textContent = stats.injectionCount || 0;
    if (statExtracts) statExtracts.textContent = stats.extractCount || 0;
  } catch (error) {
    // Ignore storage errors for stats
    if (statInjections) statInjections.textContent = '0';
    if (statExtracts) statExtracts.textContent = '0';
  }
}

// ============================================
// HELPERS
// ============================================

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ============================================
// EVENT LISTENERS
// ============================================

function setupEventListeners() {
  // Main toggle
  const mainToggle = document.getElementById('main-toggle');
  if (mainToggle) {
    mainToggle.addEventListener('click', async function() {
      this.classList.toggle('active');
      const enabled = this.classList.contains('active');
      await updateSetting('phoenixEnabled', enabled);
    });
  }
  
  // Persona buttons
  document.querySelectorAll('.persona-btn').forEach(btn => {
    btn.addEventListener('click', async function() {
      document.querySelectorAll('.persona-btn').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      
      const persona = this.dataset.persona;
      await updateSetting('currentPersona', persona);
      
      // Refresh data for new persona
      await loadContextPreview();
      await loadStats();
    });
  });
  
  // Dashboard button
  const dashboardBtn = document.getElementById('btn-dashboard');
  if (dashboardBtn) {
    dashboardBtn.addEventListener('click', () => {
      chrome.tabs.create({ url: 'http://localhost:5173' });
    });
  }
  
  // Refresh button
  const refreshBtn = document.getElementById('btn-refresh');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
      refreshBtn.textContent = 'Refreshing...';
      refreshBtn.disabled = true;
      
      await Promise.all([
        checkConnection(),
        loadContextPreview(),
        loadStats()
      ]);
      
      refreshBtn.textContent = 'Refresh Context';
      refreshBtn.disabled = false;
    });
  }
}

// ============================================
// INITIALIZE
// ============================================

document.addEventListener('DOMContentLoaded', initialize);
