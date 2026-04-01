"""
core/session.py — In-session state for the interactive REPL.

Tracks search history and current context so the REPL banner and
`session history` command have something to display.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class _SearchEntry:
    query: str
    command: str  # "search" | "similar" | "contents" | "answer"
    result_count: int
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))


_history: list[_SearchEntry] = []


def record(query: str, command: str, result_count: int) -> None:
    """Add an entry to the in-session history."""
    _history.append(_SearchEntry(query=query, command=command, result_count=result_count))


def get_history() -> list[dict[str, Any]]:
    """Return history as a list of plain dicts (most recent first)."""
    return [
        {
            "time": e.timestamp,
            "command": e.command,
            "query": e.query,
            "results": e.result_count,
        }
        for e in reversed(_history)
    ]


def get_status() -> dict[str, Any]:
    """Return a summary of the current session."""
    return {
        "total_queries": len(_history),
        "commands_used": sorted({e.command for e in _history}) or [],
        "last_query": _history[-1].query if _history else None,
    }


def clear() -> None:
    """Clear all history (used in tests)."""
    _history.clear()
