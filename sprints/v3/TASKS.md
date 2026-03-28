# Sprint v3 — Tasks

## Status: Complete

- [x] Task 1: Set up v3 production test/deploy scaffolding (P0)
  - Acceptance: Baseline config files for pytest markers, Playwright output dirs, and CI env vars are present and app still boots.
  - Files: pytest.ini, frontend/playwright.config.ts, README.md
  - Completed: 2026-03-28 — Added pytest lane markers, Playwright output/reporter/video config, CI workflow skeletons, repo hygiene ignores, and README test-lane guidance. Existing backend and Playwright smoke suites remained green.

- [x] Task 2: Add unit tests for `pdf_extractor` module (P0)
  - Acceptance: Unit tests cover happy path, malformed PDFs, empty content, and error handling branches.
  - Files: tests/unit/test_pdf_extractor.py
  - Completed: 2026-03-28 — Extracted PDF helpers into `backend/pdf_extractor.py` and added unit coverage for page metadata, fallback behavior, empty text normalization, and extractor failure handling.

- [x] Task 3: Add unit tests for `arxiv_fetcher` module (P0)
  - Acceptance: Unit tests validate URL parsing, network failure handling, and metadata extraction behavior.
  - Files: tests/unit/test_arxiv_fetcher.py
  - Completed: 2026-03-28 — Added `backend/arxiv_fetcher.py` with arXiv ID normalization, URL builders, Atom metadata parsing, and fetch logic, plus unit tests for valid/invalid inputs and network failure handling.

- [x] Task 4: Add unit tests for `prompt_template` module (P0)
  - Acceptance: Unit tests verify required sections, deterministic formatting, and safety/disclaimer text inclusion.
  - Files: tests/unit/test_prompt_template.py
  - Completed: 2026-03-28 — Extracted prompt construction into `backend/prompt_template.py`, added grounding guidance for missing facts, and covered prompt structure, truncation, and deterministic formatting with unit tests.

- [x] Task 5: Add unit tests for `notebook_generator` module (P0)
  - Acceptance: Unit tests validate notebook structure generation, JSON validity, and section completeness.
  - Files: tests/unit/test_notebook_generator.py
  - Completed: 2026-03-28 — Extracted notebook generation into `backend/notebook_generator.py` and added unit coverage for title generation, algorithm stubs, notebook validity, and markdown section completeness.

- [x] Task 6: Add integration test for `upload-pdf` API with mocked Gemini (P0)
  - Acceptance: Endpoint integration test runs end-to-end with Gemini mocked and verifies response contract.
  - Files: tests/integration/test_upload_pdf_endpoint.py
  - Completed: 2026-03-28 — Added an upload-to-analysis integration flow that exercises PDF extraction and mocked Gemini analysis together and verifies the combined response contract.

- [x] Task 7: Add integration test for `arxiv-url` API with mocked Gemini (P0)
  - Acceptance: Endpoint integration test validates arXiv flow with mocked Gemini and handles invalid URL paths.
  - Files: tests/integration/test_arxiv_url_endpoint.py
  - Completed: 2026-03-28 — Added `/api/arxiv-url` backend flow plus integration coverage for valid arXiv resolution, mocked Gemini analysis, and invalid URL rejection.

- [x] Task 8: Add Playwright E2E full user flow with screenshots (P1)
  - Acceptance: E2E covers enter API key -> enter arXiv URL -> generate -> spinner visible -> download available, with screenshot capture at each step.
  - Files: frontend/tests/e2e/full-user-flow.spec.ts, frontend/tests/screenshots/
  - Completed: 2026-03-28 — Added a browser-level full-flow test covering authenticated arXiv submission, processing state visibility, notebook download readiness, and screenshot capture at each major stage.

- [x] Task 9: Add manual visible-browser real quality validation spec (P1)
  - Acceptance: Script/checklist supports human-entered API key and validates generated notebook for valid JSON, 8 sections, valid Python cells, and safety disclaimer.
  - Files: tests/quality/test_real_attention_paper.md, tests/quality/validate_generated_notebook.py
  - Completed: 2026-03-28 — Added step-by-step manual checklist for arXiv real-paper flow and a Python validator script that checks nbformat v4 validity, 8 required sections, abstract length, Python cell syntax, safety disclaimer, and algorithm stubs. Added `_cell_source()` helper to handle nbformat list-or-string source type. Added `tests/quality/test_validator.py` (6 pytest tests exercising all check paths).

