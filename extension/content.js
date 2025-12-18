/**
 * Phoenix Protocol - Content Script
 * 
 * Detects chat textboxes and intercepts send events to inject context.
 */

const ROUTER_URL = 'http://127.0.0.1:8787';

// Detect which site we're on
function detectSite() {
  if (window.location.hostname.includes('openai.com')) return 'chatgpt';
  if (window.location.hostname.includes('claude.ai')) return 'claude';
  if (window.location.hostname.includes('gemini.google.com')) return 'gemini';
  return null;
}

// Find the textbox (site-specific selectors)
function findTextbox() {
  const site = detectSite();
  if (!site) return null;
  
  // ChatGPT selector
  if (site === 'chatgpt') {
    return document.querySelector('textarea[data-id="root"]') || 
           document.querySelector('textarea');
  }
  
  // Claude selector
  if (site === 'claude') {
    return document.querySelector('div[contenteditable="true"]') ||
           document.querySelector('textarea');
  }
  
  // Gemini selector
  if (site === 'gemini') {
    return document.querySelector('textarea') ||
           document.querySelector('div[contenteditable="true"]');
  }
  
  return null;
}

// Get context pack from router
async function getContextPack(draftPrompt) {
  try {
    const response = await fetch(`${ROUTER_URL}/api/context-pack`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        draft_prompt: draftPrompt,
        site_id: detectSite(),
        persona: 'Personal', // TODO: Get from storage
        sensitivity_mode: 'quiet'
      })
    });
    
    const data = await response.json();
    return data.pack;
  } catch (error) {
    console.error('Failed to get context pack:', error);
    return null;
  }
}

// Inject context into prompt
function injectContext(textbox, contextPack) {
  const originalText = textbox.value || textbox.textContent;
  const finalText = `${contextPack.pack_text}\n\n${originalText}`;
  
  if (textbox.value !== undefined) {
    textbox.value = finalText;
    textbox.dispatchEvent(new Event('input', { bubbles: true }));
  } else {
    textbox.textContent = finalText;
    textbox.dispatchEvent(new Event('input', { bubbles: true }));
  }
  
  // Show UI chip
  showContextChip(contextPack);
}

// Show "Context Used" UI chip
function showContextChip(contextPack) {
  // TODO: Create and inject chip element
  console.log('Context used:', contextPack.used_cards);
}

// Main: Intercept send events
function setupInterception() {
  const textbox = findTextbox();
  if (!textbox) return;
  
  // Listen for Enter key or Send button
  textbox.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      
      const draftPrompt = textbox.value || textbox.textContent;
      const contextPack = await getContextPack(draftPrompt);
      
      if (contextPack) {
        injectContext(textbox, contextPack);
      }
      
      // Trigger send (site-specific)
      // TODO: Find and click send button
    }
  });
}

// Initialize when page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', setupInterception);
} else {
  setupInterception();
}

