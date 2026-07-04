"""Jinja2 template renderer — renders .md.j2 templates with config context."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from src.core.config import CoreConfig


def build_context(config: CoreConfig, extra: dict | None = None) -> dict:
    """Build the base Jinja2 context from a validated config."""
    ctx: dict = {
        "org_name": config.organisation.name,
        "org_short": config.organisation.short,
        "quality_officer": config.organisation.quality_officer,
        "management": config.organisation.management,
        "version": config.meta.version,
    }
    if extra:
        ctx.update(extra)
    return ctx


def render_template(
    template_name: str,
    config: CoreConfig,
    templates_dir: Path,
    extra: dict | None = None,
) -> str:
    """Render a single .md.j2 template and return the result as a string.

    Raises jinja2.UndefinedError if a placeholder has no value in context.
    """
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=("html",)),
        keep_trailing_newline=True,
    )
    template = env.get_template(template_name)
    context = build_context(config, extra)
    return template.render(**context)
