# Sprint v3 — PRD: Production Readiness (Testing + CI/CD + Deployment)

## Sprint Overview
Sprint v3 turns the current app into a production-ready release candidate with strong quality gates and repeatable deployment. This sprint prioritizes a formal testing pyramid, CI/CD enforcement on every change, and container/cloud deployment automation to AWS ECS Fargate. It also includes a real, human-in-the-loop quality validation for end-to-end notebook generation against a known paper.

## Goals
- Enforce a testing pyramid target of approximately 70% unit, 20% integration, and 10% E2E coverage for new/updated v3 test suites.
- Add robust backend unit tests for `pdf_extractor`, `arxiv_fetcher`, `prompt_template`, and `notebook_generator`.
- Add integration tests for full API flows (`upload-pdf`, `arxiv-url`) with mocked Gemini behavior.
- Add Playwright E2E coverage for full user journey with screenshots at each critical step.
- Introduce CI/CD pipelines that block merge on failed tests/security checks and auto-deploy `main` to AWS after successful gates.

## User Stories
- As a maintainer, I want strong automated tests at all levels, so regressions are caught before deployment.
- As a user, I want the generation flow tested end-to-end in browser, so UI and API interactions remain reliable.
- As an engineer, I want every push/PR gated by tests and security scans, so only safe changes can merge.
- As an operator, I want one-command local containers and cloud deployment automation, so releases are repeatable.
- As a product owner, I want a real quality validation against a known paper, so notebook output quality is objectively checked.

## Technical Architecture
- Frontend: Next.js 14 App Router (existing app), Playwright E2E test harness.
- Backend: FastAPI + SQLModel, pytest for unit/integration testing, mocked Gemini for deterministic integration coverage.
- CI/CD: GitHub Actions for backend tests, frontend tests, Semgrep scan, and pip-audit.
- Containers: Backend Docker image (FastAPI), frontend production image served behind nginx/reverse proxy setup.
- Cloud: Terraform-managed AWS infrastructure with ECS Fargate, ECR, ALB, CloudWatch logs, and deploy workflow triggered after successful `main` checks.

Component Diagram (ASCII):

```
┌────────────────────────────────────────────────────────────────────┐
│ Developer / PR                                                     │
│                                                                    │
│  Push / PR  ───────────────────────────────────────────────┐        │
└─────────────────────────────────────────────────────────────┼────────┘
                                                              ▼
┌────────────────────────────────────────────────────────────────────┐
│ GitHub Actions CI                                                  │
│                                                                    │
│ 1) pytest (unit + integration)                                     │
│ 2) Playwright E2E                                                  │
│ 3) Semgrep                                                         │
│ 4) pip-audit                                                       │
│ Any failure => status check fails => merge blocked                │
└────────────────────────────────────────────────────────────────────┘
                               │
                               │ on main + all checks green
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│ CD Workflow                                                        │
│                                                                    │
│ Build Docker images -> Push to ECR -> Terraform apply/update ECS  │
│ services -> Rolling deploy on Fargate behind ALB                  │
└────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│ Runtime                                                            │
│ Frontend container + Backend container + CloudWatch observability │
└────────────────────────────────────────────────────────────────────┘
```

Data Flow:
1. Developer pushes code or opens PR.
2. CI runs backend unit/integration tests, Playwright E2E, Semgrep, and pip-audit.
3. Branch protection blocks merge if any job fails.
4. On merge to `main`, CD builds/pushes images and applies Terraform.
5. ECS Fargate updates service revisions and routes traffic through ALB.
6. Post-deploy smoke test confirms service health.
7. Manual real-quality test runs in visible browser with user-provided API key and paper file.

## Out of Scope
- New product features unrelated to production readiness (collaboration, sharing, search revamp).
- Re-architecture away from current FastAPI + Next.js stack.
- Multi-cloud deployment support.
- Full performance/load testing at scale.
- OAuth/MFA enhancements beyond current auth scope.

## Dependencies
- Sprint v2 completed auth/history baseline and stable local run.
- Existing tests and CI-compatible project structure in backend/frontend directories.
- AWS account and IAM user already prepared for Terraform/ECS workflows.
- GitHub repository with Actions enabled and branch protection configurable.
- Secure secret management for API keys and AWS credentials in GitHub secrets (not committed to repo).
