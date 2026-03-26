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
  AUTH_USER:         'auth_user',
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

// ── Authenticated User Session ───────────────────────────────────────────────
// User data is stored in sessionStorage only (cleared when tab closes)
// Server-side session is managed via HTTP-only cookie set by /api/auth/login

export interface AuthUser {
  id: number
  email: string
  full_name?: string
}

export function saveAuthUser(user: AuthUser): void {
  sessionStorage.setItem(KEYS.AUTH_USER, JSON.stringify(user))
}

export function loadAuthUser(): AuthUser | null {
  const stored = sessionStorage.getItem(KEYS.AUTH_USER)
  if (!stored) return null
  try {
    return JSON.parse(stored) as AuthUser
  } catch {
    return null
  }
}

export function clearAuthUser(): void {
  sessionStorage.removeItem(KEYS.AUTH_USER)
}

export function isUserAuthenticated(): boolean {
  return loadAuthUser() !== null
}

/**
 * Clear all user-related session data.
 * Call this on logout or when switching users.
 */
export function clearUserSession(): void {
  clearAuthUser()
  // Note: API key session is NOT cleared here since it's independent
  // Call clearSession() to clear everything including API key
}
