"""Unit tests for the qms-kit export command."""

from pathlib import Path

from click.testing import CliRunner

from cli.main import _slugify, cli

SELFHOSTED_YAML = Path(__file__).parent.parent / "config" / "selfhosted.yaml"

_MD_ARGS = ["export", "--format", "md", "--config", str(SELFHOSTED_YAML)]
_HTML_ARGS = ["export", "--format", "html", "--config", str(SELFHOSTED_YAML)]


class TestSlugify:
    def test_lowercase(self) -> None:
        assert _slugify("Quality Policy") == "quality-policy"

    def test_special_chars_replaced(self) -> None:
        assert _slugify("ISO 9001:2015") == "iso-9001-2015"

    def test_leading_trailing_stripped(self) -> None:
        assert _slugify("  hello  ") == "hello"

    def test_multiple_separators_collapsed(self) -> None:
        assert _slugify("a  --  b") == "a-b"


class TestExportMd:
    def test_export_md_exits_zero(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [*_MD_ARGS, "--output-dir", str(tmp_path / "out")])
        assert result.exit_code == 0, result.output

    def test_export_md_creates_files(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        runner = CliRunner()
        runner.invoke(cli, [*_MD_ARGS, "--output-dir", str(out)])
        assert len(list(out.glob("*.md"))) > 0

    def test_export_md_files_contain_content(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        runner = CliRunner()
        runner.invoke(cli, [*_MD_ARGS, "--output-dir", str(out)])
        for f in out.glob("*.md"):
            assert f.read_text(encoding="utf-8").strip() != ""

    def test_export_md_prints_count(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [*_MD_ARGS, "--output-dir", str(tmp_path)])
        assert "Export complete" in result.output
        assert "file(s) written" in result.output


class TestExportHtml:
    def test_export_html_exits_zero(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, [*_HTML_ARGS, "--output-dir", str(tmp_path / "out")])
        assert result.exit_code == 0, result.output

    def test_export_html_creates_index(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        runner = CliRunner()
        runner.invoke(cli, [*_HTML_ARGS, "--output-dir", str(out)])
        assert (out / "index.html").exists()

    def test_export_html_index_contains_links(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        runner = CliRunner()
        runner.invoke(cli, [*_HTML_ARGS, "--output-dir", str(out)])
        index = (out / "index.html").read_text(encoding="utf-8")
        assert "<a href=" in index
        assert ".html" in index

    def test_export_html_pages_have_back_link(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        runner = CliRunner()
        runner.invoke(cli, [*_HTML_ARGS, "--output-dir", str(out)])
        for f in out.glob("*.html"):
            if f.name == "index.html":
                continue
            assert "index.html" in f.read_text(encoding="utf-8")

    def test_export_html_valid_structure(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        runner = CliRunner()
        runner.invoke(cli, [*_HTML_ARGS, "--output-dir", str(out)])
        for f in out.glob("*.html"):
            content = f.read_text(encoding="utf-8")
            assert "<!doctype html>" in content
            assert "<style>" in content

    def test_export_html_default_output_dir(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, [*_HTML_ARGS])
        assert result.exit_code == 0, result.output
        assert "qms-export" in result.output
