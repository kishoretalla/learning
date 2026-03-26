# Sprint v2 — Tasks

## Status: Planned

- [x] Task 1: Set up backend persistence and auth dependencies (P0)
  - Acceptance: Backend includes configured DB connection, auth/hash dependencies install cleanly, app boots with no import errors.
  - Files: backend/pyproject.toml, backend/main.py, backend/db.py
  - Completed: 2026-03-26 — Added SQLModel, passlib, bcrypt, python-jose to dependencies. Created backend/db.py with init_db(), get_session_factory(), get_db() dependency injection. Integrated DB initialization into FastAPI lifespan. All 5 tests pass. Semgrep findings relate to pre-existing v1 code (Dockerfile USER, main.py logger). New db.py code is clean.

- [ ] Task 2: Create user and analysis history database models (P0)
  - Acceptance: `User`, `Session` (or equivalent), and `AnalysisHistory` models exist with user-to-history relationship and timestamps.
  - Files: backend/models.py

- [ ] Task 3: Add initial schema migration for auth and history tables (P0)
  - Acceptance: Migration creates all required tables and can be applied on a fresh SQLite database.
  - Files: backend/migrations/* or backend/schema.sql

- [ ] Task 4: Implement signup endpoint with password hashing (P0)
  - Acceptance: `POST /api/auth/signup` creates a user with hashed password and rejects duplicate email.
  - Files: backend/main.py, backend/auth.py

- [ ] Task 5: Implement login/logout endpoints with secure session cookie (P0)
  - Acceptance: `POST /api/auth/login` sets session cookie for valid credentials; `POST /api/auth/logout` clears it.
  - Files: backend/main.py, backend/auth.py

- [ ] Task 6: Add backend auth guard utility for protected routes (P0)
  - Acceptance: Protected endpoints return 401 when no valid session exists and resolve current user when authenticated.
  - Files: backend/auth.py, backend/main.py

- [ ] Task 7: Persist analysis results after successful generation for authenticated users (P1)
  - Acceptance: Completed analysis creates an `AnalysisHistory` row including title, timestamp, and notebook reference.
  - Files: backend/main.py, backend/models.py

- [ ] Task 8: Build frontend auth pages and session helpers (P1)
  - Acceptance: `/signup` and `/login` pages submit successfully and redirect authenticated users to app flow.
  - Files: frontend/app/signup/page.tsx, frontend/app/login/page.tsx, frontend/lib/session.ts

- [ ] Task 9: Build history list and detail pages with notebook re-download action (P1)
  - Acceptance: `/history` shows only current user records in reverse chronological order; detail page opens one record and can trigger notebook download.
  - Files: frontend/app/history/page.tsx, frontend/app/history/[id]/page.tsx, frontend/app/api/history/route.ts

- [ ] Task 10: Protect frontend routes and add basic auth/history smoke tests (P1)
  - Acceptance: Unauthenticated users are redirected from protected pages; tests cover signup/login and history retrieval happy path.
  - Files: frontend/middleware.ts, tests/integration/test_auth_history.py, frontend/tests/e2e/session-management.spec.ts
