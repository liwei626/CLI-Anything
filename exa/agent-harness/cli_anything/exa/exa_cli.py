"""
exa_cli.py — CLI harness for Exa.

Provides a stateful, agent-native command-line interface for the Exa API:
  - web search (neural, keyword, or deep)
  - find-similar pages
  - fetch full page contents
  - LLM-synthesised answers with citations

Usage (non-interactive):
    cli-anything-exa search "AI safety papers 2024" --type deep --content highlights
    cli-anything-exa similar https://example.com --num-results 5
    cli-anything-exa contents https://example.com --content text
    cli-anything-exa answer "What is Exa's neural search?"
    cli-anything-exa --json search "latest LLM benchmarks" --num-results 3
    cli-anything-exa server status

Usage (interactive REPL):
    cli-anything-exa
"""

from __future__ import annotations

import json
import sys
from typing import Any

import click

from cli_anything.exa.core import answer as answer_core
from cli_anything.exa.core import search as search_core
from cli_anything.exa.core import session as session_core
from cli_anything.exa.utils.exa_backend import check_connectivity

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

_json_output: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _out(data: Any) -> None:
    """Emit output in JSON or human-readable form."""
    if _json_output:
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        _pretty(data)


def _pretty(data: Any) -> None:
    """Render a result dict in a human-readable format."""
    if isinstance(data, dict):
        if "results" in data:
            _print_results(data)
        elif "answer" in data:
            _print_answer(data)
        elif "ok" in data:
            status = "OK" if data["ok"] else "ERROR"
            click.echo(f"[{status}] {data.get('message', '')}")
        elif "total_queries" in data:
            click.echo(f"Queries this session : {data['total_queries']}")
            click.echo(f"Commands used        : {', '.join(data['commands_used']) or 'none'}")
            if data["last_query"]:
                click.echo(f"Last query           : {data['last_query']}")
        else:
            # Generic dict fallback
            for k, v in data.items():
                click.echo(f"{k}: {v}")
    elif isinstance(data, list):
        for item in data:
            _pretty(item)
    else:
        click.echo(str(data))


def _print_results(data: dict[str, Any]) -> None:
    results = data.get("results", [])
    if not results:
        click.echo("No results returned.")
        return
    click.echo(f"{'─' * 72}")
    for i, r in enumerate(results, 1):
        title = r.get("title") or "(no title)"
        url = r.get("url", "")
        date = r.get("published_date", "")
        author = r.get("author", "")

        click.echo(f"{i:>2}. {title}")
        click.echo(f"    {url}")
        meta_parts = []
        if date:
            meta_parts.append(date[:10])
        if author:
            meta_parts.append(f"by {author}")
        if meta_parts:
            click.echo(f"    {' · '.join(meta_parts)}")

        if r.get("highlights"):
            for h in r["highlights"]:
                click.echo(f"    › {h.strip()}")
        elif r.get("summary"):
            click.echo(f"    {r['summary'].strip()}")
        elif r.get("text"):
            snippet = r["text"][:300].replace("\n", " ").strip()
            click.echo(f"    {snippet}…")
        click.echo()

    cost = data.get("cost_dollars")
    if cost:
        total = cost.get("total", "") if isinstance(cost, dict) else cost
        click.echo(f"Cost: ${total}")
    click.echo(f"{'─' * 72}")


def _print_answer(data: dict[str, Any]) -> None:
    click.echo(f"\n{data.get('answer', '')}\n")
    citations = data.get("citations", [])
    if citations:
        click.echo("Sources:")
        for i, c in enumerate(citations, 1):
            click.echo(f"  {i}. {c.get('title') or c.get('url', '')}")
            click.echo(f"     {c.get('url', '')}")
    cost = data.get("cost_dollars")
    if cost:
        total = cost.get("total", "") if isinstance(cost, dict) else cost
        click.echo(f"\nCost: ${total}")


def _err(msg: str) -> None:
    if _json_output:
        click.echo(json.dumps({"error": msg}))
    else:
        click.echo(f"Error: {msg}", err=True)


