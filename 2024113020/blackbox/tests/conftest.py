"""Pytest setup for QuickCart black-box API tests."""

from __future__ import annotations

import os
from typing import Any

import pytest
import requests


BASE_URL = os.getenv("QUICKCART_BASE_URL", "http://localhost:8080").rstrip("/")
ROLL_NUMBER = os.getenv("QUICKCART_ROLL_NUMBER", "2024113020")
USER_ID = os.getenv("QUICKCART_USER_ID", "1")
TIMEOUT_SECONDS = float(os.getenv("QUICKCART_TIMEOUT", "8"))


def _request(method: str, path: str, *, headers: dict[str, str] | None = None, json: dict[str, Any] | None = None):
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    return requests.request(
        method=method,
        url=f"{BASE_URL}{path}",
        headers=req_headers,
        json=json,
        timeout=TIMEOUT_SECONDS,
    )


@pytest.fixture(scope="session")
def api_available() -> bool:
    """Return True if API server is reachable."""
    try:
        resp = _request("GET", "/api/v1/admin/products", headers={"X-Roll-Number": ROLL_NUMBER})
        return resp.status_code in {200, 401, 400}
    except requests.RequestException:
        return False


@pytest.fixture(scope="session")
def base_url() -> str:
    """Provide base URL for endpoint composition."""
    return BASE_URL


@pytest.fixture(scope="session")
def common_headers() -> dict[str, str]:
    """Provide valid common headers for user-scoped endpoints."""
    return {
        "X-Roll-Number": ROLL_NUMBER,
        "X-User-ID": USER_ID,
    }


@pytest.fixture(scope="session")
def admin_headers() -> dict[str, str]:
    """Provide valid headers for admin endpoints."""
    return {"X-Roll-Number": ROLL_NUMBER}


@pytest.fixture(scope="session")
def client(api_available: bool):
    """Return a callable HTTP client; skip tests if server is unavailable."""
    if not api_available:
        pytest.skip(
            "QuickCart API is not reachable. Start server with docker and set QUICKCART_BASE_URL if needed."
        )

    def _client(method: str, path: str, *, headers: dict[str, str] | None = None, json: dict[str, Any] | None = None):
        return _request(method, path, headers=headers, json=json)

    return _client
