"""
core/answer.py — LLM-synthesised answers with citations via Exa.
"""

from __future__ import annotations

from typing import Any

from cli_anything.exa.utils.exa_backend import get_client


def get_answer(query: str) -> dict[str, Any]:
    """Ask Exa a question and receive an LLM-synthesised answer with citations.

    Args:
        query: Natural-language question.

    Returns:
        Dict with keys: answer (str), citations (list[dict]).
    """
    client = get_client()
    response = client.answer(query, text=False)
    return _answer_to_dict(response)


def _answer_to_dict(response: Any) -> dict[str, Any]:
    """Convert an exa-py AnswerResponse to a plain dict."""
    out: dict[str, Any] = {}

    answer_text = getattr(response, "answer", None)
    if answer_text is not None:
        out["answer"] = answer_text

    citations = []
    for r in getattr(response, "results", []) or []:
        cite: dict[str, Any] = {}
        for attr in ("title", "url", "published_date", "author"):
            val = getattr(r, attr, None)
            if val is not None:
                cite[attr] = val
        citations.append(cite)
    out["citations"] = citations

    cost = getattr(response, "cost_dollars", None)
    if cost is not None:
        out["cost_dollars"] = cost

    return out
