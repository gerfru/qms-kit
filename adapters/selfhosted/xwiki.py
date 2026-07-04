"""XWiki adapter — creates spaces and pages via the XWiki REST API.

Templates are authored in Markdown (single source of truth).
This adapter converts Markdown to XWiki 2.1 syntax before uploading.
"""

from __future__ import annotations

import os
import re
from typing import Any

import requests

from src.core.config import CoreConfig


def md_to_xwiki(text: str) -> str:
    """Convert a subset of Markdown to XWiki 2.1 syntax.

    Covers the constructs used in qms-kit templates:
    headings, bold, italic, tables, unordered lists, blockquotes,
    horizontal rules, and inline code.
    """
    lines = text.splitlines()
    out: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Headings: # → =, ## → ==, up to 6 levels
        heading = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading:
            level = len(heading.group(1))
            marker = "=" * level
            out.append(f"{marker} {heading.group(2).strip()} {marker}")
            i += 1
            continue

        # Horizontal rule: --- or *** or ___
        if re.match(r"^(-{3,}|\*{3,}|_{3,})\s*$", line):
            out.append("----")
            i += 1
            continue

        # Table rows: | ... |
        if line.strip().startswith("|"):
            # Skip separator rows like |---|---|
            if re.match(r"^\|[\s\-:|]+\|", line):
                i += 1
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            # Detect header: previous non-empty line was also a table row,
            # next line is a separator — check next line
            is_header = i + 1 < len(lines) and re.match(r"^\|[\s\-:|]+\|", lines[i + 1])
            if is_header:
                out.append("|=" + "|=".join(_md_inline(c) for c in cells))
            else:
                out.append("|" + "|".join(_md_inline(c) for c in cells))
            i += 1
            continue

        # Blockquote: > text → indented paragraph (XWiki has no native blockquote)
        if line.startswith(">"):
            content = line.lstrip("> ").strip()
            out.append(_md_inline(content))
            i += 1
            continue

        # Unordered list: - item or * item (not table)
        list_match = re.match(r"^(\s*)[*\-]\s+(.*)", line)
        if list_match and not line.strip().startswith("|"):
            depth = len(list_match.group(1)) // 2 + 1
            out.append("*" * depth + " " + _md_inline(list_match.group(2)))
            i += 1
            continue

        # Ordered list: 1. item
        ol_match = re.match(r"^\s*\d+\.\s+(.*)", line)
        if ol_match:
            out.append("1. " + _md_inline(ol_match.group(1)))
            i += 1
            continue

        # Default: apply inline conversions
        out.append(_md_inline(line))
        i += 1

    return "\n".join(out)


def _md_inline(text: str) -> str:
    """Apply inline Markdown → XWiki 2.1 conversions."""
    # Bold+italic: ***text*** → **//text//**
    text = re.sub(r"\*{3}(.+?)\*{3}", r"**//\1//**", text)
    # Bold: **text** stays **text** in XWiki 2.1
    # Italic: *text* → //text// (only single asterisks not inside words)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"//\1//", text)
    # Italic: _text_ → //text//
    text = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"//\1//", text)
    # Inline code: `code` → {{code}}code{{/code}}
    text = re.sub(r"`([^`]+)`", r"{{{{\1}}}}", text)
    # Markdown links: [text](url) → [[text>>url]]
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"[[\1>>\2]]", text)
    # XWiki internal links passed through: [[...>>...]] already correct
    return text


class XWikiAdapter:
    """Seeds QMS document structure into an XWiki instance.

    Templates are Markdown; this adapter converts to XWiki 2.1 before upload.
    Authentication: username + XWIKI_PASSWORD env var.
    API reference: https://www.xwiki.org/xwiki/bin/view/Documentation/UserGuide/Features/XWikiRESTfulAPI
    """

    def __init__(self, config: CoreConfig) -> None:
        if config.selfhosted is None:
            raise ValueError("selfhosted config block is required for target=selfhosted")
        xwiki = config.selfhosted.xwiki
        self._base_url = xwiki.base_url.rstrip("/")
        self._space_key = xwiki.space_key
        self._parent_page = xwiki.parent_page
        self._username = xwiki.username
        self._password = os.environ.get("XWIKI_PASSWORD", "")

    @property
    def _auth(self) -> tuple[str, str]:
        return (self._username, self._password)

    def _page_url(self, page_name: str, parent: str | None = None) -> str:
        if parent:
            return (
                f"{self._base_url}/rest/wikis/xwiki"
                f"/spaces/{self._space_key}/spaces/{parent}/pages/{page_name}"
            )
        return f"{self._base_url}/rest/wikis/xwiki/spaces/{self._space_key}/pages/{page_name}"

    def _put(self, url: str, payload: dict[str, Any]) -> None:
        resp = requests.put(url, json=payload, auth=self._auth, timeout=30)
        resp.raise_for_status()

    def page_exists(self, page_name: str, parent: str | None = None) -> bool:
        resp = requests.get(self._page_url(page_name, parent), auth=self._auth, timeout=10)
        return resp.status_code == 200

    def create_or_update_page(
        self,
        page_name: str,
        title: str,
        content: str,
        parent: str | None = None,
    ) -> None:
        """Idempotent upsert. Content is Markdown; converted to XWiki 2.1 here."""
        xwiki_content = md_to_xwiki(content)
        payload = {"title": title, "content": xwiki_content, "syntax": "xwiki/2.1"}
        self._put(self._page_url(page_name, parent), payload)

    def deploy(self, rendered_pages: dict[str, tuple[str, str]]) -> None:
        """Deploy all rendered pages flat in the QMS space.

        Structure created:
          QMS/WebHome              ← space index page
          QMS/<page>               ← all document pages (flat, no intermediate parent)

        Args:
            rendered_pages: page_name -> (title, rendered_markdown)
        """
        # Space index page
        index_entry = rendered_pages.pop("qms_index", None)
        if index_entry:
            title, content = index_entry
            self.create_or_update_page("WebHome", title, content)
            print("  XWiki: upserted space index 'WebHome'")

        # All document pages flat in the space (no intermediate parent page)
        for page_name, (title, content) in rendered_pages.items():
            self.create_or_update_page(page_name, title, content)
            print(f"  XWiki: upserted page '{page_name}'")
