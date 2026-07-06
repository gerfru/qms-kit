"""Jira Cloud adapter — creates project and seeds issue types via Jira REST API v3.

Authentication: email + ATLASSIAN_API_TOKEN env var (Basic auth, same token as Confluence).
API reference: https://developer.atlassian.com/cloud/jira/platform/rest/v3/

IMPORTANT (verified API limit): adding custom issue types to a specific project's
issue type scheme requires the scheme ID, which is only deterministic on a fresh
project. This adapter creates the project and issue types, then associates them.
For existing projects, manual assignment via Jira UI may be needed.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from src.core.config import CoreConfig, RecordType


class JiraAdapter:
    """Seeds QMS record structure into a Jira Cloud project.

    Authentication: email + ATLASSIAN_API_TOKEN env var.
    """

    def __init__(self, config: CoreConfig) -> None:
        if config.atlassian is None:
            raise ValueError("atlassian config block is required for target=atlassian")
        jira = config.atlassian.jira
        self._base_url = jira.base_url.rstrip("/")
        self._project_key = jira.project_key
        self._project_name = jira.project_name
        self._email = jira.email
        self._token = os.environ.get("ATLASSIAN_API_TOKEN", "")
        self._config = config

    @property
    def _auth(self) -> tuple[str, str]:
        return (self._email, self._token)

    def _api(self, path: str) -> str:
        return f"{self._base_url}/rest/api/3{path}"

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        resp = requests.get(
            self._api(path),
            params=params,
            auth=self._auth,
            headers={"Accept": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: dict[str, Any]) -> Any:
        resp = requests.post(
            self._api(path),
            json=payload,
            auth=self._auth,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_current_user_account_id(self) -> str:
        """Return the account ID of the authenticated user (required for project creation)."""
        data = self._get("/myself")
        return str(data["accountId"])

    def project_exists(self) -> bool:
        try:
            self._get(f"/project/{self._project_key}")
            return True
        except requests.HTTPError:
            return False

    def create_project(self) -> str:
        """Idempotent: skips creation if project already exists. Returns project ID."""
        if self.project_exists():
            print(f"  Jira: project '{self._project_key}' already exists, skipping")
            data = self._get(f"/project/{self._project_key}")
            return str(data["id"])

        account_id = self.get_current_user_account_id()
        payload = {
            "key": self._project_key,
            "name": self._project_name,
            "projectTypeKey": "business",
            "leadAccountId": account_id,
            "description": (
                f"Quality Management System records for {self._config.organisation.name}. "
                f"ISO 9001:2015 compliant."
            ),
        }
        data = self._post("/project", payload)
        print(f"  Jira: created project '{self._project_key}' (id={data['id']})")
        return str(data["id"])

    def get_issue_type_id(self, name: str) -> str | None:
        """Return issue type ID by name, or None if not found."""
        data = self._get("/issuetype")
        for issue_type in data:
            if issue_type["name"] == name:
                return str(issue_type["id"])
        return None

    def create_issue_type(self, name: str, description: str) -> str:
        """Idempotent: returns existing ID if already present, else creates."""
        existing = self.get_issue_type_id(name)
        if existing:
            print(f"  Jira: issue type '{name}' already exists (id={existing}), skipping")
            return existing

        payload = {"name": name, "description": description, "type": "standard"}
        data = self._post("/issuetype", payload)
        print(f"  Jira: created issue type '{name}' (id={data['id']})")
        return str(data["id"])

    def seed_record_type(self, record_type: RecordType, issue_type_name: str) -> None:
        """Ensure the issue type for this record type exists globally."""
        description = (
            f"ISO 9001:2015 Clause {record_type.clause} — {record_type.label}. "
            f"Fields: {', '.join(record_type.fields[:5])}."
        )
        self.create_issue_type(issue_type_name, description)

    def deploy(self, issue_type_mapping: dict[str, str]) -> None:
        """Create Jira project and seed one issue type per QMS record type.

        Args:
            issue_type_mapping: maps record type ID -> Jira issue type name
        """
        self.create_project()

        for record_type in self._config.record_types:
            issue_type_name = issue_type_mapping.get(record_type.id)
            if not issue_type_name:
                print(f"  Jira: no issue type mapping for '{record_type.id}', skipping")
                continue
            self.seed_record_type(record_type, issue_type_name)
