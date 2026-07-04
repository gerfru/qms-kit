"""XWiki adapter — creates spaces and pages via the XWiki REST API."""

from __future__ import annotations

import os

import requests

from src.core.config import CoreConfig


class XWikiAdapter:
    """Seeds QMS document structure into an XWiki instance.

    Authentication: username + XWIKI_PASSWORD env var.
    API reference: https://www.xwiki.org/xwiki/bin/view/Documentation/UserGuide/Features/XWikiRESTfulAPI
    """

    def __init__(self, config: CoreConfig) -> None:
        # TODO: extract XWiki settings from overlay config once overlay schema is wired
        self._base_url = "http://localhost:8080"
        self._space_key = "QMS"
        self._username = "Admin"
        self._password = os.environ.get("XWIKI_PASSWORD", "")
        self._config = config

    @property
    def _auth(self) -> tuple[str, str]:
        return (self._username, self._password)

    def _page_url(self, page_name: str) -> str:
        return f"{self._base_url}/rest/wikis/xwiki/spaces/{self._space_key}/pages/{page_name}"

    def page_exists(self, page_name: str) -> bool:
        resp = requests.get(self._page_url(page_name), auth=self._auth, timeout=10)
        return resp.status_code == 200

    def create_or_update_page(self, page_name: str, title: str, content: str) -> None:
        """Idempotent: creates the page if absent, updates content if present."""
        url = self._page_url(page_name)
        payload = {"title": title, "content": content, "syntax": "markdown/1.2"}
        resp = requests.put(url, json=payload, auth=self._auth, timeout=30)
        resp.raise_for_status()

    def deploy(self, rendered_pages: dict[str, tuple[str, str]]) -> None:
        """Deploy all rendered pages.

        Args:
            rendered_pages: mapping of page_name -> (title, rendered_markdown)
        """
        for page_name, (title, content) in rendered_pages.items():
            self.create_or_update_page(page_name, title, content)
            print(f"  XWiki: upserted page '{page_name}'")
