"""Unit tests for the Markdown → Confluence Storage Format converter and adapter."""

from unittest.mock import MagicMock, patch

import pytest

from adapters.atlassian.confluence import ConfluenceAdapter, _cf_table, md_to_confluence_storage
from src.core.config import AtlassianConfig, ConfluenceConfig, JiraConfig


def _make_config() -> MagicMock:
    cfg = MagicMock()
    cfg.atlassian = AtlassianConfig(
        confluence=ConfluenceConfig(
            base_url="http://atlassian.test/wiki",
            space_key="QMS",
            email="admin@test.com",
        ),
        jira=JiraConfig(
            base_url="http://atlassian.test",
            project_key="QMS",
            email="admin@test.com",
        ),
    )
    return cfg


class TestMdToConfluenceStorage:
    def test_h1(self) -> None:
        assert md_to_confluence_storage("# Title") == "<h1>Title</h1>"

    def test_h2(self) -> None:
        assert md_to_confluence_storage("## Section") == "<h2>Section</h2>"

    def test_h3(self) -> None:
        assert md_to_confluence_storage("### Sub") == "<h3>Sub</h3>"

    def test_hr(self) -> None:
        assert md_to_confluence_storage("---") == "<hr/>"

    def test_bold(self) -> None:
        assert "<strong>bold</strong>" in md_to_confluence_storage("**bold** text")

    def test_italic_asterisk(self) -> None:
        assert "<em>italic</em>" in md_to_confluence_storage("*italic* text")

    def test_italic_underscore(self) -> None:
        assert "<em>italic</em>" in md_to_confluence_storage("_italic_ text")

    def test_link(self) -> None:
        result = md_to_confluence_storage("[Atlassian](https://atlassian.com)")
        assert '<a href="https://atlassian.com">Atlassian</a>' in result

    def test_inline_code(self) -> None:
        assert "<code>cmd</code>" in md_to_confluence_storage("`cmd` here")

    def test_unordered_list_grouped(self) -> None:
        result = md_to_confluence_storage("- a\n- b\n- c")
        assert result.startswith("<ul>")
        assert result.count("<li>") == 3
        assert result.count("<ul>") == 1

    def test_ordered_list_grouped(self) -> None:
        result = md_to_confluence_storage("1. x\n2. y")
        assert result.startswith("<ol>")
        assert result.count("<li>") == 2

    def test_blockquote(self) -> None:
        result = md_to_confluence_storage("> note")
        assert "<blockquote>" in result
        assert "note" in result

    def test_paragraph(self) -> None:
        assert md_to_confluence_storage("hello world") == "<p>hello world</p>"

    def test_empty_line(self) -> None:
        result = md_to_confluence_storage("a\n\nb")
        assert result == "<p>a</p>\n\n<p>b</p>"


class TestCfTable:
    def test_header_uses_th(self) -> None:
        lines = ["| A | B |", "|---|---|", "| 1 | 2 |"]
        result = _cf_table(lines)
        assert "<th>A</th>" in result
        assert "<th>B</th>" in result

    def test_data_uses_td(self) -> None:
        lines = ["| A | B |", "|---|---|", "| 1 | 2 |"]
        result = _cf_table(lines)
        assert "<td>1</td>" in result

    def test_separator_skipped(self) -> None:
        lines = ["| A |", "|---|", "| x |"]
        result = _cf_table(lines)
        assert "---" not in result


class TestConfluenceAdapter:
    def test_raises_if_no_atlassian_config(self) -> None:
        cfg = MagicMock()
        cfg.atlassian = None
        with pytest.raises(ValueError, match="atlassian config block"):
            ConfluenceAdapter(cfg)

    def test_base_url_trailing_slash_stripped(self) -> None:
        adapter = ConfluenceAdapter(_make_config())
        assert not adapter._base_url.endswith("/")

    def test_get_page_id_returns_none_on_empty(self) -> None:
        adapter = ConfluenceAdapter(_make_config())
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": []}
        mock_resp.raise_for_status.return_value = None
        with patch("adapters.atlassian.confluence.requests.get", return_value=mock_resp):
            assert adapter.get_page_id("Missing Page") is None

    def test_get_page_id_returns_id_when_found(self) -> None:
        adapter = ConfluenceAdapter(_make_config())
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": [{"id": "42"}]}
        mock_resp.raise_for_status.return_value = None
        with patch("adapters.atlassian.confluence.requests.get", return_value=mock_resp):
            assert adapter.get_page_id("Existing Page") == "42"
