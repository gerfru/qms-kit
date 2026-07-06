<div align="center">

# 🗂️ qms-kit

**ISO 9001 quality management — deployed in one command.**

A reusable deployment kit that scaffolds an audit-ready QMS into your tool of choice on day one.
Fill in your organisation's content over the following two weeks.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)
![YAML](https://img.shields.io/badge/Config-YAML-CB171E?style=flat-square&logo=yaml&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![XWiki](https://img.shields.io/badge/Self--hosted-XWiki%20%2B%20Redmine-10B981?style=flat-square)
![Atlassian](https://img.shields.io/badge/Atlassian-Confluence%20%2B%20Jira-0052CC?style=flat-square&logo=atlassian&logoColor=white)
![ISO 9001](https://img.shields.io/badge/ISO%209001-Clauses%204–10-0057B8?style=flat-square)

[Quickstart](#-quickstart) · [What gets deployed](#-what-gets-deployed) · [Targets](#-deployment-targets) · [Docs](#-documentation)

</div>

---

> *Setting up a QMS shouldn't take three consultants and two months.*
> *The structure — document tree, record trackers, review workflows, dashboards — is the same
> for every client. Only the content differs.*

**qms-kit deploys the structure. You fill in the content.**

One command wires up spaces, document templates, issue trackers, and KPI dashboards for
ISO 9001 clauses 4–10 — in XWiki + Redmine (self-hosted), Confluence + Jira (Atlassian),
or SharePoint + Power Automate (M365). Reuse the same kit for every client; swap the overlay config.

> ⚠️ **Scope:** qms-kit delivers a documentation scaffold for internal maturity and
> customer/second-party audits. Accredited certification requires an additional operating phase
> (~3 months, full internal audit cycle + management review) that no tool can shortcut.

---

## ✨ Why qms-kit

- 📋 **ISO 9001 clauses 4–10 as structure** — every space, page, and tracker maps to a clause.
- ⚙️ **Config-driven, idempotent** — declare your QMS in YAML; run deploy as often as needed.
- 🔁 **Multi-tenant** — one core config, one overlay per client. No copy-paste between engagements.
- 🧩 **Adapter model** — self-hosted, Atlassian, and M365 are interchangeable modules.
- 📄 **Jinja2 templates** — quality policy, procedures, management review agenda, internal audit checklist, CAPA form — all with placeholders, ready to hand to your client.

---

## 📦 What gets deployed

| Layer | What |
|-------|------|
| **Structure** | Space / project, document tree, naming conventions |
| **Document templates** | Quality policy, procedures, MR agenda, internal audit checklist, CAPA/NC form |
| **Record containers** | Issue trackers for NC, CAPA, audits, KPIs |

---

## 🚀 Quickstart

### Self-hosted (XWiki + Redmine via Docker Compose)

```bash
# 1. Clone and install
git clone https://github.com/gerfru/qms-kit.git
cd qms-kit
uv sync

# 2. Start XWiki + Redmine
cp docker/.env.example docker/.env          # fill in passwords
docker compose -f docker/docker-compose.yml up -d

# 3. One-time Redmine setup (manual — API limitation)
# See docs/redmine-setup.md

# 4. Create your client overlay
cp config/selfhosted.yaml config/clients/acme.yaml
# edit acme.yaml: org name, URLs, credentials

# 5. Validate (checks config + env vars, no writes)
export XWIKI_PASSWORD=Admin
export REDMINE_API_KEY=<your-key>
qms-kit validate --target selfhosted --config config/clients/acme.yaml

# 6. Deploy
qms-kit deploy --target selfhosted --config config/clients/acme.yaml
```

> **Redmine custom fields** (Root Cause, Effectiveness Check, etc.) must be created once
> manually — the Redmine API does not support creating field definitions.
> See [docs/redmine-setup.md](docs/redmine-setup.md).

→ Full walkthrough: **[docs/setup.md](docs/setup.md)**

### Atlassian Cloud (Confluence + Jira)

Requirements: an Atlassian Cloud account with admin access to a Confluence space and a Jira project.

```bash
# 1. Clone and install (same as above)
git clone https://github.com/gerfru/qms-kit.git
cd qms-kit
uv sync

# 2. Create your client overlay from the Atlassian template
cp config/atlassian.yaml config/clients/acme.yaml
# edit acme.yaml: org name, base_url (https://<org>.atlassian.net), email,
#                 space_key, project_key

# 3. Generate an API token at id.atlassian.com → Security → API tokens
export ATLASSIAN_API_TOKEN=<your-api-token>

# 4. Validate (checks config + token presence, no writes)
qms-kit validate --target atlassian --config config/clients/acme.yaml

# 5. Deploy
qms-kit deploy --target atlassian --config config/clients/acme.yaml
```

> **One token, two services:** `ATLASSIAN_API_TOKEN` is used for both
> Confluence and Jira. The email in your overlay config must match the
> token owner's Atlassian account.

### Export (M365 / local archive)

No API credentials needed — generates files you can upload to any document library.

```bash
# Export as standalone HTML (recommended for SharePoint document libraries)
qms-kit export --format html --config config/clients/acme.yaml --output-dir ./qms-export

# Export as plain Markdown (version control, email, local archive)
qms-kit export --format md --config config/clients/acme.yaml --output-dir ./qms-export
```

The `--output-dir` defaults to `./qms-export/`. HTML output includes an `index.html`
with links to all documents and a "← Back" navigation link on every page.

---

## 🎯 Deployment targets

| Target | Status | Stack |
|--------|--------|-------|
| **Self-hosted** | ✅ Phase 1 complete | XWiki (docs) + Redmine (records) via Docker |
| **Atlassian** | ✅ Phase 2 complete | Confluence + Jira via REST API |
| **Export (M365 / archive)** | ✅ Phase 3 complete | Markdown + standalone HTML via `qms-kit export` |

> **Atlassian note:** Approval workflows and versioning are not native to Confluence Cloud
> — a Marketplace app (e.g. Comala) is required; that part is only partially automatable.

---

## 📚 Documentation

| | |
|---|---|
| 📋 **[Project Brief](docs/project-brief.md)** | Full requirements, constraints, and design decisions |
| 🚀 **[Setup Guide](docs/setup.md)** | Installation and first deployment |
| ⚙️ **[Configuration Reference](docs/configuration.md)** | All YAML keys explained |
| 🏛️ **[Architecture](docs/architecture.md)** | Four-layer design: config → templates → adapters → CLI |
| 🔌 **[Redmine Setup](docs/redmine-setup.md)** | Manual custom field setup (API limitation) |
| 📝 **[Template Reference](docs/templates.md)** | Jinja2 placeholders and rendering |

---

## 🧱 Stack

Python · Jinja2 · Pydantic · YAML · Click · Docker Compose · XWiki REST API · Redmine REST API · Confluence REST API v2 · Jira REST API v3

Three layers above the adapters: a config loader with Pydantic schema validation, a Jinja2
template renderer, and a single CLI entry point (`qms-kit deploy --target`).

---

<div align="center">
<sub>Built for consultants who'd rather configure once and deploy everywhere.</sub>
</div>
