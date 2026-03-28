#!/usr/bin/env python3
"""
Validate a generated notebook produced by the Research Paper → Notebook app.

Usage:
    python tests/quality/validate_generated_notebook.py <path/to/notebook.ipynb>

Exit code 0 = all required checks passed.
Exit code 1 = one or more required checks failed.
"""
import ast
import json
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "## Abstract",
    "## Key Methodologies",
    "## Algorithms & Techniques",
    "## Datasets",
    "## Results",
    "## Conclusions",
    "## References",
]

SAFETY_PHRASES = [
    "disclaimer",
    "not a substitute",
    "verify",
    "consult the original",
    "educational",
]

MIN_ABSTRACT_CHARS = 80


def load_notebook(path: Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def check_nbformat(nb: dict) -> list[str]:
    errors = []
    if nb.get("nbformat") != 4:
        errors.append(f"Expected nbformat 4, got {nb.get('nbformat')}")
    if "cells" not in nb:
        errors.append("'cells' key missing from notebook")
    return errors


def _cell_source(cell: dict) -> str:
    """Return cell source as a plain string regardless of nbformat storage type."""
    src = cell.get("source", "")
    if isinstance(src, list):
        return "".join(src)
    return src


def check_required_sections(nb: dict) -> list[str]:
    markdown_text = "\n".join(
        _cell_source(cell)
        for cell in nb.get("cells", [])
        if cell.get("cell_type") == "markdown"
    )
    missing = [s for s in REQUIRED_SECTIONS if s not in markdown_text]
    return [f"Missing section: {s}" for s in missing]


def check_abstract_length(nb: dict) -> list[str]:
    for cell in nb.get("cells", []):
        src = _cell_source(cell)
        if "## Abstract" in src:
            # grab text after the heading line
            body = "\n".join(
                line for line in src.splitlines() if not line.startswith("#")
            ).strip()
            if len(body) < MIN_ABSTRACT_CHARS:
                return [
                    f"Abstract body too short ({len(body)} chars, minimum {MIN_ABSTRACT_CHARS})"
                ]
            return []
    return ["Abstract section found but could not measure body length"]


def check_python_syntax(nb: dict) -> list[str]:
    errors = []
    for i, cell in enumerate(nb.get("cells", []), start=1):
        if cell.get("cell_type") != "code":
            continue
        source = _cell_source(cell)
        if not source.strip():
            continue
        try:
            ast.parse(source)
        except SyntaxError as exc:
            errors.append(f"Syntax error in code cell {i}: {exc}")
    return errors


def check_safety_disclaimer(nb: dict) -> list[str]:
    text = "\n".join(
        _cell_source(cell)
        for cell in nb.get("cells", [])
        if cell.get("cell_type") == "markdown"
    ).lower()

    if not any(phrase in text for phrase in SAFETY_PHRASES):
        return ["Safety disclaimer not found (expected at least one of: " + ", ".join(SAFETY_PHRASES) + ")"]
    return []


def check_algorithm_stubs(nb: dict) -> list[str]:
    code_text = "\n".join(
        _cell_source(cell)
        for cell in nb.get("cells", [])
        if cell.get("cell_type") == "code"
    )
    if "NotImplementedError" not in code_text:
        return ["No algorithm stub cells found (expected at least one def ... raise NotImplementedError)"]
    return []


CHECKS = [
    ("nbformat validity", check_nbformat, True),
    ("required sections (8)", check_required_sections, True),
    ("abstract length", check_abstract_length, True),
    ("Python syntax", check_python_syntax, True),
    ("safety disclaimer", check_safety_disclaimer, True),
    ("algorithm stubs", check_algorithm_stubs, False),  # warning only
]


def run(notebook_path: str) -> int:
    path = Path(notebook_path)
    if not path.exists():
        print(f"ERROR: File not found: {notebook_path}", file=sys.stderr)
        return 1

    try:
        nb = load_notebook(path)
    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid JSON in notebook: {exc}", file=sys.stderr)
        return 1

    print(f"\nValidating: {path.name}\n{'=' * 50}")
    required_failures = 0

    for label, fn, is_required in CHECKS:
        issues = fn(nb)
        if not issues:
            print(f"  ✓  {label}")
        else:
            tag = "FAIL" if is_required else "WARN"
            for issue in issues:
                print(f"  {tag}  {label}: {issue}")
            if is_required:
                required_failures += len(issues)

    print(f"\n{'=' * 50}")
    if required_failures == 0:
        print("All required checks passed.\n")
        return 0
    else:
        print(f"{required_failures} required check(s) failed.\n")
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <notebook.ipynb>", file=sys.stderr)
        sys.exit(1)
    sys.exit(run(sys.argv[1]))