def _handle_errors(fn):
    """Decorator: catch RuntimeError / Exception and emit consistent errors."""
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except RuntimeError as exc:
            _err(str(exc))
            sys.exit(1)
        except Exception as exc:  # noqa: BLE001
            _err(f"Unexpected error: {exc}")
            sys.exit(1)

    return wrapper


# ---------------------------------------------------------------------------
# CLI root
# ---------------------------------------------------------------------------

@click.group(invoke_without_command=True)
@click.option("--json", "use_json", is_flag=True, help="Emit machine-readable JSON output.")
@click.pass_context
def cli(ctx: click.Context, use_json: bool) -> None:
    """CLI harness for Exa — AI-powered web search and answer engine.

    Run without a subcommand to enter the interactive REPL.
    Set EXA_API_KEY in your environment before use.
    """
    global _json_output
    _json_output = use_json
    ctx.ensure_object(dict)

    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------

_SEARCH_TYPES = click.Choice(
    ["auto", "fast", "instant", "deep", "deep-reasoning"],
    case_sensitive=False,
)
_CONTENT_CHOICES = click.Choice(
    ["highlights", "text", "summary", "none"],
    case_sensitive=False,
)
_FRESHNESS_CHOICES = click.Choice(
    ["smart", "always", "never"],
    case_sensitive=False,
)
_CATEGORY_CHOICES = click.Choice(
    ["company", "people", "research-paper", "news", "personal-site", "financial-report"],
    case_sensitive=False,
)


@cli.command("search")
@click.argument("query")
@click.option("--type", "search_type", default="auto", show_default=True,
              type=_SEARCH_TYPES, help="Search mode.")
@click.option("--num-results", "-n", default=10, show_default=True,
              type=click.IntRange(1, 100), help="Number of results (1–100).")
@click.option("--category", type=_CATEGORY_CHOICES, default=None,
              help="Restrict to a specialised index.")
@click.option("--content", "content_mode", default="highlights", show_default=True,
              type=_CONTENT_CHOICES, help="Content to include with each result.")
@click.option("--freshness", default="smart", show_default=True,
              type=_FRESHNESS_CHOICES,
              help="Livecrawl policy: smart=cache+fallback, always=force-fresh, never=cache-only.")
@click.option("--include-domains", multiple=True, metavar="DOMAIN",
              help="Restrict results to these domains (repeatable).")
@click.option("--exclude-domains", multiple=True, metavar="DOMAIN",
              help="Exclude results from these domains (repeatable).")
@click.option("--from", "start_date", default=None, metavar="DATE",
              help="Only results published after this date (ISO 8601, e.g. 2024-01-01).")
@click.option("--to", "end_date", default=None, metavar="DATE",
              help="Only results published before this date (ISO 8601).")
@click.option("--location", default=None, metavar="CC",
              help="Geo-bias results to this two-letter country code (e.g. US).")
@_handle_errors
def search_cmd(
    query: str,
    search_type: str,
    num_results: int,
    category: str | None,
    content_mode: str,
    freshness: str,
    include_domains: tuple[str, ...],
    exclude_domains: tuple[str, ...],
    start_date: str | None,
    end_date: str | None,
    location: str | None,
) -> None:
    """Search the web using Exa's neural or deep search."""
    result = search_core.web_search(
        query,
        num_results=num_results,
        search_type=search_type,
        category=category,
        include_domains=include_domains,
        exclude_domains=exclude_domains,
        start_date=start_date,
        end_date=end_date,
        location=location,
        content_mode=content_mode,
        freshness=freshness,
    )
    session_core.record(query, "search", len(result.get("results", [])))
    _out(result)


# ---------------------------------------------------------------------------
# similar
# ---------------------------------------------------------------------------

@cli.command("similar")
@click.argument("url")
@click.option("--num-results", "-n", default=10, show_default=True,
              type=click.IntRange(1, 100), help="Number of results.")
