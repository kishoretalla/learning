# Real Quality Test Report (Attention Is All You Need)

Date: 2026-03-28
Mode: Real browser E2E (Playwright, live backend/frontend, real Gemini API)
Input: https://arxiv.org/abs/1706.03762

## Evidence (Screenshots)

1. Upload ready: tests/quality/screenshots/real-quality-01-upload-ready.png
2. Processing: tests/quality/screenshots/real-quality-02-processing.png
3. Success state: tests/quality/screenshots/real-quality-03-success.png

## Artifacts Generated

- Notebook: tests/quality/attention_output.ipynb
- Markdown: tests/quality/attention_output.md

## Validator Run

Command:

```bash
/Users/kishoretallapragada/Downloads/MSD-PRD/.venv/bin/python tests/quality/validate_generated_notebook.py tests/quality/attention_output.ipynb
```

Result: PASSED

Passed checks:
- nbformat validity
- required sections (8)
- abstract length
- Python syntax
- safety disclaimer
- algorithm stubs

## Conclusion

The real end-to-end generation flow works and produces downloadable notebook/markdown outputs, and the generated notebook passes all required quality gates.

## Fix Applied

Added a dedicated disclaimer in generated notebook references markdown and markdown export output in backend/notebook_generator.py.
