# Research Paper → Jupyter Notebook Generator

## Test Lanes

- Unit: `PYTHONPATH=. .venv/bin/pytest tests/unit -q`
- Integration: `PYTHONPATH=. .venv/bin/pytest tests/integration -q`
- Frontend E2E: `cd frontend && npx playwright test`

## CI Gates

GitHub Actions workflows now cover backend tests, frontend Playwright runs, and security checks. Do not commit cloud credentials or API keys; use repository secrets instead.

## arXiv Flow

Authenticated users can now start from an arXiv URL or identifier on the upload page. The backend resolves arXiv metadata, creates an extraction payload, and precomputes Gemini analysis so the processing page can move straight to notebook generation.

## Deployment Scaffolding

Production deployment scaffolding is included for local containers and AWS ECS Fargate:

- `docker compose up --build` uses the production-oriented root compose file.
- `backend/Dockerfile` exposes a health-checked FastAPI container.
- `frontend/Dockerfile` builds a standalone Next.js app and serves it behind nginx.
- `infra/terraform/` contains AWS ECS, ALB, ECR, and CloudWatch infrastructure scaffolding.
- `.github/workflows/deploy.yml` builds and pushes images, then applies Terraform on `main`.

The deployment files were not executed in this environment because Docker and Terraform CLIs are not available here.
