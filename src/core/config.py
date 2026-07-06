"""Config loader — merges core.yaml with a target overlay and validates with Pydantic."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


class Organisation(BaseModel):
    name: str
    short: str
    quality_officer: str
    management: str


class Role(BaseModel):
    id: str
    label: str
    responsibilities: list[str]


class Clause(BaseModel):
    id: str
    title: str
    documents: list[str]


class Document(BaseModel):
    id: str
    title: str
    template: str | None
    clause: str


class RecordType(BaseModel):
    id: str
    label: str
    clause: str
    fields: list[str]


class KPI(BaseModel):
    id: str
    label: str
    unit: str
    target: str
    frequency: str
    clause: str


class CapaState(BaseModel):
    id: str
    label: str
    transitions: list[str]


class Meta(BaseModel):
    version: str
    standard: str


class XWikiConfig(BaseModel):
    base_url: str
    space_key: str
    username: str
    parent_page: str = "QM Manual"


class RedmineConfig(BaseModel):
    base_url: str
    project_key: str
    tracker_mapping: dict[str, str]


class SelfhostedConfig(BaseModel):
    xwiki: XWikiConfig
    redmine: RedmineConfig


class ConfluenceConfig(BaseModel):
    base_url: str  # https://mycompany.atlassian.net/wiki
    space_key: str  # QMS
    email: str  # atlassian account email
    parent_page_title: str = "QM Manual"


class JiraConfig(BaseModel):
    base_url: str  # https://mycompany.atlassian.net
    project_key: str  # QMS
    project_name: str = "Quality Management System"
    email: str  # atlassian account email (same as confluence)
    issue_type_mapping: dict[str, str] = {}


class AtlassianConfig(BaseModel):
    confluence: ConfluenceConfig
    jira: JiraConfig


class CoreConfig(BaseModel):
    meta: Meta
    organisation: Organisation
    roles: list[Role]
    clauses: list[Clause]
    documents: list[Document]
    record_types: list[RecordType]
    kpis: list[KPI]
    capa_states: list[CapaState]
    target: str | None = None
    selfhosted: SelfhostedConfig | None = None
    atlassian: AtlassianConfig | None = None

    @field_validator("documents")
    @classmethod
    def document_ids_unique(cls, docs: list[Document]) -> list[Document]:
        ids = [d.id for d in docs]
        duplicates = {i for i in ids if ids.count(i) > 1}
        if duplicates:
            raise ValueError(f"Duplicate document IDs: {duplicates}")
        return docs


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge overlay into base (overlay wins on conflicts)."""
    merged = base.copy()
    for key, value in overlay.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(core_path: Path, overlay_path: Path) -> CoreConfig:
    """Load and merge core + overlay YAML, return validated CoreConfig."""
    core_data = _load_yaml(core_path)
    overlay_data = _load_yaml(overlay_path)
    merged = _deep_merge(core_data, overlay_data)
    return CoreConfig.model_validate(merged)
