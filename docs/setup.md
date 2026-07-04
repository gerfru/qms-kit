# Setup Guide

Complete walkthrough from zero to first QMS deployment on the self-hosted stack (XWiki + Redmine).

## Prerequisites

- **Docker + Docker Compose** ≥ 24 / v2 — [docs.docker.com](https://docs.docker.com/get-docker/)
- **Python** ≥ 3.12 — [python.org](https://www.python.org/downloads/)
- **uv** (latest) — `pip install uv`

## Step 1 — Clone and install

```bash
git clone https://github.com/gerfru/qms-kit.git
cd qms-kit
uv sync
```

## Step 2 — Start the self-hosted stack

```bash
# Copy the env template and fill in passwords
cp docker/.env.example docker/.env
# edit docker/.env — set real passwords and generate REDMINE_SECRET_KEY_BASE:
#   openssl rand -hex 64

docker compose -f docker/docker-compose.yml up -d
```

First startup takes 2–5 minutes while XWiki and Redmine initialize their databases.

**Verify both services are up:**

| Service | URL                                    | Default credentials |
|---------|----------------------------------------|---------------------|
| XWiki   | <http://localhost:8080>                | Admin / Admin       |
| Redmine | <http://localhost:3000>                | admin / admin       |

> Change default passwords immediately after first login.

## Step 3 — One-time Redmine setup (manual)

Custom field *definitions* cannot be created via the Redmine API — they must be set up once through the web UI.

Follow [docs/redmine-setup.md](redmine-setup.md) to create the required trackers and custom fields.

After setup: go to **My account → API access key** in Redmine and copy the key into `docker/.env` as `REDMINE_API_KEY`.

## Step 4 — Create a client overlay

```bash
cp config/clients/example.yaml config/clients/acme.yaml
```

Edit `config/clients/acme.yaml`:

```yaml
organisation:
  name: "Acme GmbH"
  short: "ACM"
  quality_officer: "Jane Smith"
  management: "John Doe"

selfhosted:
  xwiki:
    base_url: "http://localhost:8080"
    space_key: "QMS"
    username: "Admin"
  redmine:
    base_url: "http://localhost:3000"
    project_key: "qms-acme"
    tracker_mapping:
      nc: "Nonconformity"
      capa: "CAPA"
      audit: "Internal Audit"
      kpi: "KPI Measurement"
```

## Step 5 — Dry-run (recommended first)

```bash
export XWIKI_PASSWORD=Admin
export REDMINE_API_KEY=<your-key>

qms-kit deploy --target selfhosted --config config/clients/acme.yaml --dry-run
```

This renders all templates and validates the config without touching XWiki or Redmine.
Expected output: `Dry run complete — N template(s) rendered, nothing deployed.`

## Step 6 — Deploy

```bash
qms-kit deploy --target selfhosted --config config/clients/acme.yaml
```

The command will:

1. Create the QMS space in XWiki and upsert all document pages
2. Create the QMS project in Redmine and seed scaffold issues per tracker

## Stopping and cleaning up

```bash
# Stop containers (data volumes preserved)
docker compose -f docker/docker-compose.yml down

# Full reset including all data volumes
docker compose -f docker/docker-compose.yml down -v
```

## Next steps

- [Configuration Reference](configuration.md) — all YAML keys explained
- [Redmine Setup](redmine-setup.md) — manual tracker and custom field setup
- [Architecture](architecture.md) — how the layers fit together
