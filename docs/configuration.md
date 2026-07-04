# Configuration Reference

> TODO: Full reference will be written once the core config loader (Pydantic schema) is complete.

## Overview

Configuration is split into two layers:

| File | Purpose |
|------|---------|
| `config/core.yaml` | Tool-neutral QMS substance — clauses, documents, roles, records, KPIs |
| `config/<target>.yaml` | Tool overlay template — copy and fill per client |
| `config/clients/<client>.yaml` | Per-client filled overlay (gitignored, not in this repo) |

## Core Config Keys

See [`config/core.yaml`](../config/core.yaml) — all keys are documented inline.

## Overlay Keys

| Key | Description |
|-----|-------------|
| `target` | `selfhosted` / `atlassian` / `m365` |
| `organisation.name` | Full legal name of the client organisation |
| `organisation.short` | Short identifier used in document IDs |
| `organisation.quality_officer` | Full name of the QMO |
| `organisation.management` | Full name of the approving manager |

### Self-hosted specific

| Key | Description |
|-----|-------------|
| `xwiki.base_url` | XWiki instance URL |
| `xwiki.space_key` | XWiki space key for the QMS (default: `QMS`) |
| `redmine.base_url` | Redmine instance URL |
| `redmine.project_key` | Redmine project identifier |
| `redmine.tracker_mapping` | Maps record type IDs to Redmine tracker names |

## Environment Variables

Secrets are never stored in config files — pass them as environment variables:

| Variable | Used by |
|----------|---------|
| `XWIKI_PASSWORD` | XWiki REST authentication |
| `REDMINE_API_KEY` | Redmine REST authentication |
| `CONFLUENCE_API_TOKEN` | Confluence REST authentication (Phase 2) |
| `JIRA_API_TOKEN` | Jira REST authentication (Phase 2) |
| `SHAREPOINT_CLIENT_SECRET` | SharePoint Graph API (Phase 3) |
