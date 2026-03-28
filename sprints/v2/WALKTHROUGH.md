# Sprint v2 — Walkthrough

## Summary

Sprint v2 implemented account-based workflows for the Research Notebook app: signup, login, logout, route protection, and user-scoped saved analysis history. It added persistent storage with SQLModel, guarded APIs and pages with session-cookie authentication, and connected the existing notebook generation flow to per-user history records. The sprint also ended with local-run stabilization fixes so frontend auth calls proxy correctly to the backend and signup/login work reliably in local development.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│ Browser (Next.js 14 App Router)                                 │
│                                                                  │
│ Public pages:  /  /signup  /login                               │
│ Protected:     /upload  /processing  /history  /history/[id]    │
│                                                                  │
│ Auth/UI calls: /api/auth/*  /api/history/*  /api/generate-*     │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                │ HTTP + cookie session
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│ Next.js runtime (frontend server)                                │
│                                                                  │
│ middleware.ts checks `session` cookie on protected routes        │
│ next.config.js rewrites /api/* -> FastAPI backend               │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│ FastAPI backend                                                   │
│                                                                  │
│ Auth:   POST /api/auth/signup|login|logout                       │
│ Guard:  get_current_user(), get_current_user_optional()          │
│ History: GET /api/history, GET /api/history/{id}                │
│ Notebook: POST /api/generate-notebook (persists when authed)    │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│ SQLite via SQLModel                                               │
│                                                                  │
│ user, usersession, analysishistory                               │
│ indexes: user.email, analysis.user_id, timestamp indexes         │
└──────────────────────────────────────────────────────────────────┘
```

## Files Created/Modified

### backend/db.py
**Purpose**: Initializes the database, owns engine/session lifecycle, and provides FastAPI DB dependency.

**Key Functions/Components**:
- `init_db()` — creates engine and runs `SQLModel.metadata.create_all()`
- `get_session_factory()` — builds sessionmaker
- `get_db()` — request-scoped DB session dependency
- `set_engine()` — wires global engine/session factory at startup

**How it works**:
The backend startup (`lifespan`) calls `init_db()` and `set_engine()` so every request can consume `get_db()`. A key stabilization fix was applied: `sessionmaker(..., class_=Session)` now returns SQLModel sessions, ensuring `db.exec(...)` works in runtime routes exactly as it does in tests.

```python
from sqlmodel import SQLModel, Session, create_engine

return sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)
```

### backend/models.py
**Purpose**: Defines persistence schema for users, sessions, and saved analyses.

**Key Functions/Components**:
- `User` — unique email, hashed password, profile metadata
- `UserSession` — persisted session token per user
- `AnalysisHistory` — one row per completed authenticated analysis

**How it works**:
Relationships (`back_populates`) link users to many sessions and many analyses. Timestamp columns use UTC defaults. `AnalysisHistory.user_id` and `created_at` are indexed for fast user timeline retrieval.

### backend/auth.py
**Purpose**: Handles password hashing/verification and auth dependencies.

**Key Functions/Components**:
- `hash_password()` and `verify_password()` (bcrypt)
- `generate_session_token()`
- `get_current_user()` and `get_current_user_optional()`
- request/response models for auth and history responses

**How it works**:
Passwords are hashed with bcrypt rounds configured at 12, with explicit truncation guard for bcrypt’s 72-byte behavior. Session tokens are random secure hex values, stored server-side in `usersession`, and transported in HTTP-only cookies.

### backend/main.py
**Purpose**: API surface and app orchestration for auth, history, and notebook generation.

**Key Functions/Components**:
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/history`
- `GET /api/history/{id}`
- `POST /api/generate-notebook` (persist-on-auth)

**How it works**:
Signup validates password/email constraints and unique email. Login verifies password and sets `session` cookie. History endpoints require authenticated user and enforce ownership for detail reads. Notebook generation can run for anonymous users, but persists `AnalysisHistory` only when auth context exists.

```python
response.set_cookie(
    key="session",
    value=access_token,
    httponly=True,
    secure=False,
    samesite="lax",
)
```

### frontend/next.config.js
**Purpose**: Frontend runtime configuration.

**Key Functions/Components**:
- `rewrites()` for API proxying to backend

**How it works**:
A post-sprint local deployment fix added rewrites so frontend calls to `/api/auth/*`, `/api/history/*`, `/api/extract-text`, `/api/generate-notebook`, and demo paper routes are forwarded to the backend service URL. This removed local 404s from auth requests made on port 3000.

```javascript
{
  source: '/api/auth/:path*',
  destination: `${backendUrl}/api/auth/:path*`,
}
```

### frontend/middleware.ts
**Purpose**: Route-level protection in Next.js.

**Key Functions/Components**:
- `middleware()` route gate
- `config.matcher` for paths to evaluate

**How it works**:
For `/upload`, `/processing`, and `/history*`, middleware checks for `session` cookie. If absent, user is redirected to `/login?from=<pathname>` so the intended path is preserved and can be restored after successful login.

### frontend/lib/session.ts
**Purpose**: Browser-side session and helper state.

**Key Functions/Components**:
- API key helpers (`saveApiKey`, `loadApiKey`, TTL)
- auth helpers (`saveAuthUser`, `loadAuthUser`, `isUserAuthenticated`)
- `CSRF_HEADER`

**How it works**:
App-level auth state is kept in `sessionStorage` for UI decisions, while the source of truth for protected backend access is the HTTP-only `session` cookie. The helper layer keeps front-end checks fast and predictable.

### frontend/app/signup/page.tsx
**Purpose**: New account creation UI.

**Key Functions/Components**:
- `validateForm()`
- `handleSignup()`

**How it works**:
The form validates required inputs and password confirmation before calling signup API. A stabilization update disabled native browser validation (`noValidate`) and added explicit regex email validation so users receive clear application-level errors instead of browser-specific pattern messages.

### frontend/app/login/page.tsx
**Purpose**: Login UI and redirect entrypoint for protected routes.

**Key Functions/Components**:
- `validateForm()`
- `handleLogin()`

**How it works**:
Login sends credentials with `credentials: 'include'` so cookies are set and maintained. It also displays a signup success hint via `?from=signup`. Like signup, it now uses explicit email validation and `noValidate` for consistent error messaging.

### frontend/app/history/page.tsx
**Purpose**: User’s history timeline view.

**Key Functions/Components**:
- auth check and redirect
- history fetch + loading/empty/error states

**How it works**:
On mount, page verifies local auth state, then calls `/api/history` with cookies included. The backend returns user-only records in reverse chronological order; each card links to the detail page.

### frontend/app/history/[id]/page.tsx
**Purpose**: Detail page for a single analysis record.

**Key Functions/Components**:
- route param driven fetch
- ownership-aware error handling
- notebook download trigger

**How it works**:
Uses dynamic route id to fetch detail from `/api/history/{id}`. Backend enforces resource ownership; frontend handles 401/403/404 responses and renders contextual user feedback.

### tests/integration/test_auth_signup.py
**Purpose**: Verifies signup behavior and security constraints.

**Key Functions/Components**:
- user creation
- duplicate rejection
- password hashing assertions
- response shape assertions

**How it works**:
Tests ensure no plaintext password persists, duplicate emails fail, and signup returns safe user payload.

### tests/integration/test_auth_login.py
**Purpose**: Verifies login/logout and session cookie behavior.

**Key Functions/Components**:
- valid login sets cookie
- invalid credential handling
- logout clears cookie/session

**How it works**:
Covers both happy and failure paths, asserting correct status codes and cookie/session lifecycle.

### tests/integration/test_auth_guard.py
**Purpose**: Verifies protected endpoint behavior through auth dependency.

**Key Functions/Components**:
- 401 without session
- valid session resolves user
- invalid token rejection

**How it works**:
Exercises dependency injection and token lookup paths to prove route guards enforce authentication correctly.

### tests/integration/test_history_api.py
**Purpose**: Verifies history list/detail APIs and ownership controls.

**Key Functions/Components**:
- auth required checks
- per-user filtering
- reverse chronology
- 403 on cross-user access

**How it works**:
Ensures users only see their own analyses and cannot retrieve records belonging to others.

### tests/integration/test_auth_history.py
**Purpose**: End-to-end backend smoke flow for auth + persistence.

**Key Functions/Components**:
- complete flow test: signup -> login -> analyze -> history -> logout
- invalid credentials scenarios
- session persistence across requests

**How it works**:
This suite validates the core v2 user journey as an integrated contract.

### frontend/tests/e2e/auth-flow.spec.ts
**Purpose**: Browser-level route/auth behavior verification.

**Key Functions/Components**:
- protected route redirect checks
- auth page navigation assertions
- URL parameter flow assertions

**How it works**:
Post-sprint fix replaced fragile URL glob string assertions with regex URL assertions, eliminating false negatives and stabilizing local E2E runs.

## Data Flow

1. User signs up on `/signup` and frontend posts to `/api/auth/signup`.
2. Next rewrite proxies request to backend auth endpoint.
3. Backend creates user with bcrypt-hashed password and returns user payload.
4. User logs in via `/login`; backend validates credentials and sets `session` cookie.
5. Middleware allows protected routes only when cookie exists; otherwise redirects to login with `from` parameter.
6. Authenticated notebook generation writes `AnalysisHistory` row.
7. `/history` calls backend history API and renders user-scoped records.
8. `/history/[id]` fetches detail and allows notebook download for owner only.
9. Logout removes persisted session and clears cookie, restoring unauthenticated behavior.

## Test Coverage

- Unit: 0 explicit new unit-only suites in this sprint.
- Integration: 25+ auth/history-focused tests for tasks 5-10, plus earlier v2 foundation tests for DB/models/schema/signup.
- E2E: 12 Playwright tests in auth-flow suite (11 passing, 1 skipped in latest local run), plus additional v2 page-level E2E coverage from earlier tasks.

## Security Measures

- Bcrypt password hashing with explicit truncation-aware handling.
- HTTP-only cookie sessions for auth state transport.
- Backend auth guard dependencies for protected APIs.
- Ownership checks on history detail endpoints.
- CSRF-style request header checks on mutating requests.
- Protected frontend routes via middleware redirect logic.
- Email uniqueness and schema validation at API boundary.

## Known Limitations

- Session tokens are persisted but do not currently enforce explicit expiration windows.
- No password reset, email verification, MFA, or account lockout yet.
- No login/signup rate limiting in current implementation.
- SQLite remains the local persistence store and is not intended for high-concurrency production scale.
- Some E2E coverage remains skipped or pending depending on backend/live setup assumptions.

## What's Next

1. Add token expiration and rotation plus stronger session management.
2. Add auth abuse protections (rate limiting and lockout strategy).
3. Implement account recovery and email verification.
4. Expand history UX with filtering, search, and pagination.
5. Add deployment-grade config separation for local/dev/prod and stronger observability.
6. Continue E2E hardening with fully non-skipped CI auth/history flows.
