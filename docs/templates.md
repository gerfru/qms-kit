# Template Reference

## Overview

All templates are [Jinja2](https://jinja.palletsprojects.com/) files located in `templates/`.
They use `{{ variable }}` syntax for placeholders and are rendered by `core/renderer.py`
at deployment time.

## Available Templates

| File | Document | ISO Clause |
|------|----------|------------|
| `policy.md.j2` | Quality Policy | 5.2 |
| `procedure.md.j2` | Generic Procedure | 7.5 / 8.x / 9.x / 10.x |
| `mgmt_review_agenda.md.j2` | Management Review Agenda + Minutes | 9.3 |
| `internal_audit_checklist.md.j2` | Internal Audit Checklist | 9.2 |
| `capa_form.md.j2` | CAPA Form | 10.2 |

## Common Variables

All templates receive the following variables from the merged config:

| Variable | Source | Description |
|----------|--------|-------------|
| `org_name` | `organisation.name` | Full legal name of the organisation |
| `org_short` | `organisation.short` | Short identifier |
| `quality_officer` | `organisation.quality_officer` | QMO full name |
| `management` | `organisation.management` | Approving manager full name |
| `date` | injected at render time | ISO 8601 date string |
| `version` | `meta.version` | Document version |

## Template-specific Variables

### `procedure.md.j2`

| Variable | Description |
|----------|-------------|
| `procedure_title` | Title of this specific procedure |
| `doc_id` | Unique document identifier (e.g. `QMS-P-7.5-001`) |
| `owner_role` | Role responsible for this procedure |
| `approver` | Name or role of the approving person |
| `clause` | ISO 9001 clause number |
| `author` | Author of the initial version |

### `internal_audit_checklist.md.j2`

| Variable | Description |
|----------|-------------|
| `audit_date` | Date of the audit |
| `auditor` | Name of the auditor |
| `audit_scope` | Area / process being audited |
| `contact` | Auditee contact person |

### `capa_form.md.j2`

| Variable | Description |
|----------|-------------|
| `capa_id` | Unique CAPA identifier (e.g. `CAPA-2024-001`) |
| `opened_date` | Date the CAPA was opened |
| `opened_by` | Person who opened the CAPA |
| `source_ref` | Reference to triggering NC, audit finding, etc. |

## Adding a New Template

1. Create `templates/<name>.md.j2` with `{{ variable }}` placeholders.
2. Register it in `config/core.yaml` under the relevant document's `template:` key.
3. Add any new variables to `core/renderer.py` context building.
4. No adapter changes needed — adapters receive the rendered string.
