// src/lib/platformLock.js
//
// Tiny pub-sub so the axios response interceptor (a plain module, no React
// context) can tell AppContext "the platform just got locked" the instant a
// 423 comes back mid-session, instead of waiting for the next poll.

export const PLATFORM_LOCKED_EVENT = "jamiikazini:platform-locked";

export function notifyPlatformLocked(message) {
  window.dispatchEvent(new CustomEvent(PLATFORM_LOCKED_EVENT, { detail: { message } }));
}
