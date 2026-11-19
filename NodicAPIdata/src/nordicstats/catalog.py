"""Normalized table catalogues across supported provider families."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .sources import SOURCES, client_for

CATALOG_COLUMNS = [
    "source_key",
    "country",
    "api_family",
    "table_id",
    "table_path",
    "title",
    "description",
    "updated",
    "first_period",
    "last_period",
]


def _first_existing(frame: pd.DataFrame, *names: str) -> pd.Series:
    for name in names:
        if name in frame.columns:
            return frame[name]
    return pd.Series(pd.NA, index=frame.index, dtype="object")


def _normalize(
    frame: pd.DataFrame, *, source_key: str, family: str, country: str
) -> pd.DataFrame:
    """Map provider-specific catalogue fields to a small stable schema."""
    normalized = pd.DataFrame(index=frame.index)
    normalized["source_key"] = source_key
    normalized["country"] = country
    normalized["api_family"] = family
    normalized["table_id"] = _first_existing(frame, "id", "table", "tableId")
    normalized["table_path"] = _first_existing(frame, "path", "tablePath")
    normalized["title"] = _first_existing(frame, "label", "text", "title")
    normalized["description"] = _first_existing(
        frame, "description", "note", "subjectText"
    )
    normalized["updated"] = _first_existing(
        frame, "updated", "updatedDate", "latestUpdate"
    )
    normalized["first_period"] = _first_existing(frame, "firstPeriod")
    normalized["last_period"] = _first_existing(frame, "lastPeriod")
    return normalized.reset_index(drop=True)


def catalog(
    source_key: str,
    *,
    query: str = "",
    limit: int = 100,
    language: str = "en",
    session: Any = None,
) -> pd.DataFrame:
    """Return a normalized, bounded table catalogue for one source.

    PxWeb v2 providers support a server-side query. Denmark returns its table
    list and is filtered locally. PxWeb v1 uses hierarchical directories and
    will gain a separately bounded crawler; use ``client.browse()`` meanwhile.
    """
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 1000:
        raise ValueError("limit must be an integer from 1 to 1000")

    key = source_key.lower()
    try:
        source = SOURCES[key]
    except KeyError as exc:
        raise KeyError(
            f"Unknown source {source_key!r}. Choose from: {', '.join(SOURCES)}"
        ) from exc

    client = client_for(key, language=language, session=session)
    if source.family == "pxweb_v2":
        raw = client.search(query, page_size=limit, page=1)
    elif source.family == "statbank_dk":
        raw = client.tables()
        if query:
            title = _first_existing(raw, "text", "label", "title").astype("string")
            raw = raw[title.str.contains(query, case=False, na=False, regex=False)]
        raw = raw.head(limit)
    elif source.family == "pxweb_v1":
        raise NotImplementedError(
            f"{source.name} exposes a hierarchical PxWeb v1 catalogue. "
            f"Use client_for({key!r}).browse() for now; a bounded recursive "
            "catalogue walker is the next implementation step."
        )
    else:
        raise NotImplementedError(
            f"{source.name} has no catalogue adapter yet ({source.family})."
        )

    result = _normalize(
        raw, source_key=key, family=source.family, country=source.country
    )
    result.attrs.update(
        {
            "source_key": key,
            "query": query,
            "limit": limit,
            "complete": len(result) < limit,
        }
    )
    return result[CATALOG_COLUMNS]
