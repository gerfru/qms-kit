# Project Brief: Reusable ISO 9001 QMS Deployment Generator

> **Notation legend**
>
> * **(confirmed)** = explicitly specified by the client.
> * **[conclusion]** = proposal / inference, not finally confirmed.
> * **[not verified]** = could not be verified in this context.
> * **(evidenced)** = supported by prior research with sources (Microsoft Learn, Atlassian docs, certification bodies such as NQA).

---

## 1. Goal / Use Case (confirmed)

* A **reusable framework** that automatically deploys an ISO 9001 QMS **scaffold** into target tools on day one.
* Afterwards, organisation-specific content (processes, context, risk register, objectives) is filled in over approximately two weeks.
* Result: a fully documented, **audit-ready** QMS in the sense of **internal maturity or customer/second-party audit** (confirmed).
* Context: consulting small law firms / companies; the framework shall be **reusable per client**.

## 2. Scope

* **General ISO 9001** (sector-neutral), **no** medical devices (no ISO 13485 / IEC 62304). (confirmed)
* Target state is documentation / internal maturity, **not** accredited certification. (confirmed)
* **(evidenced)** Limit: accredited certification additionally requires an operating phase (typically ~3 months including a full internal audit cycle and a management review). This time cannot be configured away and is outside the scope of what the deployment delivers.

## 3. Functional Scope — "full scope" (confirmed)

Per target tool to be deployed:

* **Structure**: space / site / project, document tree, naming conventions.
* **Document templates** with placeholders: quality policy, procedures, management review agenda, internal audit checklist, CAPA / NC form.
* **Record containers**: list / issue schemas for NC, CAPA, audits, objectives / KPIs.
* **Workflows**: approval / review, CAPA routing, review reminders.
* **Dashboards**: KPI / status overview.
* Coverage of ISO 9001 clauses 4–10 as the structuring logic.

## 4. Target Platforms + Priority (confirmed)

Priority: **1. self-hosted → 2. Atlassian (Confluence + Jira) → 3. Microsoft 365 (SharePoint)**.

Platform constraints **(evidenced)** to consider when building adapters:

* **Atlassian**: provisioning via Confluence / Jira REST API or Forge. Approval workflow + versioning are **not native** in Confluence Cloud → Marketplace app required (e.g. Comala); this part is **only partially automatable**. No official first-party Terraform provider for Atlassian Cloud.
* **M365**: template-based provisioning (PnP) is **PowerShell / .NET-native**; Site Scripts (JSON) and Power Automate for approval / reminders. Python can use the REST / Graph API but has **no maintained PnP provisioning template engine**.
* **Self-hosted**: end-to-end scriptable (Docker / Compose + seed via REST / DB); operation / maintenance is the operator's responsibility.

## 5. Architecture — [conclusion]

Four layers, config-driven, idempotent:

```text
qms-kit/
├─ config/
│  ├─ core.yaml            # tool-neutral: clauses 4–10, doc list, record types, roles, KPIs, CAPA states
│  ├─ selfhosted.yaml      # overlay: DB/host, module mapping for the OSS tool
│  ├─ atlassian.yaml       # overlay: space keys, Jira project/issue types, app config
│  └─ m365.yaml            # overlay: site URLs, list mapping, flow IDs
├─ templates/              # text blocks with placeholders (Jinja2)
│  ├─ policy.md.j2
│  ├─ procedure.md.j2
│  ├─ mgmt_review_agenda.md.j2
│  ├─ internal_audit_checklist.md.j2
│  └─ capa_form.md.j2
├─ core/                   # config loader, schema validation, template renderer
├─ adapters/
│  ├─ selfhosted/          # XWiki (docs) + Redmine (records): Docker Compose + seed via REST
│  ├─ atlassian/           # REST scripts (spaces / pages / Jira issues / dashboards)
│  └─ m365/                # PnP PowerShell scripts + site scripts (JSON) + Power Automate export
├─ cli/                    # entry point: deploy --target selfhosted|atlassian|m365
├─ docs/
└─ tests/
```

Layer description [conclusion]:

1. **Config layer** — declarative QMS substance + tool overlays. The file touched when extending.
2. **Template layer** — text blocks with variables; rendered at deployment time and written to the target platform.
3. **Adapter layer** — one translator per tool from config + templates into real objects (see constraints in section 4).
4. **CLI layer** — single entry point, idempotent (M365 Site Scripts are natively non-destructive per Microsoft; idempotency for self-hosted / Atlassian must be implemented).

## 6. Technical Decisions

* **Config format: YAML** (confirmed).
* **Language: Python as core / orchestrator + PnP PowerShell in the M365 adapter via shell-out** (confirmed).
* **Config structure: tool-neutral core config + tool overlays** (confirmed).

## 7. Reusability (confirmed)

* Multi-tenant: same QMS substance, one overlay / instance per client.
* Versioned (Semver + changelog), adapters as interchangeable modules.
* Extensible: add new documents / processes without changing adapters.

## 8. Non-Goals / Limits

* Does not produce accredited certification readiness (operating / evidence phase, see section 2).
* On Atlassian: approval / versioning only partially automated (app-dependent).
* The generator delivers an audit-*ready scaffold*; the substantive process work remains manual.

## 9. Decisions Made

### 9.1 Self-hosted target (confirmed): XWiki + Redmine as the "solution" (analogous to Confluence + Jira)

* **XWiki** = document layer (QM manual, policy, procedures, templates). Verified: LGPL-2.1 (OSI-approved), automatic **versioning** and **REST API**; **official Docker image** (`xwiki`) + Docker Compose setups (MySQL / MariaDB / PostgreSQL on Tomcat). **[Not verified]:** exact form of the approval / publication workflow (extension vs. out-of-the-box).
* **Redmine** = record / tracking layer (trackable items: CAPA, NC, audits, objectives / KPIs). Verified: **GNU GPL v2** (open source, free licence), REST API can set **custom field values** via POST / PUT; **Docker official image** `redmine` + Docker Compose example on the official Docker Hub page. Note: the Docker image is maintained by docker-library (not Redmine upstream).
* **Verified API limit (Redmine):** custom field **definitions** are **read-only** via API (GET only); **creating** new fields via API is not possible. [Conclusion] The generator seeds projects / issues / field **values**; field **definitions** (e.g. Root Cause, Effectiveness Check, Status) must be set up **once manually or via plugin**.
* **Deployment (confirmed / verified):** both as separate Docker containers connected via reverse proxy; both REST APIs can be seeded from the Python generator. [Conclusion] XWiki's REST API is advantageous for seeding.

### 9.2 Config structure (confirmed): tool-neutral core config + tool overlays

### 9.3 Language (confirmed): Python core + PnP PowerShell in the M365 adapter

### 9.4 Process diagrams (confirmed): draw.io embedded as PNG in XWiki

draw.io is Docker-self-hostable, supports BPMN, and exports PNG / SVG. [Conclusion] PNG is a static image; the editable source stays in draw.io.

**Scope note:** The self-hosted target is therefore a **two-tool stack** (XWiki + Redmine). The adapter `adapters/selfhosted/` is split into an XWiki module and a Redmine module.

## 10. Delivery Order (confirmed)

Following the priority: **self-hosted adapter first**, then Atlassian, then M365. Core config + templates first as they are tool-neutral.
