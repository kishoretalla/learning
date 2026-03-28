# Sprint v3 — Walkthrough

## Summary

Sprint v3 turned the Research Notebook Generator into a production-ready release candidate. The sprint established a full testing pyramid (21 unit and integration tests, 6 quality-validator tests, plus 1 Playwright E2E scenario), enforced CI/CD gates on every push and PR with GitHub Actions, added production Docker images for both services, and scaffolded Terraform-managed AWS ECS Fargate infrastructure for cloud deployment. A human-in-the-loop manual quality validation checklist and a machine-verifiable notebook validator script were also added to objectively assess AI-generated output quality.

## Architecture Overview

```
+--------------------------------------------------------------------------+
| Developer / PR                                                           |
| git push / pull request                                                  |
+-----------------------------------+--------------------------------------+
                                    |
                                    v
+--------------------------------------------------------------------------+
| GitHub Actions CI (on every push + PR)                                  |
|                                                                          |
|  backend-tests.yml    frontend-e2e.yml    security.yml                  |
|  pytest (unit +       Playwright E2E      Semgrep +                     |
|  integration)         (Chromium)          pip-audit                     |
|                                                                          |
|  Any failure -> status check fails -> merge blocked (branch rules)      |
+-----------------------------------+--------------------------------------+
                                    |  on push to main + all checks green
                                    v
+--------------------------------------------------------------------------+
| CD Workflow (deploy.yml)                                                 |
|                                                                          |
|  1. terraform apply -> bootstrap ECR repos                              |
|  2. docker build + push  (backend + frontend images tagged : git SHA)   |
|  3. terraform apply -> update ECS task definitions                      |
|  4. ECS Fargate rolling deploy behind ALB                               |
+-----------------------------------+--------------------------------------+
                                    |
                                    v
+--------------------------------------------------------------------------+
| Runtime (AWS ECS Fargate, us-east-1 default VPC)                        |
|                                                                          |
|  ALB :80                                                                 |
|   +-- /api/* --> backend task  (FastAPI uvicorn, port 8000)             |
|   +-- /*      --> frontend task (Next.js + nginx, port 8080)            |
|                                                                          |
|  CloudWatch: /ecs/research-notebook-prod/backend  (14-day retention)    |
|              /ecs/research-notebook-prod/frontend (14-day retention)    |
|                                                                          |
|  ECR: research-notebook-backend   research-notebook-frontend            |
+--------------------------------------------------------------------------+

Local dev (docker compose up):
  backend  -> localhost:8000
  frontend -> localhost:3000  (nginx on container port 8080)
```

## Files Created/Modified

---

### pytest.ini

**Purpose**: Configures pytest test discovery and registers the three test-lane markers used across the suite.

**Key settings**:
- `testpaths = tests` — only scans the `tests/` directory
- `asyncio_mode = auto` — all `async` test functions run under pytest-asyncio without extra decorators
- Custom markers: `unit`, `integration`, `e2e` — allow running subsets with `-m unit`, `-m integration`, etc.

**How it works**:
Before v3 there was no pytest.ini, so invocation relied on defaults. Adding the marker registry means `pytest -m unit` now runs only the 21 fast, I/O-free unit tests. CI always runs all tests together without a marker filter, so every gate catches every lane.

---

### backend/pdf_extractor.py

**Purpose**: Extracts per-page text from PDF bytes using a dual-library strategy with automatic fallback.

**Key functions**:
- `extract_with_pdfplumber(data)` — primary extractor; uses `pdfplumber` for accurate text and layout
- `extract_with_pypdf(data)` — fallback extractor; uses `pypdf` when pdfplumber raises
- `extract_pdf_pages(data)` — public entry point; tries pdfplumber first, falls back to pypdf, raises `ValueError` if both fail

**How it works**:
Before this sprint PDF extraction was inlined inside `main.py`. Extracting it into its own module makes it directly unit-testable and swappable without touching the API layer.

```python
def extract_pdf_pages(data: bytes) -> list[dict[str, Any]]:
    try:
        return extract_with_pdfplumber(data)
    except Exception:
        try:
            return extract_with_pypdf(data)
        except Exception as exc:
            raise ValueError(f"Could not extract text from PDF: {exc}") from exc
```

