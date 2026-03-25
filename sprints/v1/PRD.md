# Sprint v1 — PRD: Research Paper → Jupyter Notebook Generator

## Overview

Build an MVP web application where researchers upload research PDFs and receive publication-ready Jupyter notebooks with extracted methodologies, algorithms, synthetic data experiments, and reproducible code. The app accepts an OpenAI API key, processes the PDF using GPT-4o with extended reasoning, and delivers a .ipynb file or direct Google Colab link. Beautiful UI inspired by ARC Prize design language.

## Goals

- User can enter OpenAI API key securely (client-side, never stored)
- User can upload PDF file (research papers, 1-10 MB)
- Backend extracts paper structure (abstract, methodology, algorithms, results)
- Generate a richly-structured .ipynb notebook with synthetic experiments
- User can download .ipynb OR open directly in Google Colab
- Progress UI shows real-time step narrative (parsing → analyzing → generating)
- Notebook is publication-ready for OpenAI/DeepMind-tier researchers
- No authentication/tracking in v1 (no user accounts)

## User Stories

- As a researcher, I want to upload a PDF and get an executable notebook, so I can quickly replicate paper findings without manual transcription
- As an AI researcher, I want the notebook to have synthetic data experiments, so I can understand the algorithm without original datasets
- As an OpenAI researcher, I want the notebook to be well-structured with clear methodology → algorithm → experiments flow, so I can efficiently review and extend the work
- As a user, I want to see live progress (not a blank loading bar), so I don't feel disengaged while the notebook generates

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Browser (React + Next.js 14)                                │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Input Form   │→ │  Upload PDF  │→ │  Progress    │     │
│  │ (API Key)    │  │  + Send File │  │  (Real-time) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                              │              │
│                                              ▼              │
│                                    ┌──────────────────┐    │
│                                    │ Download/Colab   │    │
│                                    │ Link Screen      │    │
│                                    └──────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ POST /api/generate-notebook
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Backend (Python FastAPI + Node.js edge proxy)              │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ PDF Parser   │→ │ GPT-4o       │→ │ Notebook     │     │
│  │ (PyPDF2,     │  │ Analyzer     │  │ Generator    │     │
│  │  pdfplumber) │  │ (Extended    │  │ (nbformat)   │     │
│  │              │  │  thinking)   │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                 │                    │            │
│         ▼                 ▼                    ▼            │
│  ┌──────────────────────────────────────────────────┐     │
│  │ Stream Progress Events via SSE                   │     │
│  │ ("Parsing PDF...", "Extracting methodology...") │     │
│  └──────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ OpenAI API       │
                    │ (GPT-4o)         │
                    └──────────────────┘
```

**Frontend:**
- Next.js 14 (App Router) + React + TypeScript
- Tailwind CSS (inspired by ARC Prize minimalist aesthetic)
- Beautiful gradient backgrounds + clean typography
- Client-side API key input (never persisted)

**Backend:**
- Python FastAPI for PDF processing + notebook generation
- Node.js edge proxy in Next.js for direct OpenAI calls
- SSE (Server-Sent Events) for real-time progress updates
- nbformat for Jupyter notebook generation
- PyPDF2 / pdfplumber for PDF parsing

**Notebook Structure:**
- Markdown cells: Abstract, Problem Statement, Methodology, Limitations
- Code cells: Algorithm pseudocode + Python implementation
- Synthetic data generation (realistic, not toy)
- Visualization cells (matplotlib/plotly)
- Experiment cells with results
- References section
- Google Colab button at top

**Deployment:**
- localhost:3000 for v1 (Next.js dev server)
- Backend runs on localhost:8000 (FastAPI)

## Out of Scope (v2+)

- User authentication / sign-up
- Usage tracking / analytics
- Rate limiting (v2 with auth)
- PDF file storage (v2 with S3 or persistent storage)
- Advanced PDF OCR for scanned papers
- Multi-language support
- Real research paper datasets (v2+)
- Export to other formats (LaTeX, HTML)
- Real-time collaboration
- Paper comparison workflows

## Dependencies

- None (greenfield project)
- OpenAI API account required (user brings their own API key)
- Google Colab (free, no setup needed for links)

## Out of Scope Details

**Why not X?**
- No database in v1: PDFs are processed on-demand, not stored
- No auth in v1: Simplifies MVP, scaling later is easy
- No advanced PDF OCR: Assume clean PDFs (research papers are usually well-formatted)
- No multi-model support: GPT-4o is best for this task, pick one and nail it
