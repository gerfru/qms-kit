# Architecture

## Four-Layer Design

```text
┌─────────────────────────────────────────┐
│  CLI  (cli/main.py)                     │  deploy --target selfhosted|atlassian|m365
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  Adapter  (adapters/<target>/)          │  translates config + rendered templates
│  selfhosted: XWiki + Redmine modules    │  into real objects in the target platform
│  atlassian:  Confluence + Jira [Ph. 2]  │
│  m365:       SharePoint + PA  [Ph. 3]   │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  Core  (core/)                          │
│  config.py   — YAML loader + Pydantic   │
│  renderer.py — Jinja2 template engine   │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  Config + Templates                     │
│  config/core.yaml      — QMS substance  │
│  config/<target>.yaml  — tool overlay   │
│  templates/*.md.j2     — doc templates  │
└─────────────────────────────────────────┘
```

## Layer Responsibilities

### Config layer

Declarative QMS substance in YAML. Contains clauses 4–10, document definitions, roles,
record types, KPIs, and CAPA states. Tool-specific details live in overlay files.
This is the only file a consultant touches when adapting the kit for a new client.

### Template layer

Jinja2 (`.md.j2`) text blocks with `{{ variable }}` placeholders. Rendered at deploy
time using values from the merged config (core + overlay). Output is written to the
target platform as pages or documents.

### Adapter layer

One module per platform. Reads the rendered output and creates real objects:

| Adapter | What it creates |
|---------|----------------|
| `selfhosted/xwiki.py` | XWiki spaces, pages, parent hierarchy |
| `selfhosted/redmine.py` | Redmine projects, trackers, issues |
| `atlassian/` | Confluence spaces/pages, Jira projects/issue types [Phase 2] |
| `m365/` | SharePoint sites/libraries, Power Automate flows [Phase 3] |

**Idempotency:** each adapter checks whether an object already exists before creating it.
Running `deploy` twice produces the same result without duplicates.

### CLI layer

Single entry point (`qms-kit deploy --target <t> --config <f>`).
Orchestrates: load config → merge overlay → render templates → call adapter.

## Self-hosted Stack

```text
                ┌──────────────┐
  Browser ───▶  │ Reverse Proxy│  (e.g. Caddy / nginx)
                └──────┬───────┘
           ┌───────────┴───────────┐
           ▼                       ▼
     ┌──────────┐           ┌──────────┐
     │  XWiki   │           │  Redmine │
     │  :8080   │           │  :3000   │
     └──────────┘           └──────────┘
     Documents, policies,   NCs, CAPAs,
     procedures, templates  audits, KPIs
```

XWiki and Redmine run as separate Docker containers seeded by the Python generator.
Custom field **definitions** in Redmine must be created once manually
(API limitation — see [Redmine Setup](redmine-setup.md)).
