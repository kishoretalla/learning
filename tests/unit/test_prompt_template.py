import pytest

from backend.prompt_template import ANALYSIS_SYSTEM_PROMPT, MAX_TEXT_CHARS, build_analysis_contents, truncate_paper_text


@pytest.mark.unit
def test_system_prompt_contains_required_json_keys():
    for key in ["abstract", "methodologies", "algorithms", "datasets", "results", "conclusions"]:
        assert f'"{key}"' in ANALYSIS_SYSTEM_PROMPT


@pytest.mark.unit
def test_system_prompt_includes_grounding_instruction():
    assert "Do not invent unsupported facts" in ANALYSIS_SYSTEM_PROMPT
    assert "Not stated in paper" in ANALYSIS_SYSTEM_PROMPT


@pytest.mark.unit
def test_truncate_paper_text_respects_max_chars():
    source = "x" * (MAX_TEXT_CHARS + 500)

    truncated = truncate_paper_text(source)

    assert len(truncated) == MAX_TEXT_CHARS


@pytest.mark.unit
def test_build_analysis_contents_uses_deterministic_format():
    contents = build_analysis_contents("Paper body")

    assert contents.startswith(ANALYSIS_SYSTEM_PROMPT)
    assert contents.endswith("Paper body")
    assert "\n\nPaper text:\n\n" in contents