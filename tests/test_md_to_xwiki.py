"""Unit tests for the Markdown → XWiki 2.1 converter."""

from adapters.selfhosted.xwiki import md_to_xwiki


class TestHeadings:
    def test_h1(self) -> None:
        assert md_to_xwiki("# Title") == "= Title ="

    def test_h2(self) -> None:
        assert md_to_xwiki("## Section") == "== Section =="

    def test_h3(self) -> None:
        assert md_to_xwiki("### Sub") == "=== Sub ==="


class TestHorizontalRule:
    def test_dashes(self) -> None:
        assert md_to_xwiki("---") == "----"

    def test_long_dashes(self) -> None:
        assert md_to_xwiki("-------") == "----"


class TestInline:
    def test_bold_preserved(self) -> None:
        assert "**bold**" in md_to_xwiki("**bold** text")

    def test_italic_asterisk(self) -> None:
        assert "//italic//" in md_to_xwiki("*italic* text")

    def test_italic_underscore(self) -> None:
        assert "//italic//" in md_to_xwiki("_italic_ text")

    def test_markdown_link(self) -> None:
        result = md_to_xwiki("[XWiki](https://xwiki.org)")
        assert "[[XWiki>>https://xwiki.org]]" in result


class TestTables:
    def test_header_row_uses_equals(self) -> None:
        table = "| Col A | Col B |\n|-------|-------|\n| a | b |"
        result = md_to_xwiki(table)
        assert "|=Col A|=Col B" in result

    def test_data_row_no_equals(self) -> None:
        table = "| Col A | Col B |\n|-------|-------|\n| a | b |"
        result = md_to_xwiki(table)
        assert "|a|b" in result

    def test_separator_row_skipped(self) -> None:
        table = "| A |\n|---|\n| b |"
        result = md_to_xwiki(table)
        assert "---" not in result


class TestLists:
    def test_unordered_dash(self) -> None:
        assert md_to_xwiki("- item") == "* item"

    def test_unordered_asterisk(self) -> None:
        assert md_to_xwiki("* item") == "* item"

    def test_ordered(self) -> None:
        assert md_to_xwiki("1. first") == "1. first"


class TestBlockquote:
    def test_blockquote_stripped(self) -> None:
        result = md_to_xwiki("> some note")
        assert "some note" in result
        assert ">" not in result
