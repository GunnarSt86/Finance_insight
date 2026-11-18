"""Shared, deliberately small HTTP helpers for provider adapters."""

from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import APIError, ResponseFormatError

DEFAULT_TIMEOUT = 30
DATA_TIMEOUT = 60


def create_session() -> requests.Session:
    """Create a session with bounded retries for transient provider failures."""
    session = requests.Session()
    session.headers.update({"User-Agent": "NordicStats/0.1 (Python requests)"})
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),
        respect_retry_after_header=True,
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def response_json(response: requests.Response) -> Any:
    """Validate an HTTP response and decode JSON with useful provider context."""
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text[:700].replace("\n", " ")
        raise APIError(
            f"API error {response.status_code} at {response.url}: {detail}"
        ) from exc
    try:
        return response.json()
    except ValueError as exc:
        raise ResponseFormatError(
            f"Expected JSON at {response.url}; got {response.text[:300]!r}"
        ) from exc