- [x] Task 10: Create GitHub Actions workflow for backend test gate (P0)
  - Acceptance: On push/PR, workflow runs pytest and fails job on any failing test.
  - Files: .github/workflows/backend-tests.yml
  - Completed: 2026-03-28 — Workflow triggers on push to main and all pull_requests; installs backend with dev extras (including google-genai), runs pytest with PYTHONPATH=. and --tb=short.

- [x] Task 11: Create GitHub Actions workflow for frontend Playwright gate (P0)
  - Acceptance: On push/PR, workflow runs Playwright and uploads traces/screenshots as artifacts on failure.
  - Files: .github/workflows/frontend-e2e.yml
  - Completed: 2026-03-28 — Workflow starts backend with uvicorn, waits for /health to respond (up to 60 s), runs all Playwright tests, and uploads playwright-report and test-results as artifacts on any outcome.

- [x] Task 12: Create GitHub Actions workflow for Semgrep + pip-audit gates (P0)
  - Acceptance: On push/PR, workflow runs Semgrep and pip-audit; non-zero findings fail checks.
  - Files: .github/workflows/security.yml
  - Completed: 2026-03-28 — Two-job workflow: semgrep uses the official action with p/security-audit ruleset; pip-audit installs and audits the backend package. Both block merge on findings.

- [x] Task 13: Document branch protection and merge-block requirements (P0)
  - Acceptance: Required checks list is documented and maps to CI workflows so merges are blocked on failures.
  - Files: docs/branch-protection.md
  - Completed: 2026-03-28 — Updated doc with exact GitHub UI check names mapped to workflow files, a table of required secrets, credentials hygiene guidelines (including key rotation and git-filter-repo), and TF_VAR_* notes for Terraform secrets.

- [ ] Task 14: Add production backend Dockerfile and healthcheck (P1)
  - Acceptance: Backend image builds and runs with health endpoint accessible in container runtime.
  - Files: backend/Dockerfile
  - Started: 2026-03-28 — Replaced the dev Dockerfile with a production-oriented backend image and healthcheck; Docker build/runtime validation is still pending because Docker is unavailable in this environment.

- [ ] Task 15: Add production frontend container with nginx serving strategy (P1)
  - Acceptance: Frontend production container builds and serves app behind nginx-compatible setup.
  - Files: frontend/Dockerfile, frontend/nginx.conf
  - Started: 2026-03-28 — Added a standalone Next.js production image fronted by nginx plus supervisor config; runtime validation is still pending because Docker is unavailable in this environment.

- [ ] Task 16: Add docker-compose production-local stack (P1)
  - Acceptance: `docker compose up` starts frontend + backend with correct networking and env wiring.
  - Files: docker-compose.yml, .env.example
  - Started: 2026-03-28 — Reworked root compose and env example toward a production-local stack with healthchecks and service dependencies; container validation is still pending because Docker is unavailable in this environment.

- [ ] Task 17: Add Terraform AWS ECS Fargate infrastructure (P1)
  - Acceptance: Terraform plan/apply creates or updates ECR, ECS cluster/service, task definitions, ALB, and logging resources.
  - Files: infra/terraform/main.tf, infra/terraform/variables.tf, infra/terraform/outputs.tf, infra/terraform/providers.tf
  - Started: 2026-03-28 — Added Terraform scaffolding for ECR, ECS Fargate services, ALB routing, security groups, IAM roles, and CloudWatch logs; Terraform plan/apply validation is still pending because AWS credentials and Terraform execution are out of scope for this environment.

- [ ] Task 18: Add CD workflow to auto-deploy on `main` after successful checks (P1)
  - Acceptance: Merge to `main` triggers build/push to ECR and Terraform-driven ECS deployment, failing safely on deployment errors.
  - Files: .github/workflows/deploy.yml
  - Started: 2026-03-28 — Added a GitHub Actions deploy workflow that bootstraps ECR repos, pushes images, and applies Terraform on `main`; live execution remains pending until repository secrets are configured.
