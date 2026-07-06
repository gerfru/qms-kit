"""qms-kit CLI — entry point for deploying the QMS scaffold."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import click

from src.core.config import CoreConfig, load_config
from src.core.renderer import render_template

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
CONFIG_DIR = Path(__file__).parent.parent / "config"

_HTML_CSS = """
body{font-family:system-ui,sans-serif;max-width:860px;margin:2rem auto;padding:0 1.5rem;
  line-height:1.6;color:#1a1a1a}
h1{border-bottom:2px solid #0057b8;padding-bottom:.4rem;color:#0057b8}
h2{color:#333;margin-top:2rem}h3{color:#555}
table{border-collapse:collapse;width:100%}
th,td{border:1px solid #ccc;padding:.5rem .75rem;text-align:left}
th{background:#f0f4fa}tr:nth-child(even){background:#fafafa}
code{background:#f3f3f3;padding:.1rem .3rem;border-radius:3px;font-size:.9em}
pre{background:#f3f3f3;padding:1rem;border-radius:4px;overflow-x:auto}
blockquote{border-left:4px solid #0057b8;margin:0;padding:.5rem 1rem;color:#555}
a{color:#0057b8}.back{margin-bottom:1.5rem;font-size:.9em}
""".strip()


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _render_extra(config: CoreConfig, doc_id: str, clause: str, title: str) -> dict[str, Any]:
    return {
        "procedure_title": title,
        "doc_id": f"QMS-{clause}-{doc_id.upper()[:8]}",
        "clause": clause,
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
    }


def _render_all(config: CoreConfig) -> dict[str, tuple[str, str]]:
    """Render index + all templated documents. Returns {doc_id: (title, md_content)}."""
    rendered: dict[str, tuple[str, str]] = {}
    index_content = render_template("qms_index.md.j2", config=config, templates_dir=TEMPLATES_DIR)
    rendered["qms_index"] = ("QM Manual", index_content)
    for doc in config.documents:
        if doc.template is None:
            continue
        content = render_template(
            f"{doc.template}.md.j2",
            config=config,
            templates_dir=TEMPLATES_DIR,
            extra=_render_extra(config, doc.id, doc.clause, doc.title),
        )
        rendered[doc.id] = (doc.title, content)
    return rendered


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

    rendered = _render_all(config)
    for doc_id, (title, _) in rendered.items():
        click.echo(f"  Rendered: {doc_id} ({title})")

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
    templated = sum(1 for d in config.documents if d.template) + 1  # +1 for index
    try:
        _render_all(config)
    except Exception as exc:
        errors.append(f"template rendering failed: {exc}")
        render_errors += 1
    click.echo(f"  {templated - render_errors}/{templated} templates rendered successfully")

    if errors:
        click.echo("\nValidation FAILED:")
        for err in errors:
            click.echo(f"  ✗ {err}")
        raise click.ClickException(f"{len(errors)} check(s) failed.")

    click.echo(f"\nValidation OK — ready to deploy --target {target}")


@cli.command()
@click.option(
    "--format",
    "fmt",
    required=True,
    type=click.Choice(["md", "html"]),
    help="Output format: md (Markdown files) or html (standalone HTML pages).",
)
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to the client overlay config.",
)
@click.option(
    "--output-dir",
    "output_dir",
    default="qms-export",
    show_default=True,
    type=click.Path(path_type=Path),
    help="Directory to write exported files into.",
)
def export(fmt: str, config_path: Path, output_dir: Path) -> None:
    """Export QMS documents as Markdown or standalone HTML files.

    Useful for uploading to SharePoint document libraries, email distribution,
    or local archiving. The output directory is created if it does not exist.
    """
    import markdown as md_lib

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

    click.echo("Rendering templates...")
    try:
        rendered = _render_all(config)
    except Exception as exc:
        raise click.ClickException(f"Template rendering failed: {exc}") from exc

    output_dir.mkdir(parents=True, exist_ok=True)

    if fmt == "md":
        _export_md(rendered, output_dir)
    else:
        _export_html(rendered, output_dir, config.organisation.name, md_lib)

    click.echo(f"\nExport complete — {len(rendered)} file(s) written to {output_dir}/")


def _export_md(rendered: dict[str, tuple[str, str]], output_dir: Path) -> None:
    for _doc_id, (title, content) in rendered.items():
        slug = _slugify(title)
        out_path = output_dir / f"{slug}.md"
        out_path.write_text(content, encoding="utf-8")
        click.echo(f"  Written: {out_path.name}")


def _export_html(
    rendered: dict[str, tuple[str, str]],
    output_dir: Path,
    org_name: str,
    md_lib: object,
) -> None:
    # Build index entries while writing per-document files
    index_entries: list[tuple[str, str]] = []  # (filename, title)

    for _doc_id, (title, md_content) in rendered.items():
        slug = _slugify(title)
        filename = f"{slug}.html"
        body_html = md_lib.markdown(md_content, extensions=["tables", "fenced_code"])  # type: ignore[attr-defined]
        back = '<p class="back"><a href="index.html">← Back to QM Manual</a></p>'
        page = (
            f"<!doctype html><html lang='en'><head>"
            f"<meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{title} — {org_name}</title>"
            f"<style>{_HTML_CSS}</style></head><body>"
            f"{back}{body_html}</body></html>"
        )
        (output_dir / filename).write_text(page, encoding="utf-8")
        click.echo(f"  Written: {filename}")
        index_entries.append((filename, title))

    # Write index.html
    items = "\n".join(f'<li><a href="{fn}">{title}</a></li>' for fn, title in index_entries)
    index_page = (
        f"<!doctype html><html lang='en'><head>"
        f"<meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>QM Manual — {org_name}</title>"
        f"<style>{_HTML_CSS}</style></head><body>"
        f"<h1>QM Manual — {org_name}</h1>"
        f"<ul>{items}</ul></body></html>"
    )
    (output_dir / "index.html").write_text(index_page, encoding="utf-8")
    click.echo("  Written: index.html")


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
