"""Unit tests for the self-hosted adapters (XWiki and Redmine).

All HTTP calls are mocked — no live services required.
"""

from unittest.mock import MagicMock, patch

import pytest  # noqa: F401 — used via pytest.CaptureFixture and pytest.raises

from adapters.selfhosted.redmine import RedmineAdapter
from adapters.selfhosted.xwiki import XWikiAdapter
from src.core.config import (
    KPI,
    CapaState,
    Clause,
    CoreConfig,
    Document,
    Meta,
    Organisation,
    RecordType,
    RedmineConfig,
    Role,
    SelfhostedConfig,
    XWikiConfig,
)


def _make_config(
    xwiki_url: str = "http://xwiki.test",
    redmine_url: str = "http://redmine.test",
    project_key: str = "qms-test",
) -> CoreConfig:
    return CoreConfig(
        meta=Meta(version="1.0", standard="ISO 9001:2015"),
        organisation=Organisation(
            name="Test GmbH",
            short="TST",
            quality_officer="Jane Smith",
            management="John Doe",
        ),
        roles=[Role(id="qmo", label="QMO", responsibilities=["quality"])],
        clauses=[Clause(id="4", title="Context", documents=["scope"])],
        documents=[Document(id="scope", title="Scope", template=None, clause="4")],
        record_types=[
            RecordType(id="nc", label="Nonconformity", clause="10.2", fields=["description"])
        ],
        kpis=[KPI(id="k1", label="KPI 1", unit="%", target="95", frequency="monthly", clause="9")],
        capa_states=[CapaState(id="open", label="Open", transitions=["open"])],
        target="selfhosted",
        selfhosted=SelfhostedConfig(
            xwiki=XWikiConfig(
                base_url=xwiki_url,
                space_key="QMS",
                username="Admin",
            ),
            redmine=RedmineConfig(
                base_url=redmine_url,
                project_key=project_key,
                tracker_mapping={"nc": "Nonconformity"},
            ),
        ),
    )


class TestXWikiAdapter:
    def test_raises_if_no_selfhosted_config(self) -> None:
        cfg = _make_config()
        cfg = cfg.model_copy(update={"selfhosted": None})
        with pytest.raises(ValueError, match="selfhosted config block"):
            XWikiAdapter(cfg)

    def test_page_exists_returns_true_on_200(self) -> None:
        adapter = XWikiAdapter(_make_config())
        mock_resp = MagicMock(status_code=200)
        with patch("adapters.selfhosted.xwiki.requests.get", return_value=mock_resp):
            assert adapter.page_exists("TestPage") is True

    def test_page_exists_returns_false_on_404(self) -> None:
        adapter = XWikiAdapter(_make_config())
        mock_resp = MagicMock(status_code=404)
        with patch("adapters.selfhosted.xwiki.requests.get", return_value=mock_resp):
            assert adapter.page_exists("MissingPage") is False

    def test_create_or_update_page_calls_put(self) -> None:
        adapter = XWikiAdapter(_make_config())
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        with patch("adapters.selfhosted.xwiki.requests.put", return_value=mock_resp) as mock_put:
            adapter.create_or_update_page("MyPage", "My Title", "# Content")
        mock_put.assert_called_once()
        call_kwargs = mock_put.call_args
        assert "MyPage" in call_kwargs.args[0]

    def test_deploy_upserts_all_pages(self) -> None:
        adapter = XWikiAdapter(_make_config())
        pages = {
            "page-a": ("Title A", "# A"),
            "page-b": ("Title B", "# B"),
        }
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        with patch("adapters.selfhosted.xwiki.requests.put", return_value=mock_resp) as mock_put:
            adapter.deploy(pages)
        # 2 document pages flat in the space (no intermediate parent page)
        assert mock_put.call_count == 2

    def test_base_url_trailing_slash_stripped(self) -> None:
        adapter = XWikiAdapter(_make_config(xwiki_url="http://xwiki.test/"))
        assert not adapter._page_url("X").startswith("http://xwiki.test//")


class TestRedmineAdapter:
    def test_raises_if_no_selfhosted_config(self) -> None:
        cfg = _make_config()
        cfg = cfg.model_copy(update={"selfhosted": None})
        with pytest.raises(ValueError, match="selfhosted config block"):
            RedmineAdapter(cfg)

    def test_project_exists_returns_true_on_200(self) -> None:
        adapter = RedmineAdapter(_make_config())
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        with patch("adapters.selfhosted.redmine.requests.get", return_value=mock_resp):
            assert adapter.project_exists() is True

    def test_project_exists_returns_false_on_http_error(self) -> None:
        import requests

        adapter = RedmineAdapter(_make_config())
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("404")
        with patch("adapters.selfhosted.redmine.requests.get", return_value=mock_resp):
            assert adapter.project_exists() is False

    def test_create_project_skips_if_exists(self, capsys: pytest.CaptureFixture) -> None:
        adapter = RedmineAdapter(_make_config())
        with (
            patch.object(adapter, "project_exists", return_value=True),
            patch.object(adapter, "_post") as mock_post,
        ):
            adapter.create_project()
        mock_post.assert_not_called()

    def test_create_project_posts_if_missing(self) -> None:
        adapter = RedmineAdapter(_make_config())
        with (
            patch.object(adapter, "project_exists", return_value=False),
            patch.object(adapter, "_post", return_value={}) as mock_post,
        ):
            adapter.create_project()
        mock_post.assert_called_once()

    def test_get_tracker_id_returns_id_by_name(self) -> None:
        adapter = RedmineAdapter(_make_config())
        trackers = {"trackers": [{"id": 5, "name": "Nonconformity"}, {"id": 6, "name": "CAPA"}]}
        with patch.object(adapter, "_get", return_value=trackers):
            assert adapter.get_tracker_id("Nonconformity") == 5
            assert adapter.get_tracker_id("CAPA") == 6
            assert adapter.get_tracker_id("Unknown") is None

    def test_deploy_seeds_all_mapped_record_types(self) -> None:
        adapter = RedmineAdapter(_make_config())
        with (
            patch.object(adapter, "create_project"),
            patch.object(adapter, "seed_record_type") as mock_seed,
        ):
            adapter.deploy({"nc": "Nonconformity"})
        mock_seed.assert_called_once()

    def test_deploy_skips_unmapped_record_types(self) -> None:
        adapter = RedmineAdapter(_make_config())
        with (
            patch.object(adapter, "create_project"),
            patch.object(adapter, "seed_record_type") as mock_seed,
        ):
            adapter.deploy({})  # empty mapping — nothing should be seeded
        mock_seed.assert_not_called()