Each extractor returns a list of page dicts with `page_number`, `text`, and `char_count` keys. `char_count` is always `len(text)` — not trusted from the library — so downstream code can rely on it.

---

### backend/arxiv_fetcher.py

**Purpose**: Normalises arXiv identifiers, builds canonical URLs, fetches Atom metadata from the arXiv API, and formats metadata as readable text for Gemini.

**Key functions**:
- `extract_arxiv_id(value)` — strips URL prefix and `.pdf` suffix, validates against the arXiv ID regex; raises `ValueError` on bad input
- `build_abs_url(id)` / `build_pdf_url(id)` — construct canonical arXiv abstract-page and PDF URLs
- `parse_arxiv_atom(xml_text)` — parses the Atom XML response from `export.arxiv.org` into a structured dict
- `fetch_arxiv_metadata(arxiv_id_or_url, client?)` — async; accepts an optional `httpx.AsyncClient` for injection (avoids network in tests)
- `build_arxiv_text(metadata)` — formats the metadata dict into a paragraph-style string for the Gemini prompt

**How it works**:
Accepted input forms: bare ID `1706.03762`, versioned `1706.03762v7`, full abs URL, full PDF URL. The regex chain normalises all forms to a bare ID, then calls `https://export.arxiv.org/api/query?id_list=<id>`.

The optional `client` parameter is a key testability pattern — production callers omit it and get a managed `httpx.AsyncClient(timeout=15.0)`; unit tests inject a mock:

```python
if client is not None:
    return await _fetch(client)          # test path
async with httpx.AsyncClient(timeout=15.0) as active_client:
    return await _fetch(active_client)   # production path
```

---

### backend/prompt_template.py

**Purpose**: Owns the Gemini analysis system prompt, the text-truncation ceiling, and the prompt assembly function so that prompt format is deterministic and testable in isolation.

**Key constants/functions**:
- `MAX_TEXT_CHARS = 100_000` — hard ceiling on paper text sent to Gemini to prevent token overruns
- `ANALYSIS_SYSTEM_PROMPT` — the exact JSON-schema instruction string sent to Gemini, including a grounding directive: "Do not invent unsupported facts. If information is not stated in the paper, say 'Not stated in paper'."
- `truncate_paper_text(text, max_chars?)` — slices text at the ceiling
- `build_analysis_contents(text)` — assembles: system prompt + `"\n\nPaper text:\n\n"` separator + truncated paper text

**How it works**:
Centralising the prompt means all changes to Gemini instructions happen in one place. The grounding directive is validated by a dedicated unit test — if someone removes "Not stated in paper", `test_system_prompt_includes_grounding_instruction` fails immediately, preventing a hallucination-enabling regression from merging.

---

### backend/notebook_generator.py

**Purpose**: Converts a structured Gemini analysis result into a valid nbformat v4 Jupyter notebook and a Markdown export.

**Key functions/types**:
- `NotebookContent` — dataclass with fields: `abstract`, `methodologies`, `algorithms`, `datasets`, `results`, `conclusions`, `filename`
- `generate_title_from_abstract(abstract)` — extracts the first sentence as the notebook title (max 100 chars), falls back to "Research Analysis"
- `algo_stub(name)` — generates a Python function stub with `raise NotImplementedError` and a valid identifier (spaces/hyphens → underscores, lowercased)
- `build_notebook(req)` — assembles 8 required sections into an nbformat v4 notebook; one code stub cell per algorithm
- `notebook_to_markdown(req)` — same content as a flat Markdown string for the `.md` export

**How it works**:
Cells are built sequentially using `nbformat.v4.new_markdown_cell()` and `nbformat.v4.new_code_cell()`. Each algorithm gets its own code stub cell; the safety disclaimer is always the final cell:

```python
for algo in req.algorithms:
    cells.append(_code(algo_stub(algo)))

cells.append(_md(f"## Datasets\n\n{bullet_list(req.datasets)}"))
cells.append(_md(f"## Results\n\n{req.results}"))
cells.append(_md(f"## Conclusions\n\n{req.conclusions}"))
cells.append(_md("## References\n\n" + DISCLAIMER))
```

`algo_stub("Multi-Head Attention")` produces `def multi_head_attention(data): ... raise NotImplementedError`.

---

