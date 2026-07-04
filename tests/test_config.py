"""Unit tests for the config loader."""

from pathlib import Path

from src.core.config import _deep_merge

CORE_YAML = Path(__file__).parent.parent / "config" / "core.yaml"
SELFHOSTED_YAML = Path(__file__).parent.parent / "config" / "selfhosted.yaml"


class TestDeepMerge:
    def test_overlay_wins_on_conflict(self) -> None:
        base = {"a": 1, "b": {"x": 10, "y": 20}}
        overlay = {"b": {"x": 99}, "c": 3}
        result = _deep_merge(base, overlay)
        assert result == {"a": 1, "b": {"x": 99, "y": 20}, "c": 3}

    def test_base_unchanged(self) -> None:
        base = {"a": 1}
        _deep_merge(base, {"a": 2})
        assert base == {"a": 1}


class TestCoreConfig:
    def test_core_yaml_loads_without_overlay(self) -> None:
        """core.yaml must be parseable on its own (Jinja placeholders are strings)."""
        import yaml

        with CORE_YAML.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        assert "clauses" in data
        assert "documents" in data
        assert len(data["clauses"]) == 7  # clauses 4-10

    def test_all_clause_document_refs_exist(self) -> None:
        import yaml

        with CORE_YAML.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        doc_ids = {d["id"] for d in data["documents"]}
        for clause in data["clauses"]:
            for ref in clause["documents"]:
                assert ref in doc_ids, f"Clause {clause['id']} references unknown doc '{ref}'"

    def test_kpis_have_required_fields(self) -> None:
        import yaml

        with CORE_YAML.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        for kpi in data["kpis"]:
            assert "id" in kpi
            assert "label" in kpi
            assert "target" in kpi

    def test_capa_state_transitions_reference_valid_states(self) -> None:
        import yaml

        with CORE_YAML.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        state_ids = {s["id"] for s in data["capa_states"]}
        for state in data["capa_states"]:
            for transition in state["transitions"]:
                assert transition in state_ids, (
                    f"State '{state['id']}' transitions to unknown state '{transition}'"
                )
