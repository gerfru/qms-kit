"""qms-kit CLI — entry point for deploying the QMS scaffold."""

from __future__ import annotations

import os
from pathlib import Path

import click

from src.core.config import load_config
from src.core.renderer import render_template

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
CONFIG_DIR = Path(__file__).parent.parent / "config"


@click.group()
def cli() -> None:
    """qms-kit: deploy an ISO 9001 QMS scaffold into your target platform."""


@cli.command()
@click.option(
    "--target",
    required=True,
    type=click.Choice(["selfhosted", "atlassian", "m365"]),
    help="Deployment target platform.",
)
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to the client overlay config (e.g. config/clients/acme.yaml).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Render templates and validate config without writing to the target.",
)
def deploy(target: str, config_path: Path, dry_run: bool) -> None:
    """Deploy the QMS scaffold to the specified target platform."""
    core_path = CONFIG_DIR / "core.yaml"

    click.echo(f"Loading config: core={core_path}, overlay={config_path}")
    config = load_config(core_path, config_path)
    click.echo(
        f"Config loaded: {config.organisation.name} "
        f"({config.meta.standard}, {len(config.documents)} documents)"
    )

    # Render all templates that have a template key set
    rendered: dict[str, tuple[str, str]] = {}

    # Space index page
    index_content = render_template(
        template_name="qms_index.md.j2",
        config=config,
        templates_dir=TEMPLATES_DIR,
    )
    rendered["qms_index"] = ("QM Manual", index_content)
    click.echo("  Rendered: qms_index (qms_index.md.j2)")

    for doc in config.documents:
        if doc.template is None:
            continue
        template_file = f"{doc.template}.md.j2"
        content = render_template(
            template_name=template_file,
            config=config,
            templates_dir=TEMPLATES_DIR,
            extra={
                "procedure_title": doc.title,
                "doc_id": f"QMS-{doc.clause}-{doc.id.upper()[:8]}",
                "clause": doc.clause,
                "owner_role": "Quality Management Officer",
                "approver": config.organisation.management,
                "author": config.organisation.quality_officer,
                "date": "TBD",
                # Record-template placeholders — filled in per instance
                "audit_date": "TBD",
                "auditor": "TBD",
                "audit_scope": "TBD",
                "contact": "TBD",
                "capa_id": "CAPA-XXXX-NNN",
                "opened_date": "TBD",
                "opened_by": "TBD",
                "source_ref": "TBD",
                "participants": "TBD",
            },
        )
        rendered[doc.id] = (doc.title, content)
        click.echo(f"  Rendered: {doc.id} ({template_file})")

    if dry_run:
        click.echo(f"\nDry run complete — {len(rendered)} template(s) rendered, nothing deployed.")
        return

    if target == "selfhosted":
        _deploy_selfhosted(config, rendered)
    elif target == "atlassian":
        _deploy_atlassian(config, rendered)
    elif target == "m365":
        raise click.ClickException("M365 adapter not yet implemented (Phase 3).")


_ENV_VARS: dict[str, list[str]] = {
    "selfhosted": ["XWIKI_PASSWORD", "REDMINE_API_KEY"],
    "atlassian": ["ATLASSIAN_API_TOKEN"],
    "m365": ["M365_CLIENT_ID", "M365_CLIENT_SECRET", "M365_TENANT_ID"],
}


