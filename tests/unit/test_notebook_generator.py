import nbformat
import pytest

from backend.notebook_generator import NotebookContent, algo_stub, build_notebook, generate_title_from_abstract, notebook_to_markdown


SAMPLE_CONTENT = NotebookContent(
    abstract="Transformers improve sequence modeling. They remove recurrence and rely on attention.",
    methodologies=["self-attention", "encoder-decoder architecture"],
    algorithms=["Scaled Dot-Product Attention", "Multi-Head Attention"],
    datasets=["WMT 2014 English-German"],
    results="The transformer achieves better BLEU with less training cost.",
    conclusions="Attention-only architectures are effective and parallelizable.",
    filename="attention-is-all-you-need.pdf",
)


@pytest.mark.unit
def test_generate_title_from_abstract_prefers_first_sentence():
    title = generate_title_from_abstract(SAMPLE_CONTENT.abstract)

    assert title == "Transformers improve sequence modeling"


@pytest.mark.unit
def test_generate_title_from_abstract_falls_back_for_empty_input():
    assert generate_title_from_abstract("   ") == "Research Analysis"


@pytest.mark.unit
def test_algo_stub_generates_python_identifier():
    stub = algo_stub("Multi-Head Attention")

    assert "def multi_head_attention(data):" in stub
    assert "raise NotImplementedError" in stub


@pytest.mark.unit
def test_build_notebook_returns_valid_notebook():
    notebook = build_notebook(SAMPLE_CONTENT)

    nbformat.validate(notebook)
    assert notebook.metadata["kernelspec"]["name"] == "python3"


@pytest.mark.unit
def test_build_notebook_contains_required_sections():
    notebook = build_notebook(SAMPLE_CONTENT)
    markdown_text = "\n".join(cell.source for cell in notebook.cells if cell.cell_type == "markdown")

    for section in ["## Abstract", "## Key Methodologies", "## Algorithms & Techniques", "## Datasets", "## Results", "## Conclusions", "## References"]:
        assert section in markdown_text


@pytest.mark.unit
def test_build_notebook_creates_one_stub_per_algorithm():
    notebook = build_notebook(SAMPLE_CONTENT)
    code_cells = [cell.source for cell in notebook.cells if cell.cell_type == "code"]
    stub_cells = [cell for cell in code_cells if "NotImplementedError" in cell]

    assert len(stub_cells) == len(SAMPLE_CONTENT.algorithms)


@pytest.mark.unit
def test_notebook_to_markdown_contains_all_main_sections():
    markdown = notebook_to_markdown(SAMPLE_CONTENT)

    for section in ["# attention-is-all-you-need", "## Abstract", "## Key Methodologies", "## Algorithms & Techniques", "## Datasets", "## Results", "## Conclusions", "## References"]:
        assert section in markdown