from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from backend.arxiv_fetcher import build_abs_url, build_pdf_url, extract_arxiv_id, fetch_arxiv_metadata, parse_arxiv_atom


SAMPLE_ARXIV_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/1706.03762v7</id>
    <published>2017-06-12T17:57:25Z</published>
    <title>Attention Is All You Need</title>
    <summary>We propose the Transformer, a new simple network architecture.</summary>
    <author><name>Ashish Vaswani</name></author>
    <author><name>Noam Shazeer</name></author>
  </entry>
</feed>
"""


@pytest.mark.unit
def test_extract_arxiv_id_supports_abs_and_pdf_urls():
    assert extract_arxiv_id("https://arxiv.org/abs/1706.03762v7") == "1706.03762v7"
    assert extract_arxiv_id("https://arxiv.org/pdf/1706.03762v7.pdf") == "1706.03762v7"


@pytest.mark.unit
def test_extract_arxiv_id_rejects_invalid_values():
    with pytest.raises(ValueError, match="Invalid arXiv identifier"):
        extract_arxiv_id("https://example.com/paper")


@pytest.mark.unit
def test_build_urls_are_derived_from_identifier():
    assert build_abs_url("1706.03762v7") == "https://arxiv.org/abs/1706.03762v7"
    assert build_pdf_url("1706.03762v7") == "https://arxiv.org/pdf/1706.03762v7.pdf"


@pytest.mark.unit
def test_parse_arxiv_atom_extracts_metadata():
    metadata = parse_arxiv_atom(SAMPLE_ARXIV_ATOM)

    assert metadata["id"] == "1706.03762v7"
    assert metadata["title"] == "Attention Is All You Need"
    assert metadata["authors"] == ["Ashish Vaswani", "Noam Shazeer"]
    assert metadata["pdf_url"] == "https://arxiv.org/pdf/1706.03762v7.pdf"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_arxiv_metadata_raises_runtime_error_on_network_failure():
    client = AsyncMock()
    client.get.side_effect = httpx.ConnectError("boom")

    with pytest.raises(RuntimeError, match="Failed to fetch arXiv metadata"):
        await fetch_arxiv_metadata("1706.03762v7", client=client)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_arxiv_metadata_returns_parsed_payload():
    response = MagicMock()
    response.text = SAMPLE_ARXIV_ATOM
    response.raise_for_status.return_value = None

    client = AsyncMock()
    client.get.return_value = response

    metadata = await fetch_arxiv_metadata("1706.03762v7", client=client)

    assert metadata["title"] == "Attention Is All You Need"