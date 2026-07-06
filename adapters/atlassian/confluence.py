"""Confluence Cloud adapter — creates pages via the Confluence REST API v2.

Templates are authored in Markdown (single source of truth).
This adapter converts Markdown to Confluence Storage Format (XHTML) before uploading.
Authentication: email + ATLASSIAN_API_TOKEN env var (Basic auth).
API reference: https://developer.atlassian.com/cloud/confluence/rest/v2/
"""

from __future__ import annotations

import os
import re
from typing import Any

import requests

from src.core.config import CoreConfig


def md_to_confluence_storage(text: str) -> str:
    """Convert a subset of Markdown to Confluence Storage Format (XHTML).

    Covers the constructs used in qms-kit templates:
    headings, bold, italic, tables, lists, blockquotes, HR, inline code, links.
    """
    lines = text.splitlines()
    out: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Headings: # → <h1>, ## → <h2>, up to h6
        heading = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading:
            level = len(heading.group(1))
            out.append(f"<h{level}>{_cf_inline(heading.group(2).strip())}</h{level}>")
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^(-{3,}|\*{3,}|_{3,})\s*$", line):
            out.append("<hr/>")
            i += 1
            continue

        # Table: collect all consecutive table lines and render together
        if line.strip().startswith("|"):
            table_lines: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            out.append(_cf_table(table_lines))
            continue

        # Unordered list: collect consecutive items into one <ul>
        if re.match(r"^\s*[*\-]\s+", line) and not line.strip().startswith("|"):
            items: list[str] = []
            while i < len(lines) and re.match(r"^\s*[*\-]\s+", lines[i]):
                m = re.match(r"^\s*[*\-]\s+(.*)", lines[i])
                if m:
                    items.append(f"<li>{_cf_inline(m.group(1))}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue

        # Ordered list: collect consecutive items into one <ol>
        if re.match(r"^\s*\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                m = re.match(r"^\s*\d+\.\s+(.*)", lines[i])
                if m:
                    items.append(f"<li>{_cf_inline(m.group(1))}</li>")
                i += 1
            out.append("<ol>" + "".join(items) + "</ol>")
            continue

        # Blockquote
        if line.startswith(">"):
            content = line.lstrip("> ").strip()
            out.append(f"<blockquote><p>{_cf_inline(content)}</p></blockquote>")
            i += 1
            continue

        # Empty line → paragraph break
        if not line.strip():
            out.append("")
            i += 1
            continue

        # Default: wrap in paragraph
        out.append(f"<p>{_cf_inline(line)}</p>")
        i += 1

    return "\n".join(out)


def _cf_inline(text: str) -> str:
    """Apply inline Markdown → Confluence Storage Format conversions."""
    # Bold + italic: ***text***
    text = re.sub(r"\*{3}(.+?)\*{3}", r"<strong><em>\1</em></strong>", text)
    # Bold: **text**
    text = re.sub(r"\*{2}(.+?)\*{2}", r"<strong>\1</strong>", text)
    # Italic: *text* (single asterisk, not part of **)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    # Italic: _text_
    text = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"<em>\1</em>", text)
    # Inline code
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # Markdown links: [text](url) → <a href="url">text</a>
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def _cf_table(lines: list[str]) -> str:
    """Render a Markdown table as Confluence Storage Format XHTML table."""
    is_header = len(lines) > 1 and re.match(r"^\|[\s\-:|]+\|", lines[1])
    rows: list[str] = []

    for idx, line in enumerate(lines):
        if re.match(r"^\|[\s\-:|]+\|", line):
            continue  # skip separator row
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        tag = "th" if (idx == 0 and is_header) else "td"
        row = "<tr>" + "".join(f"<{tag}>{_cf_inline(c)}</{tag}>" for c in cells) + "</tr>"
        rows.append(row)

    return "<table><tbody>" + "".join(rows) + "</tbody></table>"


class ConfluenceAdapter:
    """Seeds QMS document structure into a Confluence Cloud space.

    Templates are Markdown; this adapter converts to Confluence Storage Format before upload.
    Authentication: email + ATLASSIAN_API_TOKEN env var (Basic auth).
    """

    def __init__(self, config: CoreConfig) -> None:
        if config.atlassian is None:
            raise ValueError("atlassian config block is required for target=atlassian")
        cf = config.atlassian.confluence
        self._base_url = cf.base_url.rstrip("/")
        self._space_key = cf.space_key
        self._parent_page_title = cf.parent_page_title
        self._email = cf.email
        self._token = os.environ.get("ATLASSIAN_API_TOKEN", "")

    @property
    def _auth(self) -> tuple[str, str]:
        return (self._email, self._token)

    def _api(self, path: str) -> str:
        return f"{self._base_url}/api/v2{path}"

    def get_page_id(self, title: str) -> str | None:
        """Return page ID if a page with this title exists in the space, else None."""
        resp = requests.get(
            self._api("/pages"),
            params={"spaceKey": self._space_key, "title": title},
            auth=self._auth,
            headers={"Accept": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return results[0]["id"] if results else None

    def create_or_update_page(
        self,
        title: str,
        content: str,
        parent_id: str | None = None,
    ) -> str:
        """Idempotent upsert. Content is Markdown; converted to Storage Format here.

        Returns the page ID.
        """
        storage_content = md_to_confluence_storage(content)
        body: dict[str, Any] = {
            "spaceId": self._get_space_id(),
            "title": title,
            "body": {"representation": "storage", "value": storage_content},
        }
        if parent_id:
            body["parentId"] = parent_id

        existing_id = self.get_page_id(title)
        if existing_id:
            # Update existing page — need current version number
            page = requests.get(
                self._api(f"/pages/{existing_id}"),
                auth=self._auth,
                headers={"Accept": "application/json"},
                timeout=15,
            )
            page.raise_for_status()
            version = page.json()["version"]["number"] + 1
            body["version"] = {"number": version}
            resp = requests.put(
                self._api(f"/pages/{existing_id}"),
                json=body,
                auth=self._auth,
                timeout=30,
            )
        else:
            resp = requests.post(
                self._api("/pages"),
                json=body,
                auth=self._auth,
                timeout=30,
            )

        resp.raise_for_status()
        return resp.json()["id"]

    def _get_space_id(self) -> str:
        """Resolve space key to numeric space ID (required by API v2)."""
        resp = requests.get(
            self._api("/spaces"),
            params={"keys": self._space_key},
            auth=self._auth,
            headers={"Accept": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            raise ValueError(f"Confluence space '{self._space_key}' not found.")
        return results[0]["id"]

    def deploy(self, rendered_pages: dict[str, tuple[str, str]]) -> None:
        """Deploy all rendered pages into the Confluence space.

        Structure created:
          <space>/QM Manual          ← index / root page
          <space>/QM Manual/<page>   ← all document pages as children

        Args:
            rendered_pages: page_name -> (title, rendered_markdown)
        """
        # Root index page
        index_entry = rendered_pages.pop("qms_index", None)
        index_title = self._parent_page_title
        if index_entry:
            _, content = index_entry
            root_id = self.create_or_update_page(index_title, content)
        else:
            root_id = self.create_or_update_page(index_title, f"# {index_title}\n")
        print(f"  Confluence: upserted root page '{index_title}' (id={root_id})")

        # All document pages as children of the root page
        for _page_name, (title, content) in rendered_pages.items():
            page_id = self.create_or_update_page(title, content, parent_id=root_id)
            print(f"  Confluence: upserted '{title}' (id={page_id})")
