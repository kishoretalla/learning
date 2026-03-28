"""
Unit tests for the notebook quality validator script.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


def _write_notebook(nb: dict) -> Path:
    f = tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False)
    json.dump(nb, f)
    f.close()
    return Path(f.name)


def _run(path: Path) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, "tests/quality/validate_generated_notebook.py", str(path)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[2],
    )
    return result.returncode, result.stdout + result.stderr


GOOD_NOTEBOOK = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
        "language_info": {"name": "python"},
    },
    "cells": [
        {
            "cell_type": "markdown",
            "id": "md-abstract",
            "metadata": {},
            "source": (
                "# Attention Is All You Need\n\n"
                "## Abstract\n\n"
                "We propose the Transformer, a novel network architecture based solely on attention "
                "mechanisms, dispensing with recurrence and convolutions entirely."
            ),
        },
        {
            "cell_type": "markdown",
            "id": "md-methods",
            "metadata": {},
            "source": "## Key Methodologies\n\nSelf-attention, encoder-decoder.",
        },
        {
            "cell_type": "markdown",
            "id": "md-algos",
            "metadata": {},
            "source": "## Algorithms & Techniques\n\nScaled Dot-Product Attention.",
        },
        {
            "cell_type": "markdown",
            "id": "md-datasets",
            "metadata": {},
            "source": "## Datasets\n\nWMT 2014 English-German.",
        },
        {
            "cell_type": "markdown",
            "id": "md-results",
            "metadata": {},
            "source": "## Results\n\n28.4 BLEU on English-German.",
        },
        {
            "cell_type": "markdown",
            "id": "md-conclusions",
            "metadata": {},
            "source": "## Conclusions\n\nAttention-only models are effective.",
        },
        {
            "cell_type": "markdown",
            "id": "md-refs",
            "metadata": {},
            "source": (
                "## References\n\nVaswani et al., 2017.\n\n"
                "---\n*Disclaimer: Educational purposes only. "
                "Not a substitute for the original paper. Consult the original work.*"
            ),
        },
        {
            "cell_type": "code",
            "id": "code1",
            "metadata": {},
            "source": "def scaled_dot_product_attention(data):\n    raise NotImplementedError",
            "outputs": [],
            "execution_count": None,
        },
    ],
}


@pytest.mark.unit
def test_validator_passes_on_valid_notebook():
    path = _write_notebook(GOOD_NOTEBOOK)
    try:
        code, out = _run(path)
        assert code == 0, f"Expected exit 0, got {code}:\n{out}"
        assert "All required checks passed" in out
    finally:
        path.unlink(missing_ok=True)


@pytest.mark.unit
def test_validator_fails_missing_sections():
    nb = json.loads(json.dumps(GOOD_NOTEBOOK))
    # Replace source with one that omits all sections
    nb["cells"][0]["source"] = "just some text with no sections"
    path = _write_notebook(nb)
    try:
        code, out = _run(path)
        assert code == 1
        assert "Missing section" in out
    finally:
        path.unlink(missing_ok=True)


@pytest.mark.unit
def test_validator_fails_on_invalid_json():
    f = tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False)
    f.write("not valid json {{{")
    f.close()
    path = Path(f.name)
    try:
        code, out = _run(path)
        assert code == 1
        assert "Invalid JSON" in out
    finally:
        path.unlink(missing_ok=True)


@pytest.mark.unit
def test_validator_fails_on_missing_file():
    code, out = _run(Path("/tmp/no_such_notebook_xyz.json"))
    assert code == 1
    assert "not found" in out.lower() or "File not found" in out


@pytest.mark.unit
def test_validator_fails_on_short_abstract():
    nb = json.loads(json.dumps(GOOD_NOTEBOOK))
    # Replace the abstract cell (index 0) with only a short body
    nb["cells"][0]["source"] = "## Abstract\n\nShort."
    path = _write_notebook(nb)
    try:
        code, out = _run(path)
        assert code == 1
        assert "Abstract body too short" in out
    finally:
        path.unlink(missing_ok=True)


@pytest.mark.unit
def test_validator_fails_on_bad_python_syntax():
    nb = json.loads(json.dumps(GOOD_NOTEBOOK))
    # Replace the code cell (last cell) with a syntax error
    code_idx = next(i for i, c in enumerate(nb["cells"]) if c["cell_type"] == "code")
    nb["cells"][code_idx]["source"] = "def broken(:\n    pass"
    path = _write_notebook(nb)
    try:
        code, out = _run(path)
        assert code == 1
        assert "Syntax error" in out
    finally:
        path.unlink(missing_ok=True)
