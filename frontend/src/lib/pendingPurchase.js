// src/lib/pendingPurchase.js
//
// Reusable "wallet-gated action" pattern: any purchase/charge anywhere in
// the app that's paid for out of JamiiWallet balance can use
// runWalletGatedRequest() instead of calling `api` directly. If the
// backend responds 402 (insufficient balance), the intended request is
// stashed in sessionStorage (survives a full page navigation - unlike
// router state - since top-up confirmation is gateway/webhook-driven and
// may involve leaving the app entirely) and the user is sent to
// JamiiWalletPage to top up. JamiiWalletPage's own polling loop checks
// for a stashed pending purchase on every tick and retries it
// automatically once the top-up lands, so the user never has to manually
// come back and re-trigger the original purchase.
//
// The retried request reuses the exact same payload the backend already
// received, so it's the backend's own idempotency-key handling (not
// anything here) that guarantees a resume can never double-charge.

const STORAGE_KEY = "jamiikazini_pending_purchase";

export function stashPendingPurchase({ method = "post", url, data, successPath, successMessageKey, amountNeeded }) {
  try {
    sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ method, url, data, successPath, successMessageKey, amountNeeded, stashedAt: Date.now() })
    );
  } catch (e) {
    // sessionStorage unavailable (private mode, etc.) - resume just won't
    // happen automatically; the user can still retry manually.
    console.warn("Failed to stash pending purchase:", e);
  }
}

export function getPendingPurchase() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

export function clearPendingPurchase() {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch (e) {
    // ignore
  }
}

/**
 * Runs a wallet-gated POST/PUT/etc. If it fails with 402 (insufficient
 * balance), stashes the request and navigates to /jamiiwallet.
 * Returns { ok: true, data } on success, or { ok: false, insufficientBalance: true }
 * after redirecting. Any other error is re-thrown for the caller to handle.
 */
export async function runWalletGatedRequest(api, navigate, request, { successPath, successMessageKey } = {}) {
  try {
    const res = await api.request({ method: request.method || "post", url: request.url, data: request.data });
    clearPendingPurchase();
    return { ok: true, data: res.data };
  } catch (err) {
    if (err.response?.status === 402) {
      stashPendingPurchase({
        ...request,
        successPath,
        successMessageKey,
        amountNeeded: err.response?.data?.amount_needed,
      });
      navigate("/jamiiwallet", { state: { resumePending: true } });
      return { ok: false, insufficientBalance: true };
    }
    throw err;
  }
}