### tests/unit/test_pdf_extractor.py

**Purpose**: 4 unit tests for `pdf_extractor` using an inline minimal PDF bytes literal and monkeypatching — no file I/O.

**Tests**:
- `test_extract_with_pdfplumber_returns_page_metadata` — real PDF bytes fixture; asserts page count, `page_number`, and `char_count` consistency
- `test_extract_with_pypdf_normalizes_missing_text` — patches `pypdf.PdfReader` to return `None`; asserts text normalises to `""`
- `test_extract_pdf_pages_falls_back_to_pypdf` — forces pdfplumber to raise; asserts fallback result is returned
- `test_extract_pdf_pages_raises_value_error_when_all_extractors_fail` — forces both extractors to raise; asserts `ValueError` with expected message

---

### tests/unit/test_arxiv_fetcher.py

**Purpose**: 6 unit tests (2 async) for `arxiv_fetcher`; all network calls are mocked with `AsyncMock` or `MagicMock`.

**Tests**: URL normalisation happy paths; non-arXiv URL rejected; canonical URL construction; Atom XML parsing; `httpx.ConnectError` mapped to `RuntimeError`; successful fetch yields parsed title.

---

### tests/unit/test_prompt_template.py

**Purpose**: 4 unit tests locking in the structure and safety content of the Gemini prompt.

**Tests**: all 6 JSON field names present; "Not stated in paper" grounding instruction present; truncation respects `MAX_TEXT_CHARS` exactly; assembled prompt has deterministic format (starts with system prompt, ends with paper body, separator present).

---

### tests/unit/test_notebook_generator.py

**Purpose**: 7 unit tests covering notebook generation against a fixed "Attention Is All You Need" `SAMPLE_CONTENT` fixture.

**Tests**: first-sentence title extraction; empty-input fallback to "Research Analysis"; algorithm name → valid Python identifier stub; `nbformat.validate()` passes (kernelspec is `python3`); all 8 required section headings in markdown cells; one `NotImplementedError` stub cell per algorithm; Markdown export contains same section headings.

---

### tests/integration/test_upload_pdf_endpoint.py

**Purpose**: 1 integration test exercising the full upload → extract → analyze pipeline with Gemini mocked at the `backend.main` module level.

**How it works**:
Uses FastAPI's `TestClient`. First calls `POST /api/extract-text` with a real PDF bytes fixture (reused from `test_extract_text.py`), then patches `genai.Client` as a context manager to return canned JSON, and calls `POST /api/analyze-paper` with the extracted text. Asserts the response matches `MOCK_ANALYSIS` exactly and validates `filename` and `total_pages`.

```python
with _mock_gemini(MOCK_ANALYSIS):
    analyze_response = client.post("/api/analyze-paper", json={...})
assert analyze_response.json() == MOCK_ANALYSIS
```

---

### tests/integration/test_arxiv_url_endpoint.py

**Purpose**: 2 integration tests for `POST /api/arxiv-url`.

**Tests**:
- Happy path: patches `fetch_arxiv_metadata` (no network) and `genai.Client` (no Gemini); asserts combined response contract — `filename`, `is_arxiv`, `title`, `analysis`, and `pages[0].char_count` consistency
- Invalid URL: submits `https://example.com/not-arxiv`; asserts HTTP 400 with "Invalid arXiv identifier" in detail

---

### tests/quality/validate_generated_notebook.py

**Purpose**: CLI script that validates a real generated `.ipynb` against 6 objective criteria; exits 0 on pass, 1 on any failure.

**Checks**:
1. `nbformat == 4` and `cells` key present
2. All 8 required section headings present in markdown cells
3. Abstract text ≥ 80 characters
4. At least one Python code cell with valid syntax (`ast.parse`)
5. At least one safety/disclaimer phrase in any cell (case-insensitive)
6. At least one `raise NotImplementedError` algorithm stub

The `_cell_source()` helper normalises both nbformat cell source types (plain `str` or `list[str]`):

```python
def _cell_source(cell: dict) -> str:
    src = cell.get("source", "")
    if isinstance(src, list):
        return "".join(src)
    return src
```

---

### tests/quality/test_real_attention_paper.md

**Purpose**: Step-by-step human checklist for running a real-API quality validation against "Attention Is All You Need" (arXiv 1706.03762).

