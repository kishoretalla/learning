import re
import xml.etree.ElementTree as ET

import httpx


ARXIV_HOST_RE = re.compile(r"(?:https?://)?(?:www\.)?arxiv\.org/(?:abs|pdf)/(.+)$", re.IGNORECASE)
ARXIV_ID_RE = re.compile(r"^(?:[a-z\-]+(?:\.[A-Z]{2})?/)?\d{4}\.\d{4,5}(?:v\d+)?$|^[a-z\-]+(?:\.[A-Z]{2})?/\d{7}(?:v\d+)?$", re.IGNORECASE)
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def extract_arxiv_id(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise ValueError("arXiv input is empty")

    host_match = ARXIV_HOST_RE.match(candidate)
    if host_match:
        candidate = host_match.group(1)

    candidate = candidate.removesuffix(".pdf").strip("/")
    if not ARXIV_ID_RE.match(candidate):
        raise ValueError(f"Invalid arXiv identifier: {value}")

    return candidate


def build_abs_url(arxiv_id_or_url: str) -> str:
    arxiv_id = extract_arxiv_id(arxiv_id_or_url)
    return f"https://arxiv.org/abs/{arxiv_id}"


def build_pdf_url(arxiv_id_or_url: str) -> str:
    arxiv_id = extract_arxiv_id(arxiv_id_or_url)
    return f"https://arxiv.org/pdf/{arxiv_id}.pdf"


def parse_arxiv_atom(xml_text: str) -> dict[str, object]:
    root = ET.fromstring(xml_text)
    entry = root.find("atom:entry", ATOM_NS)
    if entry is None:
        raise ValueError("No arXiv entry found in response")

    title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
    summary = (entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").strip()
    published = (entry.findtext("atom:published", default="", namespaces=ATOM_NS) or "").strip()
    authors = [
        (author.findtext("atom:name", default="", namespaces=ATOM_NS) or "").strip()
        for author in entry.findall("atom:author", ATOM_NS)
    ]
    id_text = (entry.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()
    arxiv_id = extract_arxiv_id(id_text)

    return {
        "id": arxiv_id,
        "title": title,
        "summary": summary,
        "published": published,
        "authors": [author for author in authors if author],
        "abs_url": build_abs_url(arxiv_id),
        "pdf_url": build_pdf_url(arxiv_id),
    }


async def fetch_arxiv_metadata(arxiv_id_or_url: str, client: httpx.AsyncClient | None = None) -> dict[str, object]:
    arxiv_id = extract_arxiv_id(arxiv_id_or_url)
    api_url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"

    async def _fetch(active_client: httpx.AsyncClient) -> dict[str, object]:
        try:
            response = await active_client.get(api_url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Failed to fetch arXiv metadata: {exc}") from exc
        return parse_arxiv_atom(response.text)

    if client is not None:
        return await _fetch(client)

    async with httpx.AsyncClient(timeout=15.0) as active_client:
        return await _fetch(active_client)


def build_arxiv_text(metadata: dict[str, object]) -> str:
    authors = ", ".join(str(author) for author in metadata.get("authors", [])) or "Unknown authors"
    parts = [
        f"Title: {metadata.get('title', 'Untitled paper')}",
        f"Authors: {authors}",
        f"Published: {metadata.get('published', 'Unknown publish date')}",
        f"Abstract: {metadata.get('summary', 'No abstract provided.')}",
        f"arXiv URL: {metadata.get('abs_url', '')}",
        f"PDF URL: {metadata.get('pdf_url', '')}",
    ]
    return "\n\n".join(parts)