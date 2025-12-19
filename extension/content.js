/**
 * Phoenix Protocol - Content Script
 * 
 * Adds context injection controls to ChatGPT, Claude, and Gemini.
 * Non-invasive approach: "Enhance" button prepends context to your message.
 */

const ROUTER_URL = 'http://127.0.0.1:8787';

// State
let phoenixEnabled = true;
let currentPersona = 'Personal';
let lastContextPack = null;

// ============================================
// SITE DETECTION
// ============================================

function detectSite() {
  const hostname = window.location.hostname;
  if (hostname.includes('chat.openai.com') || hostname.includes('chatgpt.com')) return 'chatgpt';
  if (hostname.includes('claude.ai')) return 'claude';
  if (hostname.includes('gemini.google.com')) return 'gemini';
  return null;
}

// ============================================
// DOM SELECTORS (Site-Specific)
// ============================================

const SELECTORS = {
  chatgpt: {
    textbox: [
      '#prompt-textarea',
      'textarea[data-id="root"]',
      'div[contenteditable="true"][id="prompt-textarea"]',
      'textarea'
    ],
    sendButton: [
      'button[data-testid="send-button"]',
      'button[aria-label*="Send"]',
      'button[aria-label*="send"]'
    ],
    inputArea: [
      'form',
      '.relative.flex'
    ],
    messages: '[data-message-author-role]',
  },
  claude: {
    textbox: [
      'div[contenteditable="true"]',
      'div.ProseMirror',
      'textarea'
    ],
    sendButton: [
      'button[aria-label*="Send"]',
      'button[type="submit"]'
    ],
    inputArea: [
      'form',
      '.flex.flex-col'
    ],
    messages: '[data-testid*="turn"]',
  },
  gemini: {
    textbox: [
      'div[contenteditable="true"]',
      'rich-textarea textarea',
      'textarea'
    ],
    sendButton: [
      'button[aria-label*="Send"]',
      'button[aria-label*="Submit"]'
    ],
    inputArea: [
      'form',
      '.input-area'
    ],
    messages: 'message-content',
  }
};

function findElement(selectors) {
  if (!selectors) return null;
  for (const selector of selectors) {
    try {
      const el = document.querySelector(selector);
      if (el) return el;
    } catch (e) {}
  }
  return null;
}

function findTextbox() {
  const site = detectSite();
  if (!site || !SELECTORS[site]) return null;
  return findElement(SELECTORS[site].textbox);
}

function findSendButton() {
  const site = detectSite();
  if (!site || !SELECTORS[site]) return null;
  return findElement(SELECTORS[site].sendButton);
}

function findInputArea() {
  const site = detectSite();
  if (!site || !SELECTORS[site]) return null;
  return findElement(SELECTORS[site].inputArea);
}

// ============================================
// TEXTBOX VALUE HELPERS
// ============================================

function getTextboxValue(textbox) {
  if (!textbox) return '';
  if (textbox.tagName === 'TEXTAREA' || textbox.tagName === 'INPUT') {
    return textbox.value || '';
  }
  return textbox.textContent || textbox.innerText || '';
}

function setTextboxValue(textbox, value) {
  if (!textbox) return;
  
  if (textbox.tagName === 'TEXTAREA' || textbox.tagName === 'INPUT') {
    textbox.value = value;
    textbox.dispatchEvent(new Event('input', { bubbles: true }));
    textbox.dispatchEvent(new Event('change', { bubbles: true }));
  } else {
    // ContentEditable - need to use execCommand for proper React state sync
    textbox.focus();
    document.execCommand('selectAll', false, null);
    document.execCommand('insertText', false, value);
  }
}

// ============================================
// CONTEXT PACK API
// ============================================

async function getContextPack(draftPrompt) {
  try {
    const response = await fetch(`${ROUTER_URL}/api/context-pack`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        draft_prompt: draftPrompt,
        site_id: detectSite(),
        persona: currentPersona,
        sensitivity_mode: 'quiet',
        max_cards: 5
      })
    });
    
    if (!response.ok) {
      console.warn('Phoenix: Context pack request failed', response.status);
      return null;
    }
    
    const data = await response.json();
    lastContextPack = data.pack;
    return data.pack;
  } catch (error) {
    console.error('Phoenix: Failed to get context pack:', error);
    return null;
  }
}

// ============================================
// ENHANCE BUTTON
// ============================================

function createEnhanceButton() {
  if (document.getElementById('phoenix-enhance-btn')) return;
  
  const btn = document.createElement('button');
  btn.id = 'phoenix-enhance-btn';
  btn.innerHTML = '🔥';
  btn.title = 'Enhance with Phoenix Context (Ctrl+Shift+E)';
  btn.style.cssText = `
    position: fixed;
    bottom: 90px;
    right: 20px;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    cursor: pointer;
    font-size: 20px;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    z-index: 10000;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  `;
  
  btn.addEventListener('mouseenter', () => {
    btn.style.transform = 'scale(1.1)';
    btn.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.5)';
  });
  
  btn.addEventListener('mouseleave', () => {
    btn.style.transform = 'scale(1)';
    btn.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4)';
  });
  
  btn.addEventListener('click', enhanceCurrentPrompt);
  
  document.body.appendChild(btn);
  
  // Keyboard shortcut: Ctrl+Shift+E
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.shiftKey && e.key === 'E') {
      e.preventDefault();
      enhanceCurrentPrompt();
    }
  });
}

async function enhanceCurrentPrompt() {
  const textbox = findTextbox();
  if (!textbox) {
    showNotification('Could not find chat input', 'error');
    return;
  }
  
  const currentText = getTextboxValue(textbox);
  if (!currentText.trim()) {
    showNotification('Type a message first, then enhance', 'info');
    return;
  }
  
  // Check if already enhanced
  if (currentText.includes('--- PERSONAL CONTEXT')) {
    showNotification('Already enhanced!', 'info');
    return;
  }
  
  const btn = document.getElementById('phoenix-enhance-btn');
  if (btn) {
    btn.innerHTML = '⏳';
    btn.style.pointerEvents = 'none';
  }
  
  try {
    const contextPack = await getContextPack(currentText);
    
    if (contextPack && contextPack.pack_text && contextPack.card_count > 0) {
      const enhancedPrompt = `${contextPack.pack_text}\n\n${currentText}`;
      setTextboxValue(textbox, enhancedPrompt);
      
      showContextChip(contextPack);
      showNotification(`Added ${contextPack.card_count} context cards`, 'success');
      
      // Track injection
      chrome.storage.local.get(['injectionCount'], (result) => {
        chrome.storage.local.set({ 
          injectionCount: (result.injectionCount || 0) + 1 
        });
      });
    } else {
      showNotification('No relevant context found', 'info');
    }
  } catch (error) {
    console.error('Phoenix: Enhancement failed', error);
    showNotification('Enhancement failed', 'error');
  } finally {
    if (btn) {
      btn.innerHTML = '🔥';
      btn.style.pointerEvents = 'auto';
    }
  }
}

// ============================================
// EXTRACT BUTTON
// ============================================

function createExtractButton() {
  if (document.getElementById('phoenix-extract-btn')) return;
  
  const btn = document.createElement('button');
  btn.id = 'phoenix-extract-btn';
  btn.innerHTML = '📤';
  btn.title = 'Extract conversation to memory';
  btn.style.cssText = `
    position: fixed;
    bottom: 150px;
    right: 20px;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: #252540;
    color: white;
    border: 2px solid #667eea;
    cursor: pointer;
    font-size: 18px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    z-index: 10000;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  `;
  
  btn.addEventListener('mouseenter', () => {
    btn.style.transform = 'scale(1.1)';
    btn.style.background = '#667eea';
  });
  
  btn.addEventListener('mouseleave', () => {
    btn.style.transform = 'scale(1)';
    btn.style.background = '#252540';
  });
  
  btn.addEventListener('click', extractConversation);
  
  document.body.appendChild(btn);
}