Covers: pre-requisites, exact UI steps, CLI validator invocation, manual spot-check criteria (title accuracy, no invented facts, algorithm stubs, safety disclaimer, syntactically valid Python), and pass/fail criteria. Intended to be completed by a human with a real Gemini API key before tagging a sprint release.

---

### tests/quality/test_validator.py

**Purpose**: 6 pytest unit tests that run `validate_generated_notebook.py` as a subprocess using synthetic `tempfile` notebooks.

Good notebook passes; each of the 5 failure modes (missing sections, bad nbformat, short abstract, invalid Python, missing disclaimer) is caught and reported independently.

---

### frontend/tests/e2e/full-user-flow.spec.ts

**Purpose**: 1 Playwright end-to-end test simulating a complete authenticated user flow in real Chromium.

**How it works**:
Seeds a session cookie directly into the browser context (bypasses the login UI), then intercepts all four backend API calls with `page.route()` to return deterministic mocks — no live backend or Gemini API required. The `/api/generate-notebook` mock includes a 500ms artificial delay to exercise the spinner visibility assertion before the success state appears.

Flow:
1. Navigate to `/upload` with seeded session cookie
2. Fill API key + arXiv URL fields
3. Click "Generate Notebook" → assert navigation to `/processing`
4. Assert spinner and step labels visible
5. Wait for success → assert "Download Notebook" button visible
6. Screenshots captured at all three stages in `frontend/tests/screenshots/`

---

### frontend/playwright.config.ts

**Purpose**: Playwright harness configuration for the frontend test suite.

Key settings: `fullyParallel: true` locally; `workers: 1` in CI; `retries: 2` in CI; trace `on-first-retry`; video `retain-on-failure`; screenshot `only-on-failure`; `webServer` auto-starts `npm run dev` and waits for `localhost:3000`, reusing an existing server in local dev.

---

### .github/workflows/backend-tests.yml

**Purpose**: CI job running the full pytest suite on every push to `main` and every PR.

Installs Python 3.11, installs the backend package with `pip install -e "./backend[dev]"` (pulls in `pytest`, `pytest-asyncio`, `httpx`, etc.), runs `pytest -q --tb=short` with `PYTHONPATH=.`. Any failing test blocks the merge.

---

### .github/workflows/frontend-e2e.yml

**Purpose**: CI job that starts the FastAPI backend and runs Playwright tests against it.

Installs Python 3.11 + Node 20, starts `uvicorn` in the background, polls `GET /health` up to 60 seconds (30 × 2s intervals), then runs Playwright in headless Chromium. On any outcome, uploads `playwright-report/` and `test-results/` as workflow artifacts for debugging.

---

### .github/workflows/security.yml

**Purpose**: Two-job security gate; either job failing blocks merge.

- `semgrep` — `semgrep/semgrep-action@v1` with `p/security-audit` ruleset; OWASP-style static analysis of the full repository
- `pip-audit` — scans all backend transitive dependencies against CVE databases

Both jobs run independently on push and PR.

---

### .github/workflows/deploy.yml

**Purpose**: CD pipeline auto-deploying to AWS ECS Fargate on every successful push to `main`.

Sequence:
1. Configure AWS credentials from repository secrets
2. `terraform init` + `terraform apply` targeting only ECR repos (bootstrap step so images can be pushed)
3. `docker build` + `docker push` backend and frontend, both tagged with `github.sha`
4. Full `terraform apply` updates ECS task definitions to the new image tags
5. ECS performs a rolling replacement of tasks

Image tags default to `latest` but the workflow always passes `TF_VAR_frontend_image_tag=${{ github.sha }}` so each deploy is pinned to an exact commit.

---

### backend/Dockerfile

**Purpose**: Production backend container image based on `python:3.11-slim`.

Creates a non-root `appuser` at build time, copies only the `backend/` directory (not the entire monorepo), installs with `pip install --no-cache-dir ./backend` (production dependencies only — no `[dev]` extras). The `HEALTHCHECK` uses stdlib `urllib.request` so no extra packages are needed.

