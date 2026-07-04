"""qms-kit CLI — entry point for deploying the QMS scaffold."""

from __future__ import annotations

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
                "date": "TODO",
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
        raise click.ClickException("Atlassian adapter not yet implemented (Phase 2).")
    elif target == "m365":
        raise click.ClickException("M365 adapter not yet implemented (Phase 3).")


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
