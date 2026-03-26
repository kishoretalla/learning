/**
 * Centralised browser-session helpers.
 * All data lives in sessionStorage — cleared when the tab closes.
 * API keys are given a 1-hour TTL so stale credentials don't linger.
 */

export const SESSION_TTL_MS = 60 * 60 * 1000 // 1 hour

const KEYS = {
  API_KEY:           'openai_api_key',
  API_KEY_EXPIRY:    'openai_api_key_expiry',
  EXTRACTION_RESULT: 'extraction_result',
  ANALYSIS_RESULT:   'analysis_result',
} as const

// ── API key ─────────────────────────────────────────────────────────────────

export function saveApiKey(key: string): void {
  sessionStorage.setItem(KEYS.API_KEY, key)
  sessionStorage.setItem(KEYS.API_KEY_EXPIRY, String(Date.now() + SESSION_TTL_MS))
}

export function loadApiKey(): string | null {
  const expiry = sessionStorage.getItem(KEYS.API_KEY_EXPIRY)
  if (expiry && Date.now() > Number(expiry)) {
    clearSession()
    return null
  }
  return sessionStorage.getItem(KEYS.API_KEY)
}

export function removeApiKey(): void {
  sessionStorage.removeItem(KEYS.API_KEY)
  sessionStorage.removeItem(KEYS.API_KEY_EXPIRY)
}

// ── Session lifecycle ────────────────────────────────────────────────────────

export function clearSession(): void {
  Object.values(KEYS).forEach(k => sessionStorage.removeItem(k))
}

export function isSessionActive(): boolean {
  const expiry = sessionStorage.getItem(KEYS.API_KEY_EXPIRY)
  if (!expiry) return false
  return Date.now() <= Number(expiry)
}

export function sessionExpiresAt(): Date | null {
  const expiry = sessionStorage.getItem(KEYS.API_KEY_EXPIRY)
  return expiry ? new Date(Number(expiry)) : null
}

// ── CSRF helper ──────────────────────────────────────────────────────────────
// All mutating fetch calls should include this header so the backend can
// distinguish legitimate browser requests from cross-site form submissions.

export const CSRF_HEADER = { 'X-Requested-With': 'fetch' } as const
