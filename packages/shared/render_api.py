"""
Render.com REST API client.

Provides a typed, extensible client for the Render API (https://api.render.com/v1).
Use for service management, deploys, env vars, and future endpoints.

Environment:
  - RENDER_API_KEY or RENDER_API_TOKEN: API key from dashboard.render.com → Account → API Keys

Usage:
  from shared.render_api import get_render_client

  client = get_render_client()
  if client:
      services = client.list_services()
      client.trigger_deploy(service_id)
  else:
      # API key not configured (e.g. local dev)
      pass
"""

from __future__ import annotations

import os
from typing import Any

import httpx

RENDER_API_BASE = "https://api.render.com/v1"
DEFAULT_TIMEOUT = 30.0


def _get_api_key() -> str | None:
    """Resolve API key from env. Supports RENDER_API_KEY and RENDER_API_TOKEN."""
    return (
        os.environ.get("RENDER_API_KEY")
        or os.environ.get("RENDER_API_TOKEN")
        or None
    )


class RenderAPIError(Exception):
    """Raised when a Render API request fails."""

    def __init__(self, message: str, status_code: int | None = None, response_text: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class RenderAPIClient:
    """
    Client for Render.com REST API.

    Extensible for additional endpoints. See https://api-docs.render.com/
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = RENDER_API_BASE,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key or _get_api_key()
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    @property
    def is_configured(self) -> bool:
        """True if API key is set and client can make requests."""
        return bool(self._api_key)

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Execute HTTP request and return JSON body."""
        if not self._api_key:
            raise RenderAPIError("RENDER_API_KEY or RENDER_API_TOKEN not set")
        url = f"{self._base_url}{path}" if path.startswith("/") else f"{self._base_url}/{path}"
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.request(
                method,
                url,
                headers=self._headers,
                json=json,
                params=params,
            )
            if resp.status_code >= 400:
                raise RenderAPIError(
                    f"Render API error: {resp.status_code}",
                    status_code=resp.status_code,
                    response_text=resp.text[:500],
                )
            if resp.status_code == 204:
                return {}
            return resp.json()

    # ── Services ─────────────────────────────────────────────────

    def list_services(
        self,
        *,
        limit: int = 100,
        cursor: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        List all services in the workspace.
        Returns list of service objects (wrapped in {'service': ...} by API).
        """
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        data = self._request("GET", "/services", params=params)
        items = data if isinstance(data, list) else data.get("items", [])
        return [item.get("service", item) for item in items]

    def get_service(self, service_id: str) -> dict[str, Any]:
        """Get a single service by ID."""
        data = self._request("GET", f"/services/{service_id}")
        return data.get("service", data)

    # ── Deploys ──────────────────────────────────────────────────

    def trigger_deploy(
        self,
        service_id: str,
        *,
        clear_cache: bool = False,
    ) -> dict[str, Any]:
        """
        Trigger a new deploy for a service.
        Returns deploy object.
        """
        body: dict[str, Any] = {}
        if clear_cache:
            body["clearCache"] = "clear"
        data = self._request("POST", f"/services/{service_id}/deploys", json=body)
        return data.get("deploy", data)

    def list_deploys(
        self,
        service_id: str,
        *,
        limit: int = 20,
        cursor: str | None = None,
    ) -> list[dict[str, Any]]:
        """List deploys for a service."""
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        data = self._request("GET", f"/services/{service_id}/deploys", params=params)
        items = data if isinstance(data, list) else data.get("items", [])
        return [item.get("deploy", item) for item in items]

    def get_deploy(self, service_id: str, deploy_id: str) -> dict[str, Any]:
        """Get a single deploy by ID."""
        data = self._request("GET", f"/services/{service_id}/deploys/{deploy_id}")
        return data.get("deploy", data)

    # ── Environment variables ─────────────────────────────────────

    def list_env_vars(self, service_id: str) -> list[dict[str, Any]]:
        """
        List environment variables for a service.
        Returns list of env var objects (key, value, etc.).
        """
        data = self._request("GET", f"/services/{service_id}/env-vars")
        items = data if isinstance(data, list) else data.get("items", [])
        return [item.get("envVar", item) for item in items]

    def set_env_var(
        self,
        service_id: str,
        key: str,
        value: str,
        *,
        env_var_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create or update an environment variable.
        If env_var_id is provided, updates existing; otherwise creates new.
        """
        body = {"key": key, "value": value}
        if env_var_id:
            return self._request(
                "PATCH",
                f"/services/{service_id}/env-vars/{env_var_id}",
                json=body,
            )
        data = self._request("PUT", f"/services/{service_id}/env-vars", json=body)
        return data.get("envVar", data)

    def delete_env_var(self, service_id: str, env_var_id: str) -> None:
        """Delete an environment variable."""
        self._request("DELETE", f"/services/{service_id}/env-vars/{env_var_id}")

    def bulk_set_env_vars(
        self,
        service_id: str,
        env_vars: dict[str, str],
        *,
        preserve_existing: bool = True,
        remove_keys: list[str] | None = None,
    ) -> None:
        """
        Set multiple env vars. Merges with existing if preserve_existing=True.
        Uses GET + merge + PUT. Preserves vars not in env_vars when preserve_existing.
        remove_keys: keys to exclude from final payload (e.g. deprecated/wrong casing).
        """
        merged: dict[str, str] = {}
        if preserve_existing:
            for ev in self.list_env_vars(service_id):
                k = ev.get("key")
                v = ev.get("value") or ev.get("generatedValue", "")
                if k:
                    merged[k] = str(v) if v else ""
        for k, v in env_vars.items():
            merged[k] = str(v)
        to_remove = set(remove_keys or [])
        payload = [
            {"key": k, "value": v}
            for k, v in merged.items()
            if k not in to_remove
        ]
        self._request("PUT", f"/services/{service_id}/env-vars", json=payload)

    # ── Extensible: add more endpoints as needed ─────────────────
    # e.g. custom_domains, jobs, cron_jobs, postgres, redis, etc.
    # See https://api-docs.render.com/


def get_render_client(
    api_key: str | None = None,
    base_url: str = RENDER_API_BASE,
) -> RenderAPIClient | None:
    """
    Return a configured RenderAPIClient, or None if no API key is set.

    Use when Render API is optional (e.g. local dev). For scripts that require
    the API, call get_render_client() and check is_configured, or raise.
    """
    key = api_key or _get_api_key()
    if not key:
        return None
    return RenderAPIClient(api_key=key, base_url=base_url)


def require_render_client(api_key: str | None = None) -> RenderAPIClient:
    """
    Return a configured RenderAPIClient. Raises if API key is not set.
    Use for scripts that must have Render API access.
    """
    client = get_render_client(api_key=api_key)
    if not client or not client.is_configured:
        raise RenderAPIError(
            "RENDER_API_KEY or RENDER_API_TOKEN not set. "
            "Get a key from dashboard.render.com → Account → API Keys"
        )
    return client
