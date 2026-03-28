MAX_TEXT_CHARS = 100_000

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
Do not invent unsupported facts. If information is not stated in the paper, say "Not stated in paper".
No markdown, no explanation, only the JSON object."""


def truncate_paper_text(text: str, max_chars: int = MAX_TEXT_CHARS) -> str:
    return text[:max_chars]


def build_analysis_contents(text: str) -> str:
    truncated = truncate_paper_text(text)
    return f"{ANALYSIS_SYSTEM_PROMPT}\n\nPaper text:\n\n{truncated}"