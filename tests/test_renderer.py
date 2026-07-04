"""Unit tests for the Jinja2 template renderer."""

from pathlib import Path
from unittest.mock import MagicMock

from src.core.renderer import build_context, render_template

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def _make_config(org_name: str = "Acme Ltd") -> MagicMock:
    cfg = MagicMock()
    cfg.organisation.name = org_name
    cfg.organisation.short = "ACME"
    cfg.organisation.quality_officer = "Jane Smith"
    cfg.organisation.management = "John Doe"
    cfg.meta.version = "1.0"
    return cfg


class TestBuildContext:
    def test_contains_org_fields(self) -> None:
        ctx = build_context(_make_config())
        assert ctx["org_name"] == "Acme Ltd"
        assert ctx["quality_officer"] == "Jane Smith"
        assert ctx["management"] == "John Doe"
        assert ctx["version"] == "1.0"

    def test_extra_values_merged(self) -> None:
        ctx = build_context(_make_config(), extra={"date": "2024-01-01"})
        assert ctx["date"] == "2024-01-01"

    def test_extra_overrides_base(self) -> None:
        ctx = build_context(_make_config(), extra={"org_name": "Override Corp"})
        assert ctx["org_name"] == "Override Corp"


class TestRenderTemplate:
    def test_policy_renders_org_name(self) -> None:
        result = render_template(
            "policy.xwiki.j2",
            _make_config(),
            TEMPLATES_DIR,
            extra={"date": "2024-01-01"},
        )
        assert "Acme Ltd" in result
        assert "ISO 9001:2015" in result

    def test_procedure_renders_title(self) -> None:
        result = render_template(
            "procedure.xwiki.j2",
            _make_config(),
            TEMPLATES_DIR,
            extra={
                "procedure_title": "Document Control",
                "doc_id": "QMS-7.5-001",
                "clause": "7.5",
                "owner_role": "QMO",
                "approver": "John Doe",
                "author": "Jane Smith",
                "date": "2024-01-01",
            },
        )
        assert "Document Control" in result
        assert "7.5" in result

    def test_capa_form_renders(self) -> None:
        result = render_template(
            "capa_form.xwiki.j2",
            _make_config(),
            TEMPLATES_DIR,
            extra={
                "capa_id": "CAPA-2024-001",
                "opened_date": "2024-01-01",
                "opened_by": "Jane Smith",
                "source_ref": "NC-2024-003",
            },
        )
        assert "CAPA-2024-001" in result
        assert "10.2" in result
