# Sprint v1 — Walkthrough

## Summary
Sprint v1 established the MVP foundation for the Research Paper → Jupyter Notebook Generator by delivering a working Next.js frontend, FastAPI backend, containerized local development setup, and health-check verification tests. In addition to Task 1 infrastructure, the sprint also includes significant backend capabilities beyond the initial task checklist: PDF extraction, AI-powered paper analysis (Gemini), notebook generation scaffolding, basic in-memory metrics, and CSRF hardening middleware.

The result is a runnable end-to-end scaffold where core services boot successfully on expected ports, expose health endpoints, and provide the first production-shaped API surface for text extraction, analysis, and notebook generation workflows.

## Architecture Overview

┌─────────────────────────────────────────────────────────────────────┐
│ Browser / Next.js 14 Frontend (localhost:3000)                     │
│                                                                     │
│  Landing UI (ARC-style)   Health Route: /api/health                │
│          │                             │                            │
│          └─────────────────────────────┴──────────────┐             │
└────────────────────────────────────────────────────────┼─────────────┘
                                                         │
                                              HTTP (local dev)
                                                         │
┌────────────────────────────────────────────────────────▼─────────────┐
│ FastAPI Backend (localhost:8000)                                     │
│                                                                     │
│  /health, /                     /api/extract-text                   │
│      │                           │                                  │
│      │                           ├─ file validation (type/size/magic)
│      │                           └─ PDF parse (pdfplumber → pypdf)  │
│      │                                                              │
│  /api/analyze-paper                                              │
│      ├─ optional SSE stream                                       │
│      └─ Gemini structured JSON analysis                           │
│                                                                     │
│  /api/metrics + CSRF middleware + notebook generation helpers        │
└─────────────────────────────────────────────────────────────────────┘

## Files Created/Modified

### backend/main.py

**Purpose**: Implements the main FastAPI application, including health endpoints, PDF extraction, AI analysis, notebook-generation helpers, metrics, CORS, and CSRF middleware.

**Key Functions/Components**:
- `app` — FastAPI app configured with lifespan, middleware, and routes
- `_Metrics` — thread-safe in-memory counters for operational telemetry
- `extract_text()` — validates PDF upload and extracts per-page text
- `analyze_paper()` — runs structured Gemini analysis (sync or SSE streaming)
- `_build_notebook()` — builds Jupyter notebook cell structure from analysis data

**How it works**:
This file acts as the backend composition root. On startup, it initializes logging, CORS, lifecycle hooks, and middleware. A production-only CSRF guard requires the `X-Requested-With` header for mutation requests as defense-in-depth against cross-site form submission. It also exposes `/api/metrics` so operators can inspect key counters like upload failures, analysis success rate, and rate-limit hits.

The extraction pipeline is defensive and staged. `extract_text()` checks filename extension, file size (`10 MB` cap), file emptiness, and PDF magic bytes before parsing. Extraction tries `pdfplumber` first, then falls back to `pypdf` if needed. This dual-parser strategy improves resilience across differently structured PDFs while surfacing precise HTTP errors (`400`, `413`, `422`) when validation or parsing fails.

Analysis uses a strict JSON prompt contract and calls Gemini via `google.genai`. The backend truncates very large inputs to stay within model context limits and can stream partial tokens using SSE when `stream=true`. If Gemini rejects credentials or throttles requests, the code maps those errors to appropriate user-facing statuses (`401`, `429`) and increments dedicated metrics counters.

```python
if len(data) > MAX_PDF_SIZE:
    _metrics.inc("upload_errors")
    raise HTTPException(
        status_code=413,
        detail=f"File exceeds 10 MB limit ({len(data) / 1024 / 1024:.1f} MB).",
    )

if not data.startswith(b"%PDF"):
    _metrics.inc("upload_errors")
    raise HTTPException(status_code=400, detail="File does not appear to be a valid PDF.")
```

