# Manual Quality Validation — "Attention Is All You Need"

Use this checklist when running a real, visible-browser quality check against the
live Gemini API using the Vaswani et al. 2017 arXiv paper as the reference input.
The arXiv URL for this paper is: **https://arxiv.org/abs/1706.03762**

## Pre-requisites

- Application running locally (`docker compose up --build` or backend + frontend dev servers)
- A valid Gemini API key with quota available
- Python 3.10+ in PATH for the notebook validator script

## Steps

### 1 — Upload via arXiv URL

1. Open `http://localhost:3000/upload` in a **visible** browser window.
2. Paste `https://arxiv.org/abs/1706.03762` into the arXiv URL field.
3. Enter your Gemini API key.
4. Click **Generate Notebook**.

**Expected**: spinner appears, page transitions to `/processing`.

### 2 — Observe processing steps

On the processing page confirm all three steps complete with green checkmarks:

- [ ] Step 1 — Extracting paper content
- [ ] Step 2 — Analyzing with AI (may take 15–40 s)
- [ ] Step 3 — Generating notebook

### 3 — Download the notebook

1. Click **Download Notebook** on the success state.
2. Save the file as `attention_output.ipynb` in this directory.
3. Also click **Export as Markdown** and save as `attention_output.md`.

### 4 — Run the notebook validator

```bash
cd /path/to/repo
python tests/quality/validate_generated_notebook.py \
    tests/quality/attention_output.ipynb
```

All checks must pass (exit code 0).

### 5 — Manual spot-check

Open `attention_output.ipynb` in Jupyter or VS Code and verify:

- [ ] Title cell mentions "Attention" or "Transformer"
- [ ] Abstract section accurately describes the self-attention mechanism
- [ ] Methods section does **not** invent datasets or results not in the paper
- [ ] At least one algorithm stub `def ...(data):` is present
- [ ] Safety disclaimer is present in a Markdown cell
- [ ] All code cells contain syntactically valid Python (run the notebook; stubs will raise `NotImplementedError` — that is expected)

## Pass Criteria

| Criterion                                     | Required |
|-----------------------------------------------|----------|
| JSON notebook is valid per nbformat v4        | ✅ must pass |
| Exactly 8 required sections present           | ✅ must pass |
| All Python code cells have valid syntax       | ✅ must pass |
| Safety disclaimer present                     | ✅ must pass |
| Abstract ≥ 80 chars (not truncated/empty)     | ✅ must pass |
| No hallucinated non-attention datasets        | ⚠️ flag for review |
| Notebook executes without import errors       | ⚠️ flag for review |

## Failure Handling

If any required criterion fails, open a GitHub issue with:
- The failing section(s) output from the validator
- The raw `analysis` JSON from the processing page (available in browser sessionStorage under `analysis_result`)
- The Gemini API key tier used (Free / Paid)
