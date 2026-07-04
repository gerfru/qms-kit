# Configuration Reference

Configuration is split into two layers that are deep-merged at runtime (overlay wins on conflict).

## Files

| File | Purpose |
|------|---------|
| `config/core.yaml` | Tool-neutral QMS substance — clauses, documents, roles, records, KPIs, CAPA states |
| `config/selfhosted.yaml` | Self-hosted overlay template (copy per client) |
| `config/clients/<client>.yaml` | Per-client filled overlay (gitignored — never committed) |
| `config/clients/example.yaml` | Reference template showing all available keys |

## Core config keys (`config/core.yaml`)

These keys define the QMS substance and are shared across all targets.

### `meta`

| Key | Type | Description |
|-----|------|-------------|
| `meta.version` | string | Config schema version |
| `meta.standard` | string | QMS standard (e.g. `ISO 9001:2015`) |

### `organisation`

| Key | Type | Description |
|-----|------|-------------|
| `organisation.name` | string | Full legal name of the client organisation |
| `organisation.short` | string | Short identifier used in document IDs |
| `organisation.quality_officer` | string | Full name of the QMO |
| `organisation.management` | string | Full name of the approving manager |

### `clauses`

List of ISO 9001 clause objects (4–10). Each clause has:

| Key | Type | Description |
|-----|------|-------------|
| `id` | string | Clause number (e.g. `"4"`, `"7.5"`) |
| `title` | string | Clause title |
| `documents` | list[string] | Document IDs that belong to this clause |

### `documents`

List of document definitions. Each document has:

| Key | Type | Description |
|-----|------|-------------|
| `id` | string | Unique document ID (e.g. `quality-policy`) |
| `title` | string | Human-readable title |
| `template` | string or null | Template filename without `.md.j2` extension; null = no template |
| `clause` | string | Parent clause ID |

### `record_types`

List of record type definitions (NC, CAPA, Internal Audit, KPI). Each has:

| Key | Type | Description |
|-----|------|-------------|
| `id` | string | Record type ID (e.g. `nc`, `capa`) |
| `label` | string | Human-readable label |
| `clause` | string | ISO clause this record type belongs to |
| `fields` | list[string] | Custom fields required on this record |

### `kpis`

List of KPI definitions. Each has:

| Key | Type | Description |
|-----|------|-------------|
| `id` | string | KPI identifier |
| `label` | string | Human-readable name |
| `unit` | string | Measurement unit (e.g. `%`, `days`) |
| `target` | string | Target value |
| `frequency` | string | Measurement frequency |
| `clause` | string | ISO clause |

### `capa_states`

CAPA state machine definition. Each state has:

| Key | Type | Description |
|-----|------|-------------|
| `id` | string | State identifier |
| `label` | string | Display name |
| `transitions` | list[string] | Valid next state IDs |

---

## Overlay keys

### Common

| Key | Type | Description |
|-----|------|-------------|
| `target` | string | `selfhosted` / `atlassian` / `m365` |
| `organisation.*` | — | Overrides any `organisation` key from core |

### Self-hosted (`selfhosted:`)

#### XWiki (`selfhosted.xwiki`)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `base_url` | string | — | XWiki instance URL (e.g. `https://wiki.acme.example`) |
| `space_key` | string | `QMS` | XWiki space key for the QMS |
| `username` | string | — | XWiki admin username |
| `parent_page` | string | `QM Manual` | Parent page for all QMS pages |

Password via env var: `XWIKI_PASSWORD`

#### Redmine (`selfhosted.redmine`)

| Key | Type | Description |
|-----|------|-------------|
| `base_url` | string | Redmine instance URL (e.g. `https://redmine.acme.example`) |
| `project_key` | string | Redmine project identifier (e.g. `qms-acme`) |
| `tracker_mapping` | map | Maps record type IDs to Redmine tracker names |

API key via env var: `REDMINE_API_KEY`

**Tracker mapping example:**

```yaml
tracker_mapping:
  nc: "Nonconformity"       # must match the tracker name in Redmine exactly
  capa: "CAPA"
  audit: "Internal Audit"
  kpi: "KPI Measurement"
```

> **API limitation (verified):** Redmine tracker and custom field *definitions* cannot be created
> via the API. Run the one-time manual setup first — see [redmine-setup.md](redmine-setup.md).

---

## Environment variables

Secrets are never stored in config files. Pass them as environment variables before running `qms-kit deploy`.

| Variable | Required for | Description |
|----------|-------------|-------------|
| `XWIKI_PASSWORD` | Self-hosted | XWiki admin password |
| `REDMINE_API_KEY` | Self-hosted | Redmine API key (from My Account → API access key) |
| `CONFLUENCE_API_TOKEN` | Atlassian (Phase 2) | Confluence Cloud API token |
| `JIRA_API_TOKEN` | Atlassian (Phase 2) | Jira Cloud API token |
| `SHAREPOINT_CLIENT_SECRET` | M365 (Phase 3) | SharePoint Graph API client secret |

---

## Validation

The config is validated with Pydantic at load time. Common errors:

- **Duplicate document IDs** → `ValueError: Duplicate document IDs: {...}`
- **Missing required field** → `ValidationError: Field required`
- **Missing selfhosted block** → `ValueError: selfhosted config block is required`
- **Unknown template variable** → `jinja2.UndefinedError: ... is undefined`
