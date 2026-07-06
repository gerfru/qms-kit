"""Unit tests for the Jira Cloud adapter."""

from unittest.mock import MagicMock, patch

import pytest

from adapters.atlassian.jira import JiraAdapter
from src.core.config import AtlassianConfig, ConfluenceConfig, JiraConfig, RecordType


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
            project_name="Quality Management System",
            email="admin@test.com",
        ),
    )
    cfg.organisation.name = "Acme GmbH"
    cfg.record_types = [
        RecordType(id="nc", label="Nonconformity", clause="8.7", fields=["title", "description"]),
        RecordType(id="capa", label="CAPA", clause="10.2", fields=["title", "action"]),
    ]
    return cfg


class TestJiraAdapter:
    def test_raises_if_no_atlassian_config(self) -> None:
        cfg = MagicMock()
        cfg.atlassian = None
        with pytest.raises(ValueError, match="atlassian config block"):
            JiraAdapter(cfg)

    def test_base_url_trailing_slash_stripped(self) -> None:
        adapter = JiraAdapter(_make_config())
        assert not adapter._base_url.endswith("/")

    def test_project_exists_returns_true_on_200(self) -> None:
        adapter = JiraAdapter(_make_config())
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        with patch("adapters.atlassian.jira.requests.get", return_value=mock_resp):
            assert adapter.project_exists() is True

    def test_project_exists_returns_false_on_http_error(self) -> None:
        import requests as req

        adapter = JiraAdapter(_make_config())
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req.HTTPError()
        with patch("adapters.atlassian.jira.requests.get", return_value=mock_resp):
            assert adapter.project_exists() is False

    def test_get_issue_type_id_returns_id_when_found(self) -> None:
        adapter = JiraAdapter(_make_config())
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"name": "Nonconformity", "id": "10001"}]
        mock_resp.raise_for_status.return_value = None
        with patch("adapters.atlassian.jira.requests.get", return_value=mock_resp):
            assert adapter.get_issue_type_id("Nonconformity") == "10001"

    def test_get_issue_type_id_returns_none_when_missing(self) -> None:
        adapter = JiraAdapter(_make_config())
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"name": "Bug", "id": "1"}]
        mock_resp.raise_for_status.return_value = None
        with patch("adapters.atlassian.jira.requests.get", return_value=mock_resp):
            assert adapter.get_issue_type_id("Nonconformity") is None

    def test_create_issue_type_skips_if_exists(self) -> None:
        adapter = JiraAdapter(_make_config())
        with (
            patch.object(adapter, "get_issue_type_id", return_value="99"),
            patch("adapters.atlassian.jira.requests.post") as mock_post,
        ):
            adapter.create_issue_type("Nonconformity", "desc")
            mock_post.assert_not_called()

    def test_create_issue_type_posts_if_missing(self) -> None:
        adapter = JiraAdapter(_make_config())
        mock_post_resp = MagicMock()
        mock_post_resp.json.return_value = {"id": "10002"}
        mock_post_resp.raise_for_status.return_value = None
        with (
            patch.object(adapter, "get_issue_type_id", return_value=None),
            patch("adapters.atlassian.jira.requests.post", return_value=mock_post_resp),
        ):
            result = adapter.create_issue_type("Nonconformity", "desc")
            assert result == "10002"

    def test_deploy_seeds_all_mapped_record_types(self) -> None:
        adapter = JiraAdapter(_make_config())
        mapping = {"nc": "Nonconformity", "capa": "Corrective Action"}
        with (
            patch.object(adapter, "create_project", return_value="1"),
            patch.object(adapter, "seed_record_type") as mock_seed,
        ):
            adapter.deploy(mapping)
            assert mock_seed.call_count == 2

    def test_deploy_skips_unmapped_record_types(self) -> None:
        adapter = JiraAdapter(_make_config())
        with (
            patch.object(adapter, "create_project", return_value="1"),
            patch.object(adapter, "seed_record_type") as mock_seed,
        ):
            adapter.deploy({"nc": "Nonconformity"})  # capa not mapped
            assert mock_seed.call_count == 1