```python
if stream:
    return StreamingResponse(
        _stream_gemini(request.api_key, request.text),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

### backend/Dockerfile

**Purpose**: Defines the backend container image and runtime for local orchestration.

**Key Functions/Components**:
- Python runtime containerization for FastAPI service
- Uvicorn execution target (`main:app`)

**How it works**:
The backend Dockerfile provides reproducible runtime packaging so the service can be launched consistently through Compose. This removes local machine drift as a source of startup failures and aligns with sprint goals around fast developer onboarding.

### backend/__init__.py

**Purpose**: Marks `backend` as a Python package for imports and test discovery.

**Key Functions/Components**:
- Package initialization marker

**How it works**:
Although minimal, this file is required to allow module imports like `from backend.main import app` in integration tests and tooling. Without it, package-relative imports can become brittle depending on runner context.

### backend/pyproject.toml

**Purpose**: Declares backend package metadata, Python requirements, and dependencies.

**Key Functions/Components**:
- Runtime deps: FastAPI, Uvicorn, Pydantic, multipart parsing, PDF libs, notebook format lib
- Test deps: pytest, pytest-asyncio, httpx
- Dev deps: black, ruff, mypy

**How it works**:
This file formalizes backend dependency management and toolchain expectations. It enables deterministic environment setup and validates the project’s chosen stack for API serving, parsing, notebook creation, and testing.

### frontend/app/page.tsx

**Purpose**: Renders the landing page with ARC-inspired visual design and CTA to begin upload flow.

**Key Functions/Components**:
- `Home` — top-level client component for marketing/entry experience
- Feature cards and call-to-action links

**How it works**:
The page uses a centered hero layout with gradient typography and subtle blurred background shapes to establish the product narrative. It introduces three value propositions (PDF Upload, AI Analysis, Notebooks) and routes users to `/upload` via a primary button. This implements the planned visual-first experience from the PRD and gives users an immediate next step.

```tsx
<Link
  href="/upload"
  className="inline-flex items-center justify-center px-8 py-4 bg-gradient-to-r from-arc-purple to-arc-accent ..."
  data-testid="get-started-button"
>
  Get Started
  <span className="ml-2">→</span>
</Link>
```

### frontend/app/globals.css

**Purpose**: Defines global CSS baseline and Tailwind layer imports for the frontend.

**Key Functions/Components**:
- Tailwind `base/components/utilities` inclusion
- Global reset (`margin`, `padding`, `box-sizing`)
- Font smoothing and code font defaults

**How it works**:
This stylesheet creates a predictable rendering baseline before component-level styles apply. It reduces browser inconsistencies and ensures Tailwind utility classes behave consistently across pages.

### frontend/app/layout.tsx

**Purpose**: Provides app-wide HTML shell and metadata for Next.js App Router.

**Key Functions/Components**:
- `metadata` — page title/description
- `RootLayout` — wraps all routes and applies global body classes

**How it works**:
The root layout centralizes site metadata and applies shared theme classes (`bg-arc-dark`, `text-arc-light`) so all pages inherit base branding automatically. This avoids per-page duplication and keeps theme alignment consistent.

### frontend/app/api/health/route.ts

**Purpose**: Implements frontend service health endpoint for infrastructure verification.

**Key Functions/Components**:
- `GET()` — returns JSON status, service name, and timestamp

**How it works**:
This lightweight route provides a reliable liveness signal for the frontend process. It is used by tests and local ops checks to confirm the Next.js runtime is reachable and responding.

### frontend/Dockerfile

**Purpose**: Defines frontend container image and execution context for local development.

**Key Functions/Components**:
- Node-based image setup for Next.js
- Containerized `npm run dev` runtime under Compose

**How it works**:
Containerizing the frontend ensures consistent Node runtime behavior across environments and coordinates startup with the backend in a single command flow.

### frontend/next.config.js

**Purpose**: Holds Next.js framework configuration for the frontend app.

**Key Functions/Components**:
- Baseline framework config object

**How it works**:
Even when minimal, this file gives an explicit place for future platform-level tuning (routing, build flags, image domains, etc.) without refactoring project structure later.

### frontend/postcss.config.js

**Purpose**: Configures PostCSS pipeline required by Tailwind CSS.

**Key Functions/Components**:
- Tailwind and autoprefixer plugin wiring

**How it works**:
The file ensures utility classes are transformed correctly and CSS output includes browser-compatibility prefixes where needed.

### frontend/tailwind.config.ts

**Purpose**: Defines Tailwind scanning paths and custom ARC-themed design tokens.

**Key Functions/Components**:
- `content` globs for class extraction
- Custom color palette (`arc-dark`, `arc-purple`, etc.)
- Custom sans font stack

**How it works**:
Tailwind only generates classes it finds in configured source files. This config points at app/component directories and extends theme colors to encode visual language directly into reusable tokens.

```ts
colors: {
  'arc-dark': '#0a0a0a',
  'arc-gray': '#1a1a1a',
  'arc-light': '#f5f5f5',
  'arc-purple': '#a855f7',
  'arc-accent': '#ec4899',
}
```

### frontend/tsconfig.json

**Purpose**: Defines TypeScript compiler behavior for the frontend codebase.

**Key Functions/Components**:
- Type-checking and module resolution settings

**How it works**:
This file controls TS analysis quality and build-time compatibility for Next.js. It prevents configuration drift and keeps editor diagnostics aligned with CI/build behavior.

### frontend/package.json

**Purpose**: Declares frontend dependencies and scripts for development, build, and testing.

**Key Functions/Components**:
- Scripts: `dev`, `build`, `start`, `test`, `test:e2e`
- Runtime deps: Next.js + React
- Dev deps: Tailwind, TypeScript, Vitest, Playwright

**How it works**:
This manifest formalizes the frontend toolchain and introduces both unit-style (`vitest`) and browser E2E (`playwright`) test pathways, even if full feature tests are planned for later tasks.

### frontend/package-lock.json

**Purpose**: Pins exact npm dependency versions for reproducible installs.

**Key Functions/Components**:
- Fully resolved dependency tree

**How it works**:
Locking versions ensures all developers and CI agents install matching packages, reducing “works on my machine” issues.

### tests/__init__.py

**Purpose**: Marks the test directory as a package for Python test discovery/import stability.

**Key Functions/Components**:
- Package marker for test modules

**How it works**:
This file supports consistent import behavior when running pytest from different working directories or tooling contexts.

### tests/integration/test_health_checks.py

**Purpose**: Verifies basic availability and expected payload shape of frontend/backend health endpoints.

**Key Functions/Components**:
- `test_frontend_health_check()` — calls frontend route handler directly
- `test_backend_health_check()` — checks backend `/health`
- `test_backend_root_endpoint()` — checks backend `/`

**How it works**:
The tests provide the first integration confidence layer for Task 1 acceptance criteria. They validate that both services start and return expected semantic identifiers (service names, status, root message), not just status codes.

```python
client = TestClient(app)
response = client.get("/health")
assert response.status_code == 200
assert response.json()["status"] == "ok"
assert "research-notebook-backend" in response.json()["service"]
```

### docker-compose.yml

**Purpose**: Orchestrates frontend and backend containers for local development.

**Key Functions/Components**:
- Service definitions for `frontend` and `backend`
- Port mapping (`3000`, `8000`)
- Source-code volume mounts for hot reload
- Inter-service dependency (`frontend` depends on `backend`)

**How it works**:
Compose acts as the local runtime control plane. It builds both images, mounts source for iterative development, forwards required ports, and starts services with the expected dev commands. This aligns directly with the PRD local deployment objective.

### sprints/v1/PRD.md

**Purpose**: Defines the sprint’s product intent, architecture, goals, and out-of-scope boundaries.

**Key Functions/Components**:
- MVP goals and user stories
- Proposed architecture diagram
- Dependency and deployment strategy

**How it works**:
The PRD provides the target state used to prioritize implementation. It is the reference for judging completion and identifying scope gaps (for example, upload UI and full E2E flow not yet complete).

### sprints/v1/TASKS.md

**Purpose**: Tracks task-level execution status against PRD goals.

**Key Functions/Components**:
- Prioritized tasks (`P0`, `P1`, `P2`)
- Acceptance criteria and intended files
- Completion notes

**How it works**:
The task sheet serves as sprint execution ledger. It currently marks Task 1 complete and leaves most subsequent tasks open, which is consistent with a foundation-first delivery approach.

## Data Flow
1. User opens frontend landing page at `localhost:3000` and navigates toward upload flow.
2. Frontend health endpoint (`/api/health`) can be queried to verify UI service availability.
3. Client submits PDF + API key to backend `/api/extract-text`.
4. Backend validates extension, size, non-empty bytes, and `%PDF` signature.
5. Backend extracts per-page text (`pdfplumber`, fallback `pypdf`) and returns structured extraction payload.
6. Client sends extracted text to `/api/analyze-paper` with API key.
7. Backend calls Gemini with strict JSON schema prompt; response returns structured paper analysis fields.
8. (Current backend capability) Analysis object can feed notebook-building helpers to construct `.ipynb` content.
9. Metrics endpoint (`/api/metrics`) exposes operational counters for monitoring attempts/errors/conversions.

## Test Coverage
- Unit: 0 tests explicitly identified in sprint commit set.
- Integration: 3 tests in [tests/integration/test_health_checks.py](tests/integration/test_health_checks.py) — frontend health route, backend health route, backend root route.
- E2E: 0 tests executed for sprint deliverables in this commit set (framework tooling exists but sprint evidence shows health-focused integration checks only).

## Security Measures
- CORS restricted to local frontend origins (`http://localhost:3000`, `http://127.0.0.1:3000`).
- Production-only CSRF mitigation requiring `X-Requested-With` header on mutating requests.
- Upload hardening with file extension validation, max-size enforcement, and PDF magic-byte checks.
- Error code mapping for invalid API key (`401`) and provider rate limit (`429`) to avoid ambiguous failures.
- In-memory counters track security-relevant events (invalid key attempts, rate-limit hits, upload errors).

## Known Limitations
- `TASKS.md` marks only Task 1 complete; many PRD features (upload UI, full generation flow, progress UX) remain incomplete.
- Backend uses Gemini (`google.genai`) while PRD and task text mention OpenAI/GPT-4o, creating model/provider drift in documentation vs implementation.
- API key is currently sent with extraction endpoint even though extraction does not use model inference, increasing payload sensitivity unnecessarily.
- Notebook generation helper logic exists but end-to-end “generate and download notebook” frontend route is not fully wired in the sprint-tracked files.
- Metrics are in-memory only; counters reset on process restart and are not suitable for production observability.
- No persistent file storage, authentication, or rate limiting beyond provider-side throttling handling.

## What's Next
1. Complete P0 UX pipeline: upload form, API key form UX, and `/upload` page to drive actual extract/analyze/generate flow.
2. Align product and implementation model strategy: either migrate to OpenAI/GPT-4o per PRD or update PRD/tasks to Gemini as source of truth.
3. Implement notebook delivery path end-to-end: generation endpoint, downloadable `.ipynb`, and Colab link creation UI.
4. Add robust validation and security hardening: schema validation, stronger input sanitization, explicit server-side rate limiting.
5. Expand test suite to cover extraction edge cases, analysis error handling, notebook generation correctness, and user journey E2E.
6. Add durable observability (structured logs + persisted metrics) before production-oriented deployment milestones.
