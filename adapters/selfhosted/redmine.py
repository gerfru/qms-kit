"""Redmine adapter — creates projects and seeds issue trackers via the Redmine REST API.

IMPORTANT (verified API limit): custom field DEFINITIONS cannot be created via the API.
Field definitions must be set up manually once. See docs/redmine-setup.md.
This adapter only seeds field VALUES on issues.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from src.core.config import CoreConfig, RecordType


class RedmineAdapter:
    """Seeds QMS record structure into a Redmine instance.

    Authentication: REDMINE_API_KEY env var.
    API reference: https://www.redmine.org/projects/redmine/wiki/Rest_api
    """

    def __init__(self, config: CoreConfig) -> None:
        if config.selfhosted is None:
            raise ValueError("selfhosted config block is required for target=selfhosted")
        redmine = config.selfhosted.redmine
        self._base_url = redmine.base_url.rstrip("/")
        self._project_key = redmine.project_key
        self._api_key = os.environ.get("REDMINE_API_KEY", "")
        self._config = config

    @property
    def _headers(self) -> dict[str, str]:
        return {"X-Redmine-API-Key": self._api_key, "Content-Type": "application/json"}

    def _get(self, path: str) -> Any:
        resp = requests.get(f"{self._base_url}{path}", headers=self._headers, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: dict[str, Any]) -> Any:
        resp = requests.post(
            f"{self._base_url}{path}", json=payload, headers=self._headers, timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    def project_exists(self) -> bool:
        try:
            self._get(f"/projects/{self._project_key}.json")
            return True
        except requests.HTTPError:
            return False

    def create_project(self) -> None:
        """Idempotent: skips creation if project already exists."""
        if self.project_exists():
            print(f"  Redmine: project '{self._project_key}' already exists, skipping")
            return
        payload = {
            "project": {
                "name": self._config.organisation.name,
                "identifier": self._project_key,
                "description": f"QMS records for {self._config.organisation.name}",
            }
        }
        self._post("/projects.json", payload)
        print(f"  Redmine: created project '{self._project_key}'")

    def get_tracker_id(self, tracker_name: str) -> int | None:
        """Look up tracker ID by name. Returns None if not found."""
        data = self._get("/trackers.json")
        for tracker in data.get("trackers", []):
            if tracker["name"] == tracker_name:
                return int(tracker["id"])
        return None

    def seed_record_type(self, record_type: RecordType, tracker_name: str) -> None:
        """Create a placeholder issue for a record type to confirm the tracker is wired."""
        tracker_id = self.get_tracker_id(tracker_name)
        if tracker_id is None:
            print(
                f"  Redmine: tracker '{tracker_name}' not found — "
                f"run manual setup first (docs/redmine-setup.md)"
            )
            return
        payload = {
            "issue": {
                "project_id": self._project_key,
                "tracker_id": tracker_id,
                "subject": f"[SCAFFOLD] {record_type.label} tracker ready",
                "description": (
                    f"This issue confirms the '{tracker_name}' tracker is configured.\n"
                    f"ISO 9001 clause: {record_type.clause}\n"
                    f"Expected fields: {', '.join(record_type.fields)}"
                ),
            }
        }
        self._post("/issues.json", payload)
        print(f"  Redmine: seeded tracker '{tracker_name}' with scaffold issue")

    def deploy(self, tracker_mapping: dict[str, str]) -> None:
        """Create project and seed one scaffold issue per record type.

        Args:
            tracker_mapping: maps record type ID -> Redmine tracker name
        """
        self.create_project()
        for record_type in self._config.record_types:
            tracker_name = tracker_mapping.get(record_type.id)
            if not tracker_name:
                print(f"  Redmine: no tracker mapping for '{record_type.id}', skipping")
                continue
            self.seed_record_type(record_type, tracker_name)
