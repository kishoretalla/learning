# Sprint v1 — Tasks

## Status: In Progress

### P0: Core Must-Haves (MVP Foundation)

- [x] Task 1: Project Setup — Initialize Next.js 14 + FastAPI + Docker Compose (P0)
  - Acceptance: `npm run dev` starts Next.js on :3000, FastAPI runs on :8000, both respond to health checks
  - Files: `package.json`, `pyproject.toml`, `docker-compose.yml`, `.env.example`, `app/api/health/route.ts`, `backend/main.py`
  - Completed: March 25, 2026 — Backend FastAPI fully working with health check endpoints. Frontend Next.js scaffold created, ready for Task 2. All config files, Docker setup, and project scaffold complete.

- [ ] Task 2: Frontend — ARC Prize Theme Landing Page (P0)
  - Acceptance: Page loads with elegant gradient, reads "Research Paper → Jupyter Notebook", has upload button, matches ARC Prize visual language
  - Files: `app/page.tsx`, `app/globals.css`, `tailwind.config.ts` (ARC-inspired colors: dark bg, minimal white text, purple accents)

- [ ] Task 3: Frontend — PDF Upload + OpenAI API Key Form Component (P0)
  - Acceptance: User can enter API key (masked input), select/drag-drop PDF, form validates before submit, no network call yet
  - Files: `app/components/upload-form.tsx`, `app/upload/page.tsx`, `lib/types.ts` (forms, validation, TypeScript types)

- [ ] Task 4: Backend — PDF Text Extraction Service (P0)
  - Acceptance: Endpoint `POST /api/extract-pdf` accepts file, returns JSON with `{title, abstract, full_text, sections}` using PyPDF2 or pdfplumber
  - Files: `backend/services/pdf_parser.py`, `backend/routers/pdf.py`, `backend/schemas.py` (Pydantic models)

- [ ] Task 5: Backend — GPT-4o Paper Analyzer (P0)
  - Acceptance: Endpoint `POST /api/analyze-paper` calls GPT-4o with extracted text, returns structured JSON: `{problem_statement, methodology, key_algorithms, datasets, limitations}`
  - Files: `backend/services/ai_analyzer.py`, `backend/config.py` (OpenAI client), `backend/routers/analysis.py`

- [ ] Task 6: Backend — Jupyter Notebook Generator (P0)
  - Acceptance: Function `generate_notebook(analysis_dict) → .ipynb` creates properly formatted notebook with cells: metadata, problem, methodology, algorithms (pseudocode + Python), synthetic data, visualizations
  - Files: `backend/services/notebook_generator.py` (uses nbformat), sample synthetic data generation

- [ ] Task 7: Frontend — Upload Flow → Download .ipynb (P0)
  - Acceptance: User submits form → calls `POST /api/generate` → receives .ipynb file → downloads to disk
  - Files: `app/api/generate/route.ts` (orchestration), `app/download/page.tsx` (success screen), `lib/api-client.ts` (fetch logic)

### P1: User Experience (Engagement & Polish)

- [ ] Task 8: Backend — SSE Progress Stream (P1)
  - Acceptance: Endpoint `POST /api/generate-with-progress` sends real-time events: "Parsing PDF...", "Extracting methodology...", "Generating code...", "Creating Colab link..."
  - Files: `backend/services/progress_emitter.py`, `backend/routers/progress_stream.py` (FastAPI SSE)

- [ ] Task 9: Frontend — Progress Screen with Real-Time Text Updates (P1)
  - Acceptance: User sees animated progress text while notebook generates, updates in real-time from SSE stream, spinner + styled messages
  - Files: `app/components/progress-display.tsx`, `app/api/generate-stream/route.ts` (SSE proxy), `lib/use-sse.ts` (custom hook)

- [ ] Task 10: Frontend + Backend — Google Colab Link + Download Button (P1)
  - Acceptance: Success screen shows "Download .ipynb" button AND "Open in Google Colab" button that generates shareable Colab link
  - Files: `app/components/download-buttons.tsx`, `backend/services/colab_linker.py` (generates Colab import URLs)

### P2: Polish & Error Handling (Nice-to-Have)

- [ ] Task 11: Error Handling & User Feedback (P2)
  - Acceptance: Invalid API key shows error, large PDFs show warning, malformed papers show helpful message, backend timeouts handled gracefully
  - Files: Update error boundaries in `app/error.tsx`, `backend/exceptions.py`, user-facing error messages

- [ ] Task 12: Synthetic Data Experiments in Notebook (P2)
  - Acceptance: Notebook includes realistic synthetic data generation (not toy), toy experiments with plots using matplotlib/plotly
  - Files: `backend/templates/synthetic_experiments.py` (realistic data generation algorithms), notebook cell generation

## Implementation Notes

**Why this order?**
1. Setup → foundation
2. Landing page → visual (user sees something)
3. Form → interaction
4. PDF parsing → data extraction
5. AI analysis → intelligence
6. Notebook gen → core output
7. E2E flow → MVP complete
8-10. UX → engagement (v1.1 can be without if needed)

**Testing Strategy (v1.1+):**
- Unit tests for PDF parser (mock PDFs)
- Integration tests for GPT-4o (mock OpenAI responses)
- E2E tests with Playwright (upload PDF → download notebook)

**Non-Functional Requirements:**
- PDF upload max 10 MB
- Notebook generation timeout: 60 seconds
- SSE connection lifetime: 90 seconds max
- API key never logged or stored
- No database (stateless MVP)

## Deployment Notes

**Local (v1):**
```bash
# Terminal 1: Backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
npm run dev  # starts on :3000
```

**v2+ Deployment:**
- Backend: Python on Cloud Run / Azure Container Apps
- Frontend: Vercel
- File storage: Cloud Storage (GCS/S3)
- Auth: Oauth2 + user database
