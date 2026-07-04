"""XWiki adapter — creates spaces and pages via the XWiki REST API."""

from __future__ import annotations

import os
from typing import Any

import requests

from src.core.config import CoreConfig


class XWikiAdapter:
    """Seeds QMS document structure into an XWiki instance.

    Authentication: username + XWIKI_PASSWORD env var.
    API reference: https://www.xwiki.org/xwiki/bin/view/Documentation/UserGuide/Features/XWikiRESTfulAPI
    """

    def __init__(self, config: CoreConfig) -> None:
        if config.selfhosted is None:
            raise ValueError("selfhosted config block is required for target=selfhosted")
        xwiki = config.selfhosted.xwiki
        self._base_url = xwiki.base_url.rstrip("/")
        self._space_key = xwiki.space_key
        self._username = xwiki.username
        self._password = os.environ.get("XWIKI_PASSWORD", "")

    @property
    def _auth(self) -> tuple[str, str]:
        return (self._username, self._password)

    def _page_url(self, page_name: str) -> str:
        return f"{self._base_url}/rest/wikis/xwiki/spaces/{self._space_key}/pages/{page_name}"

    def _put(self, url: str, payload: dict[str, Any]) -> None:
        resp = requests.put(url, json=payload, auth=self._auth, timeout=30)
        resp.raise_for_status()

    def page_exists(self, page_name: str) -> bool:
        resp = requests.get(self._page_url(page_name), auth=self._auth, timeout=10)
        return resp.status_code == 200

    def create_or_update_page(self, page_name: str, title: str, content: str) -> None:
        """Idempotent: creates the page if absent, updates content if present."""
        payload = {"title": title, "content": content, "syntax": "markdown/1.2"}
        self._put(self._page_url(page_name), payload)

    def deploy(self, rendered_pages: dict[str, tuple[str, str]]) -> None:
        """Deploy all rendered pages.

        Args:
            rendered_pages: mapping of page_name -> (title, rendered_markdown)
        """
        for page_name, (title, content) in rendered_pages.items():
            self.create_or_update_page(page_name, title, content)
            print(f"  XWiki: upserted page '{page_name}'")
