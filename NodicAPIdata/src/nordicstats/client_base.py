"""Selection validation and provenance shared by API adapters."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

import pandas as pd

from .exceptions import SelectionError


def selection_values(
    selection: Mapping[str, str | Sequence[str]],
) -> dict[str, list[str]]:
    """Normalize scalar and sequence selections to lists of string codes."""
    cleaned: dict[str, list[str]] = {}
    for dimension, raw in selection.items():
        values = [raw] if isinstance(raw, str) else list(raw)
        if not values:
            raise SelectionError(
                f"Variable {dimension!r} must have at least one value"
            )
        cleaned[dimension] = [str(value) for value in values]
    return cleaned


def require_dimensions(selection: Mapping[str, Any], available: Sequence[str]) -> None:
    """Require an explicit selection for every table dimension."""
    unknown = sorted(set(selection).difference(available))
    missing = [dimension for dimension in available if dimension not in selection]
    if unknown or missing:
        raise SelectionError(
            "Use exact variable codes from .variables(). "
            f"Unknown: {unknown}; missing: {missing}. "
            "Explicit selection avoids accidental aggregation."
        )


def add_provenance(
    frame: pd.DataFrame,
    *,
    source_key: str,
    source_name: str,
    table_id: str,
    api_url: str,
    selection: Mapping[str, Sequence[str]],
    metadata: Mapping[str, Any] | None = None,
) -> pd.DataFrame:
    """Attach retrieval context without altering the tidy table columns."""
    frame.attrs.update(
        {
            "source_key": source_key,
            "source_name": source_name,
            "table_id": table_id,
            "api_url": api_url,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "selection": {key: list(values) for key, values in selection.items()},
        }
    )
    if metadata is not None:
        frame.attrs["metadata"] = dict(metadata)
    return frame
