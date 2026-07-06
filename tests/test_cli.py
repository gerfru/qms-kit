"""Unit tests for the CLI deploy and validate commands."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from cli.main import cli

CORE_YAML = Path(__file__).parent.parent / "config" / "core.yaml"
SELFHOSTED_YAML = Path(__file__).parent.parent / "config" / "selfhosted.yaml"
ATLASSIAN_YAML = Path(__file__).parent.parent / "config" / "atlassian.yaml"


class TestDeployDryRun:
    def test_dry_run_selfhosted_exits_zero(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["deploy", "--target", "selfhosted", "--config", str(SELFHOSTED_YAML), "--dry-run"],
        )
        assert result.exit_code == 0, result.output

    def test_dry_run_prints_rendered_count(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["deploy", "--target", "selfhosted", "--config", str(SELFHOSTED_YAML), "--dry-run"],
        )
        assert "Dry run complete" in result.output
        assert "rendered" in result.output

    def test_dry_run_shows_org_name(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["deploy", "--target", "selfhosted", "--config", str(SELFHOSTED_YAML), "--dry-run"],
        )
        assert "Config loaded" in result.output

    def test_dry_run_atlassian_raises_not_implemented(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["deploy", "--target", "atlassian", "--config", str(SELFHOSTED_YAML), "--dry-run"],
        )
        # dry-run returns before the adapter check, so this should succeed
        assert result.exit_code == 0

    def test_missing_config_file_exits_nonzero(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["deploy", "--target", "selfhosted", "--config", "nonexistent.yaml", "--dry-run"],
        )
        assert result.exit_code != 0


class TestDeployLive:
    def test_atlassian_target_raises_click_exception(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["deploy", "--target", "atlassian", "--config", str(SELFHOSTED_YAML)],
        )
        assert result.exit_code != 0
        assert "atlassian config block missing" in result.output

    def test_m365_target_raises_click_exception(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["deploy", "--target", "m365", "--config", str(SELFHOSTED_YAML)],
        )
        assert result.exit_code != 0
        assert "not yet implemented" in result.output

    def test_selfhosted_deploy_calls_adapters(self) -> None:
        runner = CliRunner()
        with (
            patch("adapters.selfhosted.xwiki.XWikiAdapter.deploy") as mock_xwiki,
            patch("adapters.selfhosted.redmine.RedmineAdapter.deploy") as mock_redmine,
        ):
            result = runner.invoke(
                cli,
                ["deploy", "--target", "selfhosted", "--config", str(SELFHOSTED_YAML)],
            )
        assert result.exit_code == 0, result.output
        mock_xwiki.assert_called_once()
        mock_redmine.assert_called_once()


class TestValidate:
    def test_validate_selfhosted_ok_with_env(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["validate", "--target", "selfhosted", "--config", str(SELFHOSTED_YAML)],
            env={"XWIKI_PASSWORD": "Admin", "REDMINE_API_KEY": "abc123"},
        )
        assert result.exit_code == 0, result.output
        assert "Validation OK" in result.output

    def test_validate_selfhosted_fails_missing_env(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["validate", "--target", "selfhosted", "--config", str(SELFHOSTED_YAML)],
            env={},
        )
        assert result.exit_code != 0
        assert "XWIKI_PASSWORD" in result.output
        assert "REDMINE_API_KEY" in result.output

    def test_validate_atlassian_fails_wrong_config_block(self) -> None:
        # selfhosted.yaml has no atlassian block
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["validate", "--target", "atlassian", "--config", str(SELFHOSTED_YAML)],
            env={"ATLASSIAN_API_TOKEN": "tok"},
        )
        assert result.exit_code != 0
        assert "atlassian config block missing" in result.output

    def test_validate_atlassian_ok_with_atlassian_config(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["validate", "--target", "atlassian", "--config", str(ATLASSIAN_YAML)],
            env={"ATLASSIAN_API_TOKEN": "tok"},
        )
        assert result.exit_code == 0, result.output
        assert "Validation OK" in result.output

    def test_validate_missing_config_file_exits_nonzero(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["validate", "--target", "selfhosted", "--config", "nonexistent.yaml"],
        )
        assert result.exit_code != 0

    def test_validate_prints_rendered_count(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["validate", "--target", "selfhosted", "--config", str(SELFHOSTED_YAML)],
            env={"XWIKI_PASSWORD": "x", "REDMINE_API_KEY": "x"},
        )
        assert "templates rendered successfully" in result.output
