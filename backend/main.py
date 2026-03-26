"""
Research Notebook Backend - Main FastAPI Application
"""
import io
import json
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

import httpx

import nbformat
import pdfplumber
from backend.auth import hash_password, SignupRequest, UserResponse
from backend.demo_papers import DEMO_PAPER_MAP, DEMO_PAPERS
from backend.db import init_db, set_engine, get_db
from backend.models import User
import pypdf
from fastapi import FastAPI, Form, HTTPException, Request, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from google import genai
from google.genai import errors as genai_errors
from pydantic import BaseModel
from sqlmodel import Session, select

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
)
logger = logging.getLogger(__name__)


# ── In-memory metrics ────────────────────────────────────────────────────────

@dataclass
class _Metrics:
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    uploads_attempted: int = 0
    upload_errors: int = 0
    analyses_attempted: int = 0
    analyses_successful: int = 0
    api_key_invalid: int = 0
    rate_limit_hits: int = 0
    notebooks_generated: int = 0
    colab_links_created: int = 0
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def inc(self, field_name: str, by: int = 1) -> None:
        with self._lock:
            setattr(self, field_name, getattr(self, field_name) + by)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            success = self.analyses_successful
            attempted = self.analyses_attempted
            return {
                "uploads_attempted": self.uploads_attempted,
                "upload_errors": self.upload_errors,
                "upload_error_rate": round(self.upload_errors / self.uploads_attempted, 4)
                    if self.uploads_attempted else 0.0,
                "analyses_attempted": attempted,
                "analyses_successful": success,
                "conversion_success_rate": round(success / attempted, 4) if attempted else 0.0,
                "api_key_invalid": self.api_key_invalid,
                "rate_limit_hits": self.rate_limit_hits,
                "notebooks_generated": self.notebooks_generated,
                "colab_links_created": self.colab_links_created,
                "uptime_since": self.started_at,
            }


_metrics = _Metrics()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    logger.info("🚀 Research Notebook Backend started")
    
    # Initialize database on startup
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./research-notebook.db")
    try:
        engine = init_db(db_url)
        set_engine(engine)
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    logger.info("🛑 Research Notebook Backend shutting down")


# Initialize FastAPI app
app = FastAPI(
    title="Research Notebook Backend",
    description="Convert research papers to Jupyter notebooks using AI",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_CSRF_ALLOWED = {"XMLHttpRequest", "fetch"}


@app.middleware("http")
async def csrf_protection(request: Request, call_next):
    """
    In production, require X-Requested-With on mutation endpoints to prevent
    cross-site form submission attacks.  CORS already blocks cross-origin XHR,
    but this adds defence-in-depth for multipart and JSON POST requests.
    """
    if (
        os.environ.get("ENVIRONMENT") == "production"
        and request.method in ("POST", "PUT", "PATCH", "DELETE")
        and request.headers.get("X-Requested-With") not in _CSRF_ALLOWED
    ):
        return JSONResponse(
            {"detail": "CSRF protection: X-Requested-With header required."},
            status_code=403,
        )
    return await call_next(request)


@app.get("/api/metrics", tags=["Analytics"])
async def get_metrics():
    """Return in-memory usage metrics and error counts."""
    return _metrics.snapshot()


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        {
            "status": "ok",
            "service": "research-notebook-backend",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        status_code=200,
    )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Research Notebook Backend",
        "version": "0.1.0",
        "docs": "/docs",
    }


# ── Authentication Routes ───────────────────────────────────────────────────

@app.post("/api/auth/signup", tags=["Auth"], status_code=201, response_model=UserResponse)
async def signup(
    request: SignupRequest,
    db: Session = Depends(get_db),
):
    """
    User signup endpoint.
    
    Creates a new user account with email and password.
    Password is hashed with bcrypt before storage.
    
    Returns: 201 Created with user data (password excluded)
    Returns: 409 Conflict if email already exists
    Returns: 422 Validation Error if email/password invalid
    """
    # Validate password length (minimum 8 characters for security)
    if len(request.password) < 8:
        raise HTTPException(
            status_code=422,
            detail="Password must be at least 8 characters long",
        )
    
    # Check if email already exists
    existing_user = db.exec(
        select(User).where(User.email == request.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already exists. Please use a different email.",
        )
    
    # Hash password
    hashed_password = hash_password(request.password)
    
    # Create user
    user = User(
        email=request.email,
        hashed_password=hashed_password,
        full_name=request.full_name,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Return user data with ISO timestamp
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at.isoformat(),
    )


MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB


def _extract_with_pdfplumber(data: bytes) -> list[dict[str, Any]]:
    pages = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append({"page_number": i, "text": text, "char_count": len(text)})
    return pages


def _extract_with_pypdf(data: bytes) -> list[dict[str, Any]]:
    pages = []
    reader = pypdf.PdfReader(io.BytesIO(data))
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append({"page_number": i, "text": text, "char_count": len(text)})
    return pages


@app.post("/api/extract-text", tags=["Extraction"])
async def extract_text(
    file: UploadFile,
    api_key: str = Form(...),
):
    """
    Accept a PDF upload and return structured text with per-page metadata.
    """
    _metrics.inc("uploads_attempted")

    # Validate filename
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        _metrics.inc("upload_errors")
        logger.warning("upload_rejected reason=invalid_extension filename=%s", filename)
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Read and enforce size limit
    data = await file.read()
    if len(data) > MAX_PDF_SIZE:
        _metrics.inc("upload_errors")
        logger.warning("upload_rejected reason=too_large size_mb=%.1f", len(data) / 1024 / 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds 10 MB limit ({len(data) / 1024 / 1024:.1f} MB).",
        )

    if len(data) == 0:
        _metrics.inc("upload_errors")
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Validate PDF magic bytes
    if not data.startswith(b"%PDF"):
        _metrics.inc("upload_errors")
        logger.warning("upload_rejected reason=invalid_magic filename=%s", filename)
        raise HTTPException(status_code=400, detail="File does not appear to be a valid PDF.")

    # Extract text — pdfplumber first, pypdf as fallback
    try:
        pages = _extract_with_pdfplumber(data)
    except Exception:
        try:
            pages = _extract_with_pypdf(data)
        except Exception as exc:
            _metrics.inc("upload_errors")
            logger.error("pdf_extraction_failed filename=%s error=%s", filename, exc)
            raise HTTPException(
                status_code=422, detail=f"Could not extract text from PDF: {exc}"
            ) from exc

    total_chars = sum(p["char_count"] for p in pages)
    logger.info("pdf_extracted filename=%s pages=%d chars=%d", filename, len(pages), total_chars)

    return {
        "filename": filename,
        "total_pages": len(pages),
        "total_chars": total_chars,
        "pages": pages,
    }


MAX_TEXT_CHARS = 100_000  # ~75k tokens, safely within Gemini's context window

ANALYSIS_SYSTEM_PROMPT = """\
You are an expert research paper analyzer. Extract structured information from the provided paper text.
Return ONLY valid JSON with exactly these keys:
{
  "abstract": "<string: paper abstract or concise summary if absent>",
  "methodologies": ["<string>", ...],
  "algorithms": ["<string>", ...],
  "datasets": ["<string>", ...],
  "results": "<string: key quantitative and qualitative findings>",
  "conclusions": "<string: main conclusions and contributions>"
}
No markdown, no explanation, only the JSON object."""


class AnalyzePaperRequest(BaseModel):
    text: str
    api_key: str
    filename: str | None = None


def _call_gemini(api_key: str, text: str) -> dict[str, Any]:
    client = genai.Client(api_key=api_key)
    truncated = text[:MAX_TEXT_CHARS]
    response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=f"{ANALYSIS_SYSTEM_PROMPT}\n\nPaper text:\n\n{truncated}",
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    raw = response.text or "{}"
    return json.loads(raw)


async def _stream_gemini(api_key: str, text: str) -> AsyncGenerator[str, None]:
    import asyncio
    client = genai.Client(api_key=api_key)
    truncated = text[:MAX_TEXT_CHARS]

    def _generate():
        return list(client.models.generate_content_stream(
            model="gemini-3.1-pro-preview",
            contents=f"{ANALYSIS_SYSTEM_PROMPT}\n\nPaper text:\n\n{truncated}",
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        ))

    chunks = await asyncio.to_thread(_generate)
    accumulated = ""
    for chunk in chunks:
        delta = getattr(chunk, "text", "") or ""
        if delta:
            accumulated += delta
            yield f"data: {json.dumps({'delta': delta})}\n\n"

    try:
        parsed = json.loads(accumulated)
    except json.JSONDecodeError:
        parsed = {"raw": accumulated}
    yield f"event: complete\ndata: {json.dumps(parsed)}\n\n"


@app.post("/api/analyze-paper", tags=["Analysis"])
async def analyze_paper(request: AnalyzePaperRequest, stream: bool = False):
    """
    Call GPT-4o to extract structured analysis from paper text.
    Set ?stream=true for Server-Sent Events streaming.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Paper text is empty.")
    if not request.api_key.strip():
        raise HTTPException(status_code=400, detail="Gemini API key is required.")

    _metrics.inc("analyses_attempted")
    logger.info("analysis_started filename=%s text_chars=%d", request.filename or "unknown", len(request.text))

    if stream:
        return StreamingResponse(
            _stream_gemini(request.api_key, request.text),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    try:
        t0 = time.monotonic()
        result = _call_gemini(request.api_key, request.text)
        elapsed = round(time.monotonic() - t0, 2)
        _metrics.inc("analyses_successful")
        logger.info("analysis_complete filename=%s elapsed_s=%s", request.filename or "unknown", elapsed)
    except genai_errors.ClientError as exc:
        if exc.status == "PERMISSION_DENIED" or (hasattr(exc, "code") and exc.code == 403):
            _metrics.inc("api_key_invalid")
            logger.warning("api_key_invalid filename=%s", request.filename or "unknown")
            raise HTTPException(status_code=401, detail="Invalid Gemini API key.") from exc
        if exc.status == "RESOURCE_EXHAUSTED" or (hasattr(exc, "code") and exc.code == 429):
            _metrics.inc("rate_limit_hits")
            logger.warning("rate_limit_hit filename=%s", request.filename or "unknown")
            raise HTTPException(status_code=429, detail="Gemini rate limit reached. Please retry later.") from exc
        logger.error("gemini_error filename=%s error=%s", request.filename or "unknown", exc)
        raise HTTPException(status_code=502, detail=f"Gemini error: {exc}") from exc
    except genai_errors.APIError as exc:
        logger.error("gemini_error filename=%s error=%s", request.filename or "unknown", exc)
        raise HTTPException(status_code=502, detail=f"Gemini error: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail="Gemini returned malformed JSON.") from exc

    return result


class GenerateNotebookRequest(BaseModel):
    abstract: str
    methodologies: list[str]
    algorithms: list[str]
    datasets: list[str]
    results: str
    conclusions: str
    filename: str | None = None


def _md(source: str) -> nbformat.notebooknode.NotebookNode:
    return nbformat.v4.new_markdown_cell(source)


def _code(source: str) -> nbformat.notebooknode.NotebookNode:
    return nbformat.v4.new_code_cell(source)


def _bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- N/A"


def _algo_stub(name: str) -> str:
    safe = name.replace(" ", "_").replace("-", "_").lower()
    return (
        f"def {safe}(data):\n"
        f'    """{name} implementation stub.\n'
        f"    Replace with actual implementation from the paper.\n"
        f'    """\n'
        f"    # TODO: implement {name}\n"
        f"    raise NotImplementedError\n"
    )


def _build_notebook(req: GenerateNotebookRequest) -> nbformat.notebooknode.NotebookNode:
    title = req.filename.replace(".pdf", "") if req.filename else "Research Paper"
    nb = nbformat.v4.new_notebook()

    cells = [
        # ── Title ──────────────────────────────────────────────────────────────
        _md(
            f"# {title}\n\n"
            "*Generated by [Research Notebook Generator](http://localhost:3000)*\n\n"
            f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        ),

        # ── Setup ──────────────────────────────────────────────────────────────
        _md("## Setup\n\nInstall and import required libraries."),
        _code(
            "# Install dependencies (works in Colab, local Jupyter, and plain Python)\n"
            "import sys\n"
            "try:\n"
            "    import numpy, pandas, matplotlib, sklearn\n"
            "except ImportError:\n"
            "    import subprocess\n"
            "    subprocess.check_call([sys.executable, '-m', 'pip', 'install',\n"
            "                           'numpy', 'pandas', 'matplotlib', 'scikit-learn'])\n\n"
            "import numpy as np\n"
            "import pandas as pd\n"
            "import matplotlib.pyplot as plt\n"
            "import matplotlib.ticker as ticker\n"
            "from sklearn.model_selection import train_test_split\n"
            "from sklearn.metrics import accuracy_score\n\n"
            "np.random.seed(42)\n"
            'print("Libraries loaded successfully.")'
        ),

        # ── Abstract ───────────────────────────────────────────────────────────
        _md(f"## Abstract\n\n{req.abstract}"),

        # ── Methodologies ──────────────────────────────────────────────────────
        _md(f"## Key Methodologies\n\n{_bullet_list(req.methodologies)}"),

        # ── Algorithms ─────────────────────────────────────────────────────────
        _md(
            "## Algorithms & Techniques\n\n"
            f"{_bullet_list(req.algorithms)}\n\n"
            "The cells below provide stub implementations to get you started."
        ),
    ]

    # One code cell per algorithm
    for algo in req.algorithms:
        cells.append(_code(_algo_stub(algo)))

    cells += [
        # ── Datasets ───────────────────────────────────────────────────────────
        _md(
            "## Datasets\n\n"
            f"{_bullet_list(req.datasets)}\n\n"
            "The cell below generates synthetic data that mimics the structure "
            "described in the paper so you can run experiments immediately."
        ),
        _code(
            "# Synthetic dataset — replace with real data loading as needed\n"
            "n_samples = 1000\n"
            "n_features = 10\n\n"
            "X = np.random.randn(n_samples, n_features)\n"
            "y = (X[:, 0] + X[:, 1] > 0).astype(int)  # binary target\n\n"
            "X_train, X_test, y_train, y_test = train_test_split(\n"
            "    X, y, test_size=0.2, random_state=42\n"
            ")\n\n"
            f'print(f"Train: {{X_train.shape}}, Test: {{X_test.shape}}")\n'
            "pd.DataFrame(X_train, columns=[f'feature_{i}' for i in range(n_features)]).head()"
        ),

        # ── Results ────────────────────────────────────────────────────────────
        _md(f"## Results\n\n{req.results}"),
        _code(
            "# Reproduce key results — update metric values from the paper\n"
            "metrics = {\n"
            "    'Baseline': 0.70,\n"
            "    'Proposed Method': 0.85,\n"
            "}\n\n"
            "fig, ax = plt.subplots(figsize=(7, 4))\n"
            "bars = ax.bar(metrics.keys(), metrics.values(), color=['#6b7280', '#a855f7'])\n"
            "ax.set_ylim(0, 1.0)\n"
            "ax.set_ylabel('Score')\n"
            "ax.set_title('Method Comparison')\n"
            "ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))\n"
            "for bar, val in zip(bars, metrics.values()):\n"
            "    ax.text(bar.get_x() + bar.get_width() / 2, val + 0.01,\n"
            "            f'{val:.0%}', ha='center', va='bottom', fontweight='bold')\n"
            "plt.tight_layout()\n"
            "plt.show()"
        ),

        # ── Conclusions ────────────────────────────────────────────────────────
        _md(f"## Conclusions\n\n{req.conclusions}"),

        # ── References ─────────────────────────────────────────────────────────
        _md(
            "## References\n\n"
            f"- Source paper: **{title}**\n"
            "- Datasets: " + (", ".join(req.datasets) if req.datasets else "See paper") + "\n"
            "- Add full citations here."
        ),
    ]

    nb.cells = cells
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nb.metadata["language_info"] = {"name": "python", "version": "3.10.0"}
    nb.metadata["colab"] = {"name": f"{title}.ipynb", "provenance": []}
    return nb