async function extractConversation() {
  const site = detectSite();
  const btn = document.getElementById('phoenix-extract-btn');
  
  if (btn) {
    btn.innerHTML = '⏳';
    btn.style.pointerEvents = 'none';
  }
  
  try {
    const conversation = extractConversationContent(site);
    
    if (!conversation.text || conversation.messages.length === 0) {
      showNotification('No conversation found to extract', 'error');
      return;
    }
    
    const response = await fetch(`${ROUTER_URL}/api/profile/demo_user/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: `conv_${Date.now()}`,
        conversation_text: conversation.text,
        messages: conversation.messages,
        user_id: 'demo_user'
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      showExtractionResult(data);
      
      // Track extraction
      chrome.storage.local.get(['extractCount'], (result) => {
        chrome.storage.local.set({ 
          extractCount: (result.extractCount || 0) + 1 
        });
      });
    } else {
      showNotification('Extraction failed: ' + (data.message || 'Unknown error'), 'error');
    }
  } catch (error) {
    console.error('Phoenix: Extraction failed:', error);
    showNotification('Failed to connect to Phoenix Router', 'error');
  } finally {
    if (btn) {
      btn.innerHTML = '📤';
      btn.style.pointerEvents = 'auto';
    }
  }
}

function extractConversationContent(site) {
  const messages = [];
  let text = '';
  
  try {
    if (site === 'chatgpt') {
      const messageElements = document.querySelectorAll('[data-message-author-role]');
      messageElements.forEach(el => {
        const role = el.getAttribute('data-message-author-role');
        const contentEl = el.querySelector('.markdown') || el;
        const content = contentEl.textContent || contentEl.innerText;
        if (content && content.trim()) {
          messages.push({ role, content: content.trim() });
          text += `${role === 'user' ? 'User' : 'Assistant'}: ${content.trim()}\n\n`;
        }
      });
    } else if (site === 'claude') {
      const turns = document.querySelectorAll('[data-testid*="turn"]');
      turns.forEach(el => {
        const isHuman = el.getAttribute('data-testid')?.includes('human');
        const content = el.textContent || el.innerText;
        if (content && content.trim()) {
          messages.push({ role: isHuman ? 'user' : 'assistant', content: content.trim() });
          text += `${isHuman ? 'User' : 'Assistant'}: ${content.trim()}\n\n`;
        }
      });
    } else if (site === 'gemini') {
      const containers = document.querySelectorAll('message-content');
      containers.forEach(el => {
        const content = el.textContent || el.innerText;
        if (content && content.trim()) {
          messages.push({ role: 'user', content: content.trim() });
          text += `Message: ${content.trim()}\n\n`;
        }
      });
    }
  } catch (error) {
    console.error('Phoenix: Error extracting conversation', error);
  }
  
  return { text: text.trim(), messages };
}

// ============================================
// CONTEXT CHIP UI
// ============================================

function showContextChip(contextPack) {
  let chip = document.getElementById('phoenix-context-chip');
  
  if (!chip) {
    chip = document.createElement('div');
    chip.id = 'phoenix-context-chip';
    chip.innerHTML = `
      <style>
        #phoenix-context-chip {
          position: fixed;
          bottom: 210px;
          right: 20px;
          z-index: 10000;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .phoenix-chip-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 14px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border-radius: 12px;
          cursor: pointer;
          box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
          font-size: 13px;
          font-weight: 500;
        }
        .phoenix-chip-badge {
          background: rgba(255,255,255,0.2);
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 11px;
        }
        .phoenix-chip-content {
          display: none;
          margin-top: 8px;
          background: #1a1a2e;
          border-radius: 12px;
          padding: 12px;
          max-width: 300px;
          max-height: 250px;
          overflow-y: auto;
          box-shadow: 0 4px 20px rgba(0,0,0,0.4);
          color: #e0e0e0;
          font-size: 12px;
        }
        .phoenix-chip-content.show {
          display: block;
        }
        .phoenix-card-item {
          background: #252540;
          padding: 8px 10px;
          border-radius: 6px;
          margin-bottom: 6px;
          border-left: 3px solid #667eea;
        }
        .phoenix-card-type {
          font-size: 9px;
          text-transform: uppercase;
          color: #888;
        }
        .phoenix-card-text {
          color: #fff;
          margin-top: 4px;
          line-height: 1.3;
        }
      </style>
      <div class="phoenix-chip-header" id="phoenix-chip-toggle">
        <span>🔥</span>
        <span>Context Added</span>
        <span class="phoenix-chip-badge" id="phoenix-chip-count">0</span>
      </div>
      <div class="phoenix-chip-content" id="phoenix-chip-content"></div>
    `;
    document.body.appendChild(chip);
    
    document.getElementById('phoenix-chip-toggle').addEventListener('click', () => {
      document.getElementById('phoenix-chip-content').classList.toggle('show');
    });
  }
  
  // Update content
  document.getElementById('phoenix-chip-count').textContent = contextPack.card_count;
  document.getElementById('phoenix-chip-content').innerHTML = contextPack.used_cards.map(card => `
    <div class="phoenix-card-item">
      <div class="phoenix-card-type">${card.type}</div>
      <div class="phoenix-card-text">${card.text}</div>
    </div>
  `).join('');
  
  // Auto-hide after 10 seconds
  setTimeout(() => {
    const content = document.getElementById('phoenix-chip-content');
    if (content && !content.classList.contains('show')) {
      chip.style.opacity = '0.7';
    }
  }, 10000);
}

// ============================================
// EXTRACTION RESULT MODAL
// ============================================

function showExtractionResult(data) {
  const modal = document.createElement('div');
  modal.id = 'phoenix-extract-modal';
  modal.style.cssText = `
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.8);
    z-index: 10002;
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(4px);
  `;
  
  const categoriesHtml = Object.entries(data.categorized || {}).map(([cat, items]) => {
    if (typeof items === 'object' && !Array.isArray(items)) {
      return `<div style="margin-bottom: 12px;">
        <strong style="color: #667eea;">${cat}:</strong>
        ${Object.entries(items).map(([subCat, subItems]) => 
          `<div style="margin-left: 16px; color: #aaa;">${subCat}: ${Array.isArray(subItems) ? subItems.length : 0} items</div>`
        ).join('')}
      </div>`;
    }
    return `<div style="margin-bottom: 8px;">
      <strong style="color: #667eea;">${cat}:</strong> 
      <span style="color: #aaa;">${Array.isArray(items) ? items.length : 0} items</span>
    </div>`;
  }).join('');
  
  modal.innerHTML = `
    <div style="
      background: #1a1a2e;
      padding: 24px;
      border-radius: 16px;
      max-width: 400px;
      color: #e0e0e0;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    ">
      <h3 style="margin: 0 0 16px 0; color: #fff; display: flex; align-items: center; gap: 8px;">
        ✅ Extraction Complete
      </h3>
      <p style="color: #888; margin-bottom: 16px;">
        Extracted <strong style="color: #667eea;">${data.extracted_items?.length || 0}</strong> items
      </p>
      <div style="background: #252540; padding: 12px; border-radius: 8px; margin-bottom: 16px;">
        ${categoriesHtml || '<div style="color: #666;">No categories</div>'}
      </div>
      <button onclick="document.getElementById('phoenix-extract-modal').remove()" style="
        width: 100%;
        padding: 12px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
      ">Done</button>
    </div>
  `;
  
  document.body.appendChild(modal);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.remove();
  });
}

// ============================================
// NOTIFICATIONS
// ============================================

function showNotification(message, type = 'info') {
  const existing = document.getElementById('phoenix-notification');
  if (existing) existing.remove();
  
  const colors = {
    success: '#00d26a',
    error: '#ff4757',
    info: '#667eea'
  };
  
  const notif = document.createElement('div');
  notif.id = 'phoenix-notification';
  notif.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    background: ${colors[type] || colors.info};
    color: white;
    border-radius: 8px;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 13px;
    z-index: 10003;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    animation: phoenixSlideIn 0.3s ease;
  `;
  notif.textContent = message;
  
  // Add animation style
  if (!document.getElementById('phoenix-animation-styles')) {
    const style = document.createElement('style');
    style.id = 'phoenix-animation-styles';
    style.textContent = `
      @keyframes phoenixSlideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
    `;
    document.head.appendChild(style);
  }
  
  document.body.appendChild(notif);
  setTimeout(() => notif.remove(), 3000);
}

// ============================================
// INITIALIZATION
// ============================================

function initialize() {
  const site = detectSite();
  if (!site) {
    console.log('Phoenix: Unsupported site');
    return;
  }
  
  console.log('Phoenix Protocol initialized for:', site);
  
  // Load settings
  chrome.storage.sync.get(['phoenixEnabled', 'currentPersona'], (result) => {
    phoenixEnabled = result.phoenixEnabled !== false;
    currentPersona = result.currentPersona || 'Personal';
  });
  
  // Create UI elements after page settles
  setTimeout(() => {
    createEnhanceButton();
    createExtractButton();
  }, 2000);
}

// Initialize
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}

// Re-create buttons on SPA navigation
const observer = new MutationObserver(() => {
  if (!document.getElementById('phoenix-enhance-btn')) {
    createEnhanceButton();
  }
  if (!document.getElementById('phoenix-extract-btn')) {
    createExtractButton();
  }
});
observer.observe(document.body, { childList: true, subtree: true });

// Listen for settings changes
chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName === 'sync') {
    if (changes.phoenixEnabled) phoenixEnabled = changes.phoenixEnabled.newValue;
    if (changes.currentPersona) currentPersona = changes.currentPersona.newValue;
  }
});
