# Branch Protection Requirements

## Required Status Checks

Configure the default branch (`main`) to require all of the following checks before merge.
These map directly to the CI workflow job names.

| Check name (GitHub UI label)     | Workflow file                          |
|----------------------------------|----------------------------------------|
| `Backend Tests / pytest`         | `.github/workflows/backend-tests.yml` |
| `Frontend E2E / playwright`      | `.github/workflows/frontend-e2e.yml`  |
| `Security Checks / semgrep`      | `.github/workflows/security.yml`      |
| `Security Checks / pip-audit`    | `.github/workflows/security.yml`      |

## Required Protection Rules

- Require a pull request before merging.
- Require all status checks to pass before merging.
- Require branches to be up to date before merging.
- Dismiss stale review approvals when new commits are pushed.
- Restrict direct pushes to `main`.

## Secrets and Credentials

**Never commit AWS credentials, API keys, database connection strings, or any other secrets to the repository.**

If credentials are accidentally committed:
1. Rotate the exposed key pair immediately from the cloud provider console.
2. Use `git filter-repo` (or BFG Repo Cleaner) to purge them from git history.
3. Force-push the cleaned history and revoke the old key before any further use.

Files that must stay out of git:
- `aws_cred.md` (already in `.gitignore` — do not remove that entry)
- `.env` / `.env.local` / `.env.production`
- Any file containing raw key material

## Required GitHub Actions Secrets

Configure these in **Settings → Secrets and variables → Actions** before enabling the deploy workflow:

| Secret name              | Used by                              |
|--------------------------|--------------------------------------|
| `AWS_ACCESS_KEY_ID`      | `.github/workflows/deploy.yml` (CD)  |
| `AWS_SECRET_ACCESS_KEY`  | `.github/workflows/deploy.yml` (CD)  |
| `AWS_REGION`             | `.github/workflows/deploy.yml` (CD)  |
| `DATABASE_URL`           | Backend ECS task definition          |
| `GITHUB_TOKEN`           | Auto-provided by Actions; no setup needed |

Terraform variable overrides (pass as `TF_VAR_*` env vars in the deploy workflow or as secrets):

- `TF_VAR_database_url` — production database connection string
- `TF_VAR_github_token` — GitHub token for Colab gist generation (optional)
