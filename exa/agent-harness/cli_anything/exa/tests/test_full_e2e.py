"""
test_full_e2e.py — End-to-end tests against the real Exa API.

Requires: EXA_API_KEY set in the environment.
Run with: pytest tests/test_full_e2e.py -v

These tests make real API calls and consume credits. They verify that:
  - The CLI produces parseable JSON output
  - Results contain expected fields
  - All subcommands route correctly to the API
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from click.testing import CliRunner
from cli_anything.exa.exa_cli import cli
from cli_anything.exa.core import session as session_core


# ---------------------------------------------------------------------------
# Skip guard
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.skipif(
    not os.environ.get("EXA_API_KEY"),
    reason="EXA_API_KEY not set — skipping E2E tests",
)


@pytest.fixture(autouse=True)
def clear_session():
    session_core.clear()
    yield
    session_core.clear()


@pytest.fixture()
def runner():
    return CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_cli() -> list[str]:
    """Return the command prefix to invoke cli-anything-exa."""
    cmd = "cli-anything-exa"
    result = subprocess.run(["which", cmd], capture_output=True, text=True)
    if result.returncode == 0:
        return [cmd]
    # Fall back to module invocation
    return [sys.executable, "-m", "cli_anything.exa"]


def _run(*args: str) -> subprocess.CompletedProcess:
    prefix = _resolve_cli()
    return subprocess.run(
        prefix + list(args),
        capture_output=True,
        text=True,
        env={**os.environ},
    )


# ---------------------------------------------------------------------------
# server status
# ---------------------------------------------------------------------------

class TestServerStatusE2E:
    def test_status_ok(self):
        proc = _run("server", "status")
        assert proc.returncode == 0
        assert "OK" in proc.stdout

    def test_status_json(self):
        proc = _run("--json", "server", "status")
        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert data["ok"] is True
        assert "message" in data


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------

class TestSearchE2E:
    def test_basic_search_returns_results(self, runner):
        result = runner.invoke(cli, ["--json", "search", "large language models 2024"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "results" in data
        assert len(data["results"]) > 0

    def test_search_result_has_required_fields(self, runner):
        result = runner.invoke(cli, ["--json", "search", "AI safety research", "--num-results", "3"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        r = data["results"][0]
        assert "url" in r
        assert "title" in r

    def test_search_highlights_content(self, runner):
        result = runner.invoke(
            cli, ["--json", "search", "neural search algorithms", "--content", "highlights"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        r = data["results"][0]
        assert "highlights" in r
        assert isinstance(r["highlights"], list)
        assert len(r["highlights"]) > 0

    def test_search_text_content(self, runner):
        result = runner.invoke(
            cli, ["--json", "search", "machine learning overview", "--content", "text", "--num-results", "1"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        r = data["results"][0]
        assert "text" in r
        assert len(r["text"]) > 50

    def test_search_category_news(self, runner):
        result = runner.invoke(
            cli, ["--json", "search", "AI regulation", "--category", "news", "--num-results", "3"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["results"]) > 0

    def test_search_domain_filter(self, runner):
        result = runner.invoke(
            cli,
            ["--json", "search", "machine learning", "--include-domains", "arxiv.org", "--num-results", "3"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        for r in data["results"]:
            assert "arxiv.org" in r["url"]

    def test_search_num_results_respected(self, runner):
        result = runner.invoke(cli, ["--json", "search", "AI research", "--num-results", "5"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["results"]) <= 5

    def test_search_human_readable_output(self, runner):
        result = runner.invoke(cli, ["search", "Exa search API"])
        assert result.exit_code == 0
        assert "http" in result.output  # URL is shown

    def test_search_records_session(self, runner):
        runner.invoke(cli, ["--json", "search", "test query"])
        status = session_core.get_status()
        assert status["total_queries"] == 1
        assert status["last_query"] == "test query"


# ---------------------------------------------------------------------------
# similar
# ---------------------------------------------------------------------------

class TestSimilarE2E:
    def test_basic_similar(self, runner):
        result = runner.invoke(
            cli, ["--json", "similar", "https://arxiv.org/abs/2303.08774", "--num-results", "3"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "results" in data
        assert len(data["results"]) > 0

    def test_similar_result_fields(self, runner):
        result = runner.invoke(
            cli, ["--json", "similar", "https://openai.com/research/gpt-4", "--num-results", "2"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        r = data["results"][0]
        assert "url" in r
        assert "title" in r


# ---------------------------------------------------------------------------
# contents
# ---------------------------------------------------------------------------

class TestContentsE2E:
    def test_basic_contents(self, runner):
        result = runner.invoke(
            cli, ["--json", "contents", "https://exa.ai", "--content", "text"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "results" in data
        assert len(data["results"]) > 0

    def test_contents_text_field_present(self, runner):
        result = runner.invoke(
            cli, ["--json", "contents", "https://exa.ai", "--content", "text"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        r = data["results"][0]
        assert "text" in r
        assert len(r["text"]) > 0

    def test_contents_multiple_urls(self, runner):
        result = runner.invoke(
            cli,
            ["--json", "contents", "https://exa.ai", "https://arxiv.org", "--content", "highlights"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["results"]) >= 1


# ---------------------------------------------------------------------------
# answer
# ---------------------------------------------------------------------------

class TestAnswerE2E:
    def test_basic_answer(self, runner):
        result = runner.invoke(cli, ["--json", "answer", "What is Exa's neural search?"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "answer" in data
        assert len(data["answer"]) > 10

    def test_answer_has_citations(self, runner):
        result = runner.invoke(cli, ["--json", "answer", "How does Exa differ from Google?"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "citations" in data
        assert isinstance(data["citations"], list)

    def test_answer_human_readable(self, runner):
        result = runner.invoke(cli, ["answer", "What is RAG in AI?"])
        assert result.exit_code == 0
        assert len(result.output.strip()) > 0


# ---------------------------------------------------------------------------
# subprocess (entry-point) smoke test
# ---------------------------------------------------------------------------

class TestEntryPoint:
    def test_cli_entry_point_help(self):
        proc = _run("--help")
        assert proc.returncode == 0
        assert "Exa" in proc.stdout

    def test_cli_entry_point_search(self):
        proc = _run("--json", "search", "Exa API overview", "--num-results", "2")
        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert "results" in data
