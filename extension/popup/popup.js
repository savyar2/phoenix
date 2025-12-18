/**
 * Phoenix Protocol - Popup Script
 */

const ROUTER_URL = 'http://127.0.0.1:8787';

async function checkConnection() {
  try {
    const response = await fetch(`${ROUTER_URL}/health`);
    const data = await response.json();
    
    const statusEl = document.getElementById('status');
    if (data.status === 'healthy') {
      statusEl.textContent = '✅ Connected to Context Router';
      statusEl.className = 'status connected';
    } else {
      statusEl.textContent = '❌ Router not responding';
      statusEl.className = 'status disconnected';
    }
  } catch (error) {
    const statusEl = document.getElementById('status');
    statusEl.textContent = '❌ Cannot connect to router';
    statusEl.className = 'status disconnected';
  }
}

// Check connection when popup opens
checkConnection();