@cli.command()
@click.option(
    "--target",
    required=True,
    type=click.Choice(["selfhosted", "atlassian", "m365"]),
    help="Deployment target platform.",
)
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to the client overlay config.",
)
def validate(target: str, config_path: Path) -> None:
    """Validate config and environment for a target — no changes written.

    Exits 0 if everything is ready to deploy, 1 if any check fails.
    Suitable for use in CI pipelines before a deploy step.
    """
    errors: list[str] = []

    # Config load + schema validation
    core_path = CONFIG_DIR / "core.yaml"
    click.echo(f"Loading config: core={core_path}, overlay={config_path}")
    try:
        config = load_config(core_path, config_path)
    except Exception as exc:
        raise click.ClickException(f"Config invalid: {exc}") from exc
    click.echo(
        f"Config loaded: {config.organisation.name} "
        f"({config.meta.standard}, {len(config.documents)} documents)"
    )

    # Target-specific config block
    if target == "selfhosted" and config.selfhosted is None:
        errors.append("selfhosted config block missing in overlay")
    if target == "atlassian" and config.atlassian is None:
        errors.append("atlassian config block missing in overlay")

    # Required env vars
    missing_vars = [v for v in _ENV_VARS.get(target, []) if not os.environ.get(v)]
    for var in missing_vars:
        errors.append(f"env var not set: {var}")

    # Template rendering
    click.echo("Rendering templates...")
    render_errors = 0
    try:
        render_template("qms_index.md.j2", config=config, templates_dir=TEMPLATES_DIR)
    except Exception as exc:
        errors.append(f"qms_index.md.j2: {exc}")
        render_errors += 1

    for doc in config.documents:
        if doc.template is None:
            continue
        try:
            render_template(
                f"{doc.template}.md.j2",
                config=config,
                templates_dir=TEMPLATES_DIR,
                extra={
                    "procedure_title": doc.title,
                    "doc_id": f"QMS-{doc.clause}-{doc.id.upper()[:8]}",
                    "clause": doc.clause,
                    "owner_role": "Quality Management Officer",
                    "approver": config.organisation.management,
                    "author": config.organisation.quality_officer,
                    "date": "TBD",
                    "audit_date": "TBD",
                    "auditor": "TBD",
                    "audit_scope": "TBD",
                    "contact": "TBD",
                    "capa_id": "CAPA-XXXX-NNN",
                    "opened_date": "TBD",
                    "opened_by": "TBD",
                    "source_ref": "TBD",
                    "participants": "TBD",
                },
            )
        except Exception as exc:
            errors.append(f"{doc.template}.md.j2: {exc}")
            render_errors += 1

    templated = sum(1 for d in config.documents if d.template) + 1  # +1 for index
    rendered_ok = templated - render_errors
    click.echo(f"  {rendered_ok}/{templated} templates rendered successfully")

    if errors:
        click.echo("\nValidation FAILED:")
        for err in errors:
            click.echo(f"  ✗ {err}")
        raise click.ClickException(f"{len(errors)} check(s) failed.")

    click.echo(f"\nValidation OK — ready to deploy --target {target}")


def _deploy_atlassian(config: object, rendered: dict[str, tuple[str, str]]) -> None:
    from adapters.atlassian.confluence import ConfluenceAdapter
    from adapters.atlassian.jira import JiraAdapter
    from src.core.config import CoreConfig

    cfg = config if isinstance(config, CoreConfig) else None
    if cfg is None or cfg.atlassian is None:
        raise click.ClickException("atlassian config block missing in overlay.")

    click.echo("\nDeploying to Atlassian Cloud (Confluence + Jira)...")

    confluence = ConfluenceAdapter(cfg)
    confluence.deploy(rendered)

    jira = JiraAdapter(cfg)
    jira.deploy(cfg.atlassian.jira.issue_type_mapping)

    click.echo("\nDone.")


def _deploy_selfhosted(config: object, rendered: dict[str, tuple[str, str]]) -> None:
    from adapters.selfhosted.redmine import RedmineAdapter
    from adapters.selfhosted.xwiki import XWikiAdapter
    from src.core.config import CoreConfig

    cfg = config if isinstance(config, CoreConfig) else None
    if cfg is None or cfg.selfhosted is None:
        raise click.ClickException("selfhosted config block missing in overlay.")

    click.echo("\nDeploying to self-hosted (XWiki + Redmine)...")

    xwiki = XWikiAdapter(cfg)
    xwiki.deploy(rendered)

    redmine = RedmineAdapter(cfg)
    redmine.deploy(cfg.selfhosted.redmine.tracker_mapping)

    click.echo("\nDone.")