@app.post("/api/generate-notebook", tags=["Notebook"])
async def generate_notebook(request: GenerateNotebookRequest):
    """
    Accept GPT-4o analysis results and return a downloadable Jupyter notebook (.ipynb).
    """
    if not request.abstract.strip() and not request.results.strip():
        raise HTTPException(status_code=400, detail="Analysis result is empty — nothing to generate.")

    nb = _build_notebook(request)

    try:
        nbformat.validate(nb)
    except nbformat.ValidationError as exc:
        raise HTTPException(status_code=500, detail=f"Generated notebook failed validation: {exc}") from exc

    content = nbformat.writes(nb).encode("utf-8")
    stem = (request.filename or "paper").replace(".pdf", "")
    download_name = f"{stem}-notebook.ipynb"

    _metrics.inc("notebooks_generated")
    logger.info("notebook_generated filename=%s size_bytes=%d", download_name, len(content))

    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )


class ColabLinkRequest(BaseModel):
    notebook_json: str
    filename: str | None = None


async def _create_github_gist(notebook_json: str, filename: str) -> dict[str, Any]:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        return {"available": False, "reason": "GITHUB_TOKEN not configured"}

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        user_r = await client.get("https://api.github.com/user", headers=headers)
        if user_r.status_code != 200:
            return {"available": False, "reason": "Invalid GitHub token"}
        username = user_r.json()["login"]

        gist_r = await client.post(
            "https://api.github.com/gists",
            headers=headers,
            json={
                "description": f"Research Notebook — {filename.replace('.ipynb', '')}",
                "public": False,
                "files": {filename: {"content": notebook_json}},
            },
        )
        if gist_r.status_code != 201:
            return {"available": False, "reason": "Failed to create GitHub Gist"}

    gist_id = gist_r.json()["id"]
    return {
        "available": True,
        "gist_id": gist_id,
        "gist_url": f"https://gist.github.com/{username}/{gist_id}",
        "colab_url": f"https://colab.research.google.com/gist/{username}/{gist_id}/{filename}",
    }


