# Security Policy

## Scope

qms-kit is a CLI tool that deploys ISO 9001 QMS scaffolds into self-hosted
(XWiki + Redmine) and cloud (Confluence + Jira) platforms.

**Credentials never leave your machine** — all secrets (API tokens, passwords)
are passed via environment variables and are never written to disk or logged.
Client overlay configs in `config/clients/` are gitignored by design.

## Security Scanning in the SDLC

| Layer | Tool | Trigger |
|-------|------|---------|
| SAST (Python) | bandit | CI (every PR) |
| Lint / code quality | ruff | CI (every PR) |
| Dependency updates | Renovate | Automated PRs |
| SBOM | Syft (CycloneDX) | On every `v*` release tag |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead: GitHub → Security → **"Report a vulnerability"** (private disclosure)
or contact the repository owner directly.

Response SLA:
- **Acknowledgement:** within 7 days
- **Fix or mitigation:** within 30 days for confirmed vulnerabilities

No bug bounty programme — reports are handled promptly and credited in the
release notes if desired.
