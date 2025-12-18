/**
 * Phoenix Protocol - Background Service Worker
 * 
 * Handles extension lifecycle and communication.
 */

chrome.runtime.onInstalled.addListener(() => {
  console.log('🔥 Phoenix Protocol extension installed');
});

