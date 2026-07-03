<div align="center">

# 🗂️ qms-kit

**ISO 9001 quality management — deployed in one command.**

A reusable deployment kit that scaffolds an audit-ready QMS into your tool of choice on day one.
Fill in your organisation's content over the following two weeks.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)
![YAML](https://img.shields.io/badge/Config-YAML-CB171E?style=flat-square&logo=yaml&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![XWiki](https://img.shields.io/badge/Self--hosted-XWiki%20%2B%20Redmine-10B981?style=flat-square)
![ISO 9001](https://img.shields.io/badge/ISO%209001-Clauses%204–10-0057B8?style=flat-square)

[Quickstart](#-quickstart) · [What gets deployed](#-what-gets-deployed) · [Targets](#-deployment-targets) · [Docs](#-documentation)

</div>

---

> *Setting up a QMS shouldn't take three consultants and two months.*
> *The structure — document tree, record trackers, review workflows, dashboards — is the same
> for every client. Only the content differs.*

**qms-kit deploys the structure. You fill in the content.**

One command wires up spaces, document templates, issue trackers, approval workflows, and KPI
dashboards for ISO 9001 clauses 4–10 — in XWiki + Redmine (self-hosted), Confluence + Jira
(Atlassian), or SharePoint + Power Automate (M365).
Reuse the same kit for every client; swap the overlay config.

> ⚠️ **Scope:** qms-kit delivers a documentation scaffold for internal maturity and
> customer/second-party audits. Accredited certification requires an additional operating phase
> (~3 months, full internal audit cycle + management review) that no tool can shortcut.

---

## ✨ Why qms-kit

- 📋 **ISO 9001 clauses 4–10 as structure** — every space, page, and tracker maps to a clause.
- ⚙️ **Config-driven, idempotent** — declare your QMS in YAML; run deploy as often as needed.
- 🔁 **Multi-tenant** — one core config, one overlay per client. No copy-paste between engagements.
- 🧩 **Adapter model** — self-hosted, Atlassian, and M365 are interchangeable modules; the core never changes.
- 📄 **Jinja2 templates** — policy, procedure, management review agenda, audit checklist, CAPA form — all with placeholders, ready to hand to your client.

---

## 📦 What gets deployed

| Layer | What |
|-------|------|
| **Structure** | Space / site / project, document tree, naming conventions |
| **Document templates** | Quality policy, procedures, MR agenda, internal audit checklist, CAPA/NC form |
| **Record containers** | Issue schemas for NC, CAPA, audits, objectives/KPIs |
| **Workflows** | Approval/review routing, CAPA escalation, review reminders |
| **Dashboards** | KPI and status overview |

---

## 🚀 Quickstart

> Self-hosted target (XWiki + Redmine via Docker Compose):

```bash
# 1. Copy and fill in your client overlay
cp config/selfhosted.yaml config/clients/acme.yaml
# edit acme.yaml: org name, XWiki URL, Redmine URL, credentials

# 2. Start the stack (first time only — brings up XWiki + Redmine)
docker compose -f adapters/selfhosted/docker-compose.yml up -d

# 3. Seed the QMS scaffold
python -m cli deploy --target selfhosted --config config/clients/acme.yaml
```

> **Note on Redmine custom fields:** Field *definitions* (Root Cause, Effectiveness Check, Status)
> must be created once manually or via plugin — the Redmine API does not support creating them.
> The deployer seeds projects, issues, and field *values* automatically.
> See [docs/redmine-setup.md](docs/redmine-setup.md).

→ Full walkthrough: **[docs/setup.md](docs/setup.md)**

---

## 🎯 Deployment targets

| Target | Status | Stack |
|--------|--------|-------|
| **Self-hosted** | ✅ Phase 1 | XWiki (docs) + Redmine (records) via Docker |
| **Atlassian** | 🔜 Phase 2 | Confluence + Jira via REST API |
| **Microsoft 365** | 🔜 Phase 3 | SharePoint + Power Automate via PnP PowerShell |

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

Python · Jinja2 · YAML · Docker Compose · XWiki REST API · Redmine REST API

Three layers above the adapters: a config loader with Pydantic schema validation, a Jinja2
template renderer, and a single CLI entry point (`deploy --target`).
M365 adapter shells out to PnP PowerShell; everything else is pure Python.

---

<div align="center">
<sub>Built for consultants who'd rather configure once and deploy everywhere.</sub>
</div>
