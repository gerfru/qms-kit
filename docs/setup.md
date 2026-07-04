# Setup Guide

> TODO: Full installation walkthrough will be written once the self-hosted adapter is complete.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.12+
- `uv` package manager (`pip install uv`)

## Quick Start (Self-hosted)

```bash
# 1. Clone the repository
git clone https://github.com/gerfru/qms-kit.git
cd qms-kit

# 2. Install dependencies
uv sync

# 3. Copy and fill in the client overlay
cp config/selfhosted.yaml config/clients/acme.yaml
# edit config/clients/acme.yaml with your org details, XWiki URL, Redmine URL

# 4. Start the self-hosted stack
docker compose -f adapters/selfhosted/docker-compose.yml up -d

# 5. Run the one-time Redmine manual setup (custom field definitions)
# See docs/redmine-setup.md

# 6. Deploy the QMS scaffold
python -m cli deploy --target selfhosted --config config/clients/acme.yaml
```

## Next Steps

See [Configuration Reference](configuration.md) for all available options.