```dockerfile
FROM python:3.11-slim
RUN useradd --create-home appuser
COPY backend/ ./backend/
RUN pip install --no-cache-dir ./backend
USER appuser
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### frontend/Dockerfile

**Purpose**: Production frontend container running Next.js in standalone output mode behind nginx.

Multi-stage build: `builder` stage runs `npm ci && npm run build` to produce a Next.js standalone bundle; `runner` stage uses `node:20-alpine`, installs nginx + supervisor via `apk`, copies the standalone bundle and wires both processes via supervisord. Exposes port 8080. The `HEALTHCHECK` uses `wget` (available in alpine) to hit the nginx port.

```dockerfile
FROM node:20-alpine AS builder
RUN npm ci && npm run build

FROM node:20-alpine AS runner
RUN apk add --no-cache nginx supervisor
COPY --from=builder /app/.next/standalone ./
COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisord.conf
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
```

---

### frontend/nginx.conf + frontend/supervisord.conf

**Purpose**: nginx reverse-proxies port 8080 to the internal Next.js port and serves `.next/static` assets directly from disk. supervisord manages both the nginx and Node processes inside the same container, restarting either if it exits unexpectedly.

---

### docker-compose.yml

**Purpose**: Production-local stack with healthchecks and correct startup ordering.

`frontend` declares `depends_on: backend: condition: service_healthy` so Docker Compose waits for the backend to pass its healthcheck before starting the frontend. Backend maps to `localhost:8000`; frontend maps to `localhost:3000`.

---

### infra/terraform/ (main.tf, variables.tf, outputs.tf, providers.tf)

**Purpose**: Full Terraform configuration for AWS ECS Fargate deployment into the account's default VPC.

**Resources created**:
- ECR repos for backend and frontend (`scan_on_push = true`)
- ECS cluster, task execution role + task role, task definitions for both services
- ECS services (configurable desired count, default 1)
- Application Load Balancer with target groups; HTTP listener routing `/api/*` to backend and `/*` to frontend
- CloudWatch log groups (14-day retention) for both services
- Security groups for ALB and ECS tasks

All resource names are prefixed `${var.app_name}-${var.environment}` (default: `research-notebook-prod`). Key outputs: `alb_dns_name`, both ECR repository URLs, ECS cluster name.

---

### docs/branch-protection.md

**Purpose**: Documents the GitHub repository settings operators must configure to enforce the CI gates.

Contains: a table mapping exact check names (as they appear in the GitHub UI) to their workflow files; required branch protection rules (no direct push to main, PRs required, dismiss stale reviews); credentials hygiene procedures including `git filter-repo` instructions for accidentally committed secrets; and a table of all required GitHub Actions secrets.

---

## Data Flow

### CI/CD Pipeline

```
Developer pushes or opens PR
  +-- backend-tests.yml  -> pytest (unit + integration + quality validator)
  +-- frontend-e2e.yml   -> Playwright Chromium E2E
  +-- security.yml       -> Semgrep static analysis + pip-audit CVE scan

Any failure -> branch protection blocks merge

Merge to main:
  deploy.yml:
    terraform apply (ECR bootstrap only)
    -> docker build + push backend:SHA + frontend:SHA to ECR
    -> terraform apply (ECS task definitions updated to new SHA)
    -> ECS rolling deploy (old tasks drain, new tasks warm up behind ALB)
```

### Playwright E2E Flow

```
Browser opens /upload
  -> session cookie seeded into context  (bypasses login UI)
  -> user fills API key + arXiv URL fields
  -> POST /api/arxiv-url intercepted     -> MOCK_ARXIV_RESPONSE returned instantly
  -> user clicks "Generate Notebook"     -> page navigates to /processing
  -> processing steps visible (spinner, step labels)
  -> POST /api/generate-notebook intercepted -> 500ms delay -> mock .ipynb returned
  -> success state renders               -> "Download Notebook" button visible
  -> screenshots saved: upload-ready, processing, success
```

### Manual Quality Validation Flow

```
Human: docker compose up --build  (or local dev servers)
  -> opens http://localhost:3000/upload in visible browser
  -> pastes https://arxiv.org/abs/1706.03762 + real Gemini API key
  -> clicks "Generate Notebook"
  -> observes 3 processing steps complete with green checkmarks
  -> downloads attention_output.ipynb
  -> runs: python tests/quality/validate_generated_notebook.py attention_output.ipynb
  -> reviews 6 machine checks (exit 0 = pass)
  -> spot-checks content accuracy against known paper facts
```

## Test Coverage

- **Unit — 21 tests** across 4 modules:
  - `test_pdf_extractor.py` — 4 tests: happy path, None normalisation, pdfplumber fallback, double failure
  - `test_arxiv_fetcher.py` — 6 tests: URL normalisation, rejection, URL construction, Atom parsing, network error, success
  - `test_prompt_template.py` — 4 tests: JSON keys, grounding instruction, truncation, deterministic format
  - `test_notebook_generator.py` — 7 tests: title extraction, fallback, algo stub, valid notebook, 8 sections, stub count, markdown export
- **Integration — 3 tests**:
  - `test_upload_pdf_endpoint.py` — 1 test: upload → extract → analyze response contract with mocked Gemini
  - `test_arxiv_url_endpoint.py` — 2 tests: full response contract, invalid URL rejection
- **Quality validator unit tests — 6 tests**: good notebook passes; each of 5 failure modes caught independently
- **E2E — 1 Playwright scenario**: full authenticated arXiv flow from upload through download with 3 screenshots

## Security Measures

- **Semgrep gate** — `p/security-audit` ruleset on every push and PR; non-zero findings block merge
- **pip-audit gate** — all backend transitive dependencies scanned against CVE databases on every push and PR
- **Non-root container user** — backend Dockerfile creates and runs as `appuser` (never root)
- **ECR scan on push** — `scan_on_push = true` on both ECR repos; AWS Inspector scans every image layer at push time
- **Secrets via GitHub Secrets** — no AWS credentials, database URLs, or API keys committed; all sensitive values flow through `secrets.*` in workflow files
- **Credentials hygiene docs** — `docs/branch-protection.md` documents key rotation procedures and `git filter-repo` instructions for accidentally committed secrets
- **Grounding instruction in Gemini prompt** — "Do not invent unsupported facts" reduces hallucination risk; enforced by a unit test that fails if the phrase is removed

## Known Limitations

- **Terraform not validated in CI** — `terraform plan` is not a CI check; syntax or plan errors are only discovered at deploy time
- **SQLite in production** — the backend defaults to a local SQLite file, which is not suitable for ECS Fargate with multiple tasks (no shared filesystem). The `database_url` Terraform variable accepts a managed DB URL but no RDS resource is provisioned
- **Frontend E2E mocks all API calls** — the Playwright test never makes real HTTP requests; real API contract breaks (wrong field names, wrong status codes) are not caught at the E2E layer
- **Docker validation pending** — Tasks 14–16 are marked "Started" not "Complete" because Docker was unavailable in the development environment; the Dockerfiles and compose file are written but not runtime-tested
- **Deploy workflow untested** — `deploy.yml` requires repository secrets that are not yet configured; no live deployment has been executed
- **No HTTPS listener** — the Terraform ALB only has an HTTP listener on port 80; a TLS certificate and HTTPS listener are required before serving real user traffic
- **Single E2E scenario** — only the arXiv URL path is tested end-to-end; the PDF file upload flow has no E2E coverage
- **No rate limiting** — `POST /api/analyze-paper` and `POST /api/arxiv-url` have no per-IP or per-key rate limits

## What's Next

v4 should close the infrastructure and coverage gaps left open by v3:

1. **Managed database** — add AWS RDS (PostgreSQL) to the Terraform stack; migrate SQLModel models from the SQLite dialect and add connection pooling for multi-task Fargate deploys
2. **HTTPS** — add an ACM certificate resource and an HTTPS listener to the ALB; redirect HTTP to HTTPS
3. **Terraform plan in CI** — add `terraform plan` as a required CI check using a read-only IAM role to catch configuration errors before they reach `deploy.yml`
4. **PDF upload E2E test** — add a second Playwright scenario covering the file upload path with a locally served PDF fixture
5. **Docker smoke test in CI** — add a CI step running `docker compose up --wait` + a `curl` healthcheck to confirm both containers build and start correctly
6. **Rate limiting** — add per-IP rate limiting on the generation endpoints to prevent Gemini API key abuse
7. **Post-deploy smoke test** — add a `deploy.yml` step that curls the ALB DNS name and fails the workflow if the health endpoint does not respond, enabling rollback detection