@click.option("--content", "content_mode", default="highlights", show_default=True,
              type=_CONTENT_CHOICES, help="Content to include with each result.")
@_handle_errors
def similar_cmd(url: str, num_results: int, content_mode: str) -> None:
    """Find pages similar to a given URL."""
    result = search_core.find_similar(url, num_results=num_results, content_mode=content_mode)
    session_core.record(url, "similar", len(result.get("results", [])))
    _out(result)


# ---------------------------------------------------------------------------
# contents
# ---------------------------------------------------------------------------

@cli.command("contents")
@click.argument("urls", nargs=-1, required=True)
@click.option("--content", "content_mode", default="text", show_default=True,
              type=click.Choice(["text", "highlights", "summary"], case_sensitive=False),
              help="Content to retrieve.")
@click.option("--freshness", default="smart", show_default=True,
              type=_FRESHNESS_CHOICES,
              help="Livecrawl policy.")
@_handle_errors
def contents_cmd(urls: tuple[str, ...], content_mode: str, freshness: str) -> None:
    """Fetch full page contents for one or more URLs."""
    result = search_core.get_contents(list(urls), content_mode=content_mode, freshness=freshness)
    session_core.record(str(urls[0]), "contents", len(result.get("results", [])))
    _out(result)


# ---------------------------------------------------------------------------
# answer
# ---------------------------------------------------------------------------

@cli.command("answer")
@click.argument("query")
@_handle_errors
def answer_cmd(query: str) -> None:
    """Get an LLM-synthesised answer with cited sources."""
    result = answer_core.get_answer(query)
    session_core.record(query, "answer", len(result.get("citations", [])))
    _out(result)


# ---------------------------------------------------------------------------
# server
# ---------------------------------------------------------------------------

@cli.group("server")
def server_group() -> None:
    """Server and API connectivity commands."""


@server_group.command("status")
@_handle_errors
def server_status() -> None:
    """Check that the Exa API is reachable with your API key."""
    result = check_connectivity()
    _out(result)


# ---------------------------------------------------------------------------
# session
# ---------------------------------------------------------------------------

@cli.group("session")
def session_group() -> None:
    """Inspect the current REPL session state."""


@session_group.command("status")
def session_status() -> None:
    """Show a summary of activity in this session."""
    _out(session_core.get_status())


@session_group.command("history")
def session_history() -> None:
    """List queries made in this session (most recent first)."""
    history = session_core.get_history()
    if _json_output:
        click.echo(json.dumps(history, indent=2))
    else:
        if not history:
            click.echo("No queries yet.")
            return
        click.echo(f"{'Time':<10} {'Cmd':<10} {'Results':<9} Query")
        click.echo("─" * 72)
        for entry in history:
            click.echo(
                f"{entry['time']:<10} {entry['command']:<10} "
                f"{entry['results']:<9} {entry['query']}"
            )


# ---------------------------------------------------------------------------
# REPL
# ---------------------------------------------------------------------------

@cli.command("repl")
def repl() -> None:
    """Start the interactive REPL (default when no subcommand is given)."""
    try:
        from cli_anything.exa.utils.repl_skin import ReplSkin
    except ImportError:
        click.echo("prompt-toolkit is required for REPL mode: pip install prompt-toolkit")
        sys.exit(1)

    skin = ReplSkin(
        software_name="Exa",
        version="1.0.0",
        accent_color="cyan",
        skill_package="cli_anything.exa",
    )
    skin.print_banner()

    while True:
        try:
            user_input = skin.prompt()
        except (KeyboardInterrupt, EOFError):
            skin.print_goodbye()
            break

        line = user_input.strip()
        if not line:
            continue
        if line.lower() in ("exit", "quit", "q"):
            skin.print_goodbye()
            break

        # Dispatch the line as a CLI invocation
        try:
            args = line.split()
            cli.main(args=args, standalone_mode=False)
        except SystemExit:
            pass
        except Exception as exc:  # noqa: BLE001
            _err(str(exc))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    cli()


if __name__ == "__main__":
    main()
