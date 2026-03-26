# Sprint v2 — PRD: Authentication + Saved Analysis History

## Sprint Overview
Sprint v2 adds account-based workflows so users can securely sign in and keep their work. Researchers will be able to view and revisit previous paper analyses and generated notebook artifacts from a personal history page, instead of losing results when a session ends.

## Goals
- Users can sign up, sign in, and sign out with secure session handling.
- Authenticated routes are protected and redirect unauthenticated users.
- Each completed analysis is saved as a history record tied to the user.
- Users can view a chronological history list with key metadata.
- Users can open a saved history item and re-download its generated notebook.

## User Stories
- As a researcher, I want to create an account, so that my analysis work is associated with me.
- As a returning user, I want to see my past analyses, so that I can continue previous work without re-uploading everything.
- As a user, I want protected pages to require login, so that my saved research stays private.
- As a user, I want to open a history item and download its notebook again, so that I can quickly reuse prior outputs.

## Technical Architecture
- **Frontend**: Next.js 14 (App Router), TypeScript, existing Tailwind UI.
- **Backend**: FastAPI + SQLModel/SQLAlchemy-compatible persistence layer.
- **Auth**: Session cookie auth using signed tokens with password hashing (bcrypt/argon2).
- **Database**: SQLite for v2 local/dev persistence with migration support (Alembic or equivalent).

Component Diagram (ASCII):

```
┌────────────────────────────────────────────────────────────────┐
│ Next.js Frontend                                               │
│                                                                │
│  /login  /signup  /history  /history/[id]                      │
│        │         │         │                                   │
│        └─────────┴─────────┴─────┐                             │
└────────────────────────────────────┼────────────────────────────┘
                                     │ HTTPS (cookie session)
                                     ▼
┌────────────────────────────────────────────────────────────────┐
│ FastAPI Backend                                                 │
│                                                                │
│  Auth API: /api/auth/signup /api/auth/login /api/auth/logout  │
│  History API: /api/history, /api/history/{id}                  │
│        │                           │                            │
│        └───────────────┬───────────┘                            │
│                        ▼                                        │
│            SQLite (users, sessions, analyses, notebooks)       │
└────────────────────────────────────────────────────────────────┘
```

Data Flow:
1. User signs up or logs in from frontend auth pages.
2. Backend validates credentials, returns secure session cookie.
3. Existing analyze/generate flow completes.
4. Backend persists analysis summary and notebook artifact metadata for the logged-in user.
5. Frontend history page requests `/api/history` and renders saved items.
6. User opens a detail page to re-download notebook via protected endpoint.

## Out of Scope
- OAuth providers (Google, GitHub, Microsoft).
- Team/shared workspaces and collaboration.
- Cross-device sync beyond account-bound persistence.
- Full-text search/filtering across history.
- Advanced security hardening (MFA, risk detection, SSO).

## Dependencies
- Sprint v1 backend analysis and notebook generation endpoints.
- Existing frontend upload/processing flow from v1.
- New database schema and migration setup introduced in v2.
- Password hashing and signed session libraries added to backend dependencies.
