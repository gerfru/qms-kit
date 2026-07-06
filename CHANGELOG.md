# Changelog

All notable changes to qms-kit are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

## [0.3.0] — 2025-07-06

### Added
- `qms-kit validate` CLI command — validates config and env vars for a target,
  renders all templates, exits 0/1 (useful in CI pipelines)
- Atlassian Quickstart section in README
- CHANGELOG (this file)

## [0.2.0] — 2025-06-29

### Added
- **Phase 2: Atlassian Cloud adapter** (`--target atlassian`)
  - `ConfluenceAdapter`: deploys QMS document tree via Confluence REST API v2,
    Markdown → Storage Format (XHTML) converter (`md_to_confluence_storage`)
  - `JiraAdapter`: creates Jira project (`projectTypeKey=business`), seeds QMS
    issue types via Jira REST API v3 — idempotent (skips existing resources)
  - Single `ATLASSIAN_API_TOKEN` covers both services
- `AtlassianConfig`, `ConfluenceConfig`, `JiraConfig` Pydantic models
- `config/atlassian.yaml` overlay template
- 30 unit tests for Confluence converter and Jira adapter

### Changed
- `--target atlassian` now fully wired in CLI (was "not yet implemented")
- `_deploy_atlassian()` in `cli/main.py` calls both adapters in sequence
- Added record-template placeholder vars to CLI render context
  (`audit_date`, `capa_id`, `opened_by`, etc.)

## [0.1.1] — 2025-06-22

### Fixed
- Removed `[dependency-groups]` section from `pyproject.toml`; dev deps
  consolidated into `[project.optional-dependencies] dev` so
  `uv sync --frozen --extra dev` installs them correctly in CI
- XWiki deploy now deploys pages flat in QMS space — eliminates duplicate
  "QMS → QMS" nav entry caused by intermediate parent page

### Changed
- GitHub Actions PR size check now excludes `*.lock`, `*.md`, `tests/`, `test_*.py`

## [0.1.0] — 2025-06-15

### Added
- **Phase 1: Self-hosted adapter** (`--target selfhosted`)
  - `XWikiAdapter`: deploys QMS space + document pages via XWiki REST API,
    Markdown → XWiki 2.1 syntax converter (`md_to_xwiki`)
  - `RedmineAdapter`: creates project, seeds scaffold issues via Redmine REST API
- **16 Jinja2 document templates** (Markdown as single source of truth):
  quality policy, procedures (context, leadership, planning, support, operation,
  performance, improvement), management review agenda, internal audit checklist,
  CAPA form, NC form, KPI dashboard, competence matrix, risk register,
  supplier evaluation
- Four-layer architecture: Config → Templates → Adapters → CLI
- `CoreConfig` / Pydantic v2 schema with `_deep_merge()` overlay loader
- `qms-kit deploy` Click CLI with `--target`, `--config`, `--dry-run`
- Docker Compose stack for XWiki + Redmine (self-hosted target)
- GitHub Actions CI: ruff, bandit, mypy, pytest, PR size check (400-line limit)
- `uv` package manager, installable as CLI via `pyproject.toml`

[Unreleased]: https://github.com/gerfru/qms-kit/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/gerfru/qms-kit/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/gerfru/qms-kit/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/gerfru/qms-kit/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/gerfru/qms-kit/releases/tag/v0.1.0