@app.post("/api/create-colab-link", tags=["Colab"])
async def create_colab_link(request: ColabLinkRequest):
    """
    Create a private GitHub Gist from the notebook and return a Colab-ready URL.
    Requires GITHUB_TOKEN env var; returns available=false gracefully if not set.
    """
    if not request.notebook_json.strip():
        raise HTTPException(status_code=400, detail="notebook_json is empty.")

    filename = request.filename or "notebook.ipynb"
    if not filename.endswith(".ipynb"):
        filename += ".ipynb"

    try:
        result = await _create_github_gist(request.notebook_json, filename)
    except httpx.HTTPError as exc:
        logger.error("gist_creation_failed error=%s", exc)
        raise HTTPException(status_code=502, detail=f"GitHub API error: {exc}") from exc

    if result.get("available"):
        _metrics.inc("colab_links_created")
        logger.info("colab_link_created gist_id=%s", result.get("gist_id"))

    return result


# ── Task 11: Demo Papers Library ─────────────────────────────────────────────

@app.get("/api/demo-papers", tags=["Demo"])
async def list_demo_papers():
    """Return the catalogue of pre-loaded demo papers (no PDF upload needed)."""
    return [
        {k: v for k, v in p.items() if k != "text"}
        for p in DEMO_PAPERS
    ]


@app.post("/api/demo-papers/{paper_id}/extract", tags=["Demo"])
async def extract_demo_paper(paper_id: str):
    """
    Return pre-extracted text for a demo paper so the frontend can skip
    PDF upload and go straight to /processing.
    """
    paper = DEMO_PAPER_MAP.get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail=f"Demo paper '{paper_id}' not found.")

    text = paper["text"]
    pages = [{"page_number": i + 1, "text": para, "char_count": len(para)}
             for i, para in enumerate(text.split("\n\n")) if para.strip()]

    logger.info("demo_paper_extracted id=%s pages=%d", paper_id, len(pages))
    return {
        "filename": f"{paper_id}.pdf",
        "total_pages": len(pages),
        "total_chars": sum(p["char_count"] for p in pages),
        "pages": pages,
        "is_demo": True,
        "title": paper["title"],
    }


# ── Task 12: Markdown Export ──────────────────────────────────────────────────

def _notebook_to_markdown(req: "GenerateNotebookRequest") -> str:
    title = req.filename.replace(".pdf", "") if req.filename else "Research Paper"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def bullets(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items) if items else "- N/A"

    def algo_fence(name: str) -> str:
        safe = name.replace(" ", "_").replace("-", "_").lower()
        return (
            f"```python\ndef {safe}(data):\n"
            f'    """{name} implementation stub."""\n'
            f"    # TODO: implement {name}\n"
            f"    raise NotImplementedError\n```"
        )

    sections = [
        f"# {title}\n\n*Generated {ts} · [Research Notebook Generator](http://localhost:3000)*",
        f"## Abstract\n\n{req.abstract}",
        f"## Key Methodologies\n\n{bullets(req.methodologies)}",
        "## Algorithms & Techniques\n\n"
        + bullets(req.algorithms)
        + ("\n\n" + "\n\n".join(algo_fence(a) for a in req.algorithms) if req.algorithms else ""),
        "## Datasets\n\n" + bullets(req.datasets) + "\n\n```python\n"
        "import numpy as np\nimport pandas as pd\n\n"
        "# Replace with real data loading\nX = np.random.randn(1000, 10)\n```",
        f"## Results\n\n{req.results}",
        f"## Conclusions\n\n{req.conclusions}",
        "## References\n\n"
        f"- Source: **{title}**\n"
        "- Datasets: " + (", ".join(req.datasets) if req.datasets else "See paper"),
    ]
    return "\n\n---\n\n".join(sections) + "\n"


@app.post("/api/export-markdown", tags=["Notebook"])
async def export_markdown(request: "GenerateNotebookRequest"):
    """
    Convert GPT-4o analysis results to a GitHub-ready Markdown document (.md).
    """
    if not request.abstract.strip() and not request.results.strip():
        raise HTTPException(status_code=400, detail="Analysis result is empty — nothing to export.")

    md = _notebook_to_markdown(request)
    stem = (request.filename or "paper").replace(".pdf", "")
    filename = f"{stem}-notebook.md"

    logger.info("markdown_exported filename=%s size_bytes=%d", filename, len(md.encode()))
    return StreamingResponse(
        io.BytesIO(md.encode("utf-8")),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
