// src/lib/jwt.js

// 🎯 Tafsiri token kuwa object (exp, iat, n.k.)
export function parseJwt(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch (e) {
    return null;
  }
}

// 🕒 Rudisha muda uliobaki (kwa sekunde)
export function getRemainingSeconds(token) {
  const decoded = parseJwt(token);
  if (!decoded?.exp) return 0;
  const expiryTime = decoded.exp * 1000;
  return Math.max(0, Math.floor((expiryTime - Date.now()) / 1000));
}

// 🕵️‍♂️ Je access token imebaki ndani ya dakika X?
export function isTokenExpiringSoon(token, minutes = 1) {
  const remaining = getRemainingSeconds(token);
  return remaining <= minutes * 60;
}

// 🧮 Gawanya token kwa vipindi vya dakika 5
export function getTokenStage(token) {
  const decoded = parseJwt(token);
  if (!decoded?.exp || !decoded?.iat) return null;

  const total = (decoded.exp - decoded.iat); // sekunde
  const elapsed = Math.floor(Date.now() / 1000) - decoded.iat;
  const progress = elapsed / total;

  if (progress < 1 / 3) return 1;  // Dakika 0–5
  if (progress < 2 / 3) return 2;  // Dakika 5–10
  if (progress < 1)     return 3;  // Dakika 10–15
  return 4;  // Expired
}