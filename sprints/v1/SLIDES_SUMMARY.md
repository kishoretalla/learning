# Sprint v1 — Slide-Friendly Summary

## Slide 1: Sprint Objective
- Build the MVP foundation for Research Paper → Jupyter Notebook generation.
- Prove local architecture, service startup, and basic verification.
- Prepare core APIs for extraction and analysis workflows.

## Slide 2: Delivered This Sprint
- Next.js frontend service (port 3000).
- FastAPI backend service (port 8000).
- Docker Compose local orchestration.
- Frontend + backend health endpoints.
- Integration tests for service availability.
- Initial backend endpoints for:
: PDF extraction
: AI analysis
: metrics
: notebook scaffolding

## Slide 3: Architecture (Current)
```text
Browser (Next.js)
   |
   |  /api/health
   |  user navigation
   v
FastAPI Backend
   |- /health
   |- /api/extract-text
   |- /api/analyze-paper
   |- /api/metrics
   \- notebook generation helpers
```

## Slide 4: Why This Matters
- De-risks project startup and integration complexity early.
- Shortens time-to-feature for upcoming user workflows.
- Establishes tested service contracts between frontend and backend.
- Provides baseline security controls from the beginning.

## Slide 5: Quality Snapshot
- Integration tests: 3
- Unit tests in sprint scope: 0
- E2E tests in sprint scope: 0
- Current confidence: infrastructure health is verified; full product flow not yet validated.

## Slide 6: Security Snapshot
- CORS allowlist for local frontend origins.
- Production-only CSRF header check on mutation routes.
- PDF upload validation (extension, size limit, magic bytes).
- Error handling for invalid API keys and provider rate limits.

## Slide 7: Gaps / Limitations
- Upload-to-download user journey is not complete.
- Real-time progress UX remains pending.
- PRD-provider mismatch (GPT-4o language vs Gemini implementation).
- Metrics are in-memory only (no persistence).

## Slide 8: v2 Priorities
1. Complete end-to-end user workflow (upload → notebook output).
2. Align model strategy and documentation.
3. Add stronger validation and rate limiting.
4. Expand test coverage (functional + E2E).
5. Improve production-readiness and observability.

## Slide 9: One-Line Summary
Sprint v1 delivered a solid technical foundation; v2 should convert it into a fully usable researcher workflow.