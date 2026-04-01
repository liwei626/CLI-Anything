"""
test_core.py — Unit tests for the Exa CLI harness.

All tests use mocks; no real API calls are made.
Run with: pytest tests/test_core.py -v
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from cli_anything.exa.exa_cli import cli
from cli_anything.exa.core import session as session_core
from cli_anything.exa.utils.exa_backend import build_contents_param, CATEGORY_SLUG_MAP


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_session():
    """Reset session history before each test."""
    session_core.clear()
    yield
    session_core.clear()


@pytest.fixture()
def runner():
    return CliRunner()


def _mock_result(n: int = 2):
    """Build a fake exa-py search result object using SimpleNamespace."""
    results = [
        SimpleNamespace(
            title=f"Result {i + 1}",
            url=f"https://example.com/{i + 1}",
            id=f"https://example.com/{i + 1}",
            published_date="2024-01-01",
            author=None,
            text=f"Body text for result {i + 1}.",
            highlights=[f"Highlight for result {i + 1}."],
            highlight_scores=[0.9],
            summary=None,
        )
        for i in range(n)
    ]
    return SimpleNamespace(results=results, cost_dollars={"total": 0.005})


def _mock_answer():
    citation = SimpleNamespace(
        title="Some Paper",
        url="https://example.com/paper",
        published_date="2024-01-01",
        author="Jane Doe",
    )
    return SimpleNamespace(
        answer="Exa uses neural embeddings for search.",
        results=[citation],
        cost_dollars={"total": 0.003},
    )
    return response


# ---------------------------------------------------------------------------
# Backend unit tests
# ---------------------------------------------------------------------------

class TestBuildContentsParam:
    def test_none_mode_returns_none(self):
        assert build_contents_param("none") is None

    def test_highlights_mode(self):
        result = build_contents_param("highlights")
        assert "highlights" in result
        assert result["highlights"]["max_characters"] == 4_000

    def test_text_mode(self):
        result = build_contents_param("text")
        assert "text" in result
        assert result["text"]["max_characters"] == 10_000

    def test_summary_mode(self):
        result = build_contents_param("summary")
        assert result["summary"] is True

    def test_freshness_always(self):
        result = build_contents_param("highlights", freshness="always")
        assert result["max_age_hours"] == 0

    def test_freshness_never(self):
        result = build_contents_param("highlights", freshness="never")
        assert result["max_age_hours"] == -1

    def test_freshness_smart_omits_key(self):
        result = build_contents_param("highlights", freshness="smart")
        assert "max_age_hours" not in result


class TestCategorySlugMap:
    def test_hyphenated_slugs_map_to_api_values(self):
        assert CATEGORY_SLUG_MAP["research-paper"] == "research paper"
        assert CATEGORY_SLUG_MAP["personal-site"] == "personal site"
        assert CATEGORY_SLUG_MAP["financial-report"] == "financial report"

    def test_simple_slugs_pass_through(self):
        assert CATEGORY_SLUG_MAP["news"] == "news"
        assert CATEGORY_SLUG_MAP["company"] == "company"


# ---------------------------------------------------------------------------
# Session unit tests
# ---------------------------------------------------------------------------

class TestSession:
    def test_empty_session(self):
        status = session_core.get_status()
        assert status["total_queries"] == 0
        assert status["last_query"] is None

    def test_record_and_history(self):
        session_core.record("test query", "search", 5)
        history = session_core.get_history()
        assert len(history) == 1
        assert history[0]["query"] == "test query"
        assert history[0]["results"] == 5

    def test_history_most_recent_first(self):
        session_core.record("first", "search", 1)
        session_core.record("second", "answer", 2)
        history = session_core.get_history()
        assert history[0]["query"] == "second"
        assert history[1]["query"] == "first"

    def test_status_after_records(self):
        session_core.record("q1", "search", 3)
        session_core.record("q2", "answer", 1)
        status = session_core.get_status()
        assert status["total_queries"] == 2
        assert "search" in status["commands_used"]
        assert "answer" in status["commands_used"]
        assert status["last_query"] == "q2"


# ---------------------------------------------------------------------------
# CLI parsing tests
# ---------------------------------------------------------------------------

class TestCLIHelp:
    def test_root_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Exa" in result.output

    def test_search_help(self, runner):
        result = runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "--type" in result.output
        assert "--num-results" in result.output
        assert "--content" in result.output

    def test_similar_help(self, runner):
        result = runner.invoke(cli, ["similar", "--help"])
        assert result.exit_code == 0
        assert "--num-results" in result.output

    def test_contents_help(self, runner):
        result = runner.invoke(cli, ["contents", "--help"])
        assert result.exit_code == 0

    def test_answer_help(self, runner):
        result = runner.invoke(cli, ["answer", "--help"])
        assert result.exit_code == 0

    def test_server_status_help(self, runner):
        result = runner.invoke(cli, ["server", "status", "--help"])
        assert result.exit_code == 0

    def test_session_help(self, runner):
        result = runner.invoke(cli, ["session", "--help"])
        assert result.exit_code == 0


class TestSearchCLI:
    @patch("cli_anything.exa.core.search.get_client")
    def test_basic_search(self, mock_get_client, runner):
        mock_client = MagicMock()
        mock_client.search.return_value = _mock_result(2)
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["search", "AI research"])
        assert result.exit_code == 0
        mock_client.search.assert_called_once()
        call_kwargs = mock_client.search.call_args
        assert call_kwargs[0][0] == "AI research"

    @patch("cli_anything.exa.core.search.get_client")
    def test_search_json_output(self, mock_get_client, runner):
        mock_client = MagicMock()
        mock_client.search.return_value = _mock_result(1)
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["--json", "search", "test query"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "results" in data
        assert len(data["results"]) == 1

    @patch("cli_anything.exa.core.search.get_client")
    def test_search_type_flag(self, mock_get_client, runner):
        mock_client = MagicMock()
        mock_client.search.return_value = _mock_result(1)
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["search", "deep query", "--type", "deep"])
        assert result.exit_code == 0
        _, kwargs = mock_client.search.call_args
        assert kwargs.get("type") == "deep"

    @patch("cli_anything.exa.core.search.get_client")
    def test_search_num_results_flag(self, mock_get_client, runner):
        mock_client = MagicMock()
        mock_client.search.return_value = _mock_result(5)
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["search", "test", "--num-results", "5"])
        assert result.exit_code == 0
        _, kwargs = mock_client.search.call_args
        assert kwargs.get("num_results") == 5

    @patch("cli_anything.exa.core.search.get_client")
    def test_search_include_domains(self, mock_get_client, runner):
        mock_client = MagicMock()
        mock_client.search.return_value = _mock_result(1)
        mock_get_client.return_value = mock_client

        result = runner.invoke(
            cli, ["search", "test", "--include-domains", "arxiv.org", "--include-domains", "nature.com"]
        )
        assert result.exit_code == 0
        _, kwargs = mock_client.search.call_args
        assert "arxiv.org" in kwargs.get("include_domains", [])

    @patch("cli_anything.exa.core.search.get_client")
    def test_search_invalid_type_rejected(self, mock_get_client, runner):
        result = runner.invoke(cli, ["search", "test", "--type", "bogus"])
        assert result.exit_code != 0


class TestSimilarCLI:
    @patch("cli_anything.exa.core.search.get_client")
    def test_basic_similar(self, mock_get_client, runner):
        mock_client = MagicMock()
        mock_client.find_similar.return_value = _mock_result(3)
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["similar", "https://example.com"])
        assert result.exit_code == 0
        mock_client.find_similar.assert_called_once()

    @patch("cli_anything.exa.core.search.get_client")
    def test_similar_json_output(self, mock_get_client, runner):
        mock_client = MagicMock()
        mock_client.find_similar.return_value = _mock_result(2)
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["--json", "similar", "https://example.com"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "results" in data


class TestContentsCLI:
    @patch("cli_anything.exa.core.search.get_client")
    def test_basic_contents(self, mock_get_client, runner):
        mock_client = MagicMock()
        mock_client.get_contents.return_value = _mock_result(1)
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["contents", "https://example.com"])
        assert result.exit_code == 0
        mock_client.get_contents.assert_called_once()

    @patch("cli_anything.exa.core.search.get_client")
    def test_contents_multiple_urls(self, mock_get_client, runner):
        mock_client = MagicMock()
        mock_client.get_contents.return_value = _mock_result(2)
        mock_get_client.return_value = mock_client

        result = runner.invoke(
            cli, ["contents", "https://example.com/a", "https://example.com/b"]
        )
        assert result.exit_code == 0
        args, _ = mock_client.get_contents.call_args
        assert len(args[0]) == 2


class TestAnswerCLI:
    @patch("cli_anything.exa.core.answer.get_client")
    def test_basic_answer(self, mock_get_client, runner):
        mock_client = MagicMock()
        mock_client.answer.return_value = _mock_answer()
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["answer", "What is Exa?"])
        assert result.exit_code == 0
        assert "neural embeddings" in result.output

    @patch("cli_anything.exa.core.answer.get_client")
    def test_answer_json_output(self, mock_get_client, runner):
        mock_client = MagicMock()
        mock_client.answer.return_value = _mock_answer()
        mock_get_client.return_value = mock_client

        result = runner.invoke(cli, ["--json", "answer", "What is Exa?"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "answer" in data
        assert "citations" in data


class TestServerCLI:
    @patch("cli_anything.exa.exa_cli.check_connectivity")
    def test_server_status_ok(self, mock_check, runner):
        mock_check.return_value = {"ok": True, "message": "API key valid — Exa reachable"}
        result = runner.invoke(cli, ["server", "status"])
        assert result.exit_code == 0
        assert "OK" in result.output

    @patch("cli_anything.exa.exa_cli.check_connectivity")
    def test_server_status_error(self, mock_check, runner):
        mock_check.return_value = {"ok": False, "message": "EXA_API_KEY not set"}
        result = runner.invoke(cli, ["server", "status"])
        assert result.exit_code == 0
        assert "ERROR" in result.output

    @patch("cli_anything.exa.exa_cli.check_connectivity")
    def test_server_status_json(self, mock_check, runner):
        mock_check.return_value = {"ok": True, "message": "OK"}
        result = runner.invoke(cli, ["--json", "server", "status"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True


class TestSessionCLI:
    @patch("cli_anything.exa.core.search.get_client")
    def test_session_status_after_search(self, mock_get_client, runner):
        mock_client = MagicMock()
        mock_client.search.return_value = _mock_result(3)
        mock_get_client.return_value = mock_client

        runner.invoke(cli, ["search", "test query"])
        result = runner.invoke(cli, ["session", "status"])
        assert result.exit_code == 0
        assert "1" in result.output  # total_queries

    def test_session_history_empty(self, runner):
        result = runner.invoke(cli, ["session", "history"])
        assert result.exit_code == 0
        assert "No queries" in result.output

    @patch("cli_anything.exa.core.search.get_client")
    def test_session_history_json(self, mock_get_client, runner):
        mock_client = MagicMock()
        mock_client.search.return_value = _mock_result(2)
        mock_get_client.return_value = mock_client

        runner.invoke(cli, ["search", "test"])
        result = runner.invoke(cli, ["--json", "session", "history"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert data[0]["query"] == "test"


class TestErrorHandling:
    @patch("cli_anything.exa.core.search.get_client")
    def test_runtime_error_produces_json_error(self, mock_get_client, runner):
        mock_get_client.side_effect = RuntimeError("EXA_API_KEY environment variable is not set.")
        result = runner.invoke(cli, ["--json", "search", "test"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data

    def test_missing_query_argument(self, runner):
        result = runner.invoke(cli, ["search"])
        assert result.exit_code != 0
