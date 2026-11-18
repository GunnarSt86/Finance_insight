"""Teaching-oriented StatBank Denmark adapter (JSON-stat output).

This is not PxWeb: it has a different request format, but shares JSON-stat.
All data queries should use explicit metadata-derived variable codes.
"""
from __future__ import annotations

from math import prod
from typing import Mapping, Sequence

import pandas as pd
import requests

from pxweb_client import _json, _require_dimensions, _selection_values, _session, jsonstat_to_frame


class DenmarkStatbank:
    def __init__(self, base_url="https://api.statbank.dk/v1", language="en", session=None):
        self.base_url = base_url.rstrip("/")
        self.language = language
        self.session = session or _session()

    def _post_json(self, method: str, data: dict):
        payload = {"lang": self.language, **data}
        response = self.session.post(
            f"{self.base_url}/{method}", json=payload, timeout=60
        )
        return _json(response)

    def subjects(self):
        """Return the top-level Danish statistical subject hierarchy."""
        return self._post_json("subjects", {"format": "JSON"})

    def tables(self):
        """Return the Danish table catalogue. Can be a large response."""
        return pd.DataFrame(self._post_json("tables", {"format": "JSON"}))

    def metadata(self, table_id: str) -> dict:
        return self._post_json("tableinfo", {"table": table_id, "format": "JSON"})

    def variables(self, table_id: str) -> pd.DataFrame:
        meta = self.metadata(table_id)
        return pd.DataFrame([
            {"code": v.get("id", v.get("code")), "label": v.get("text", ""),
             "n_values": len(v.get("values", [])),
             "sample_codes": [x.get("id", x) if isinstance(x, dict) else x for x in v.get("values", [])[:8]]}
            for v in meta.get("variables", [])
        ])

    def fetch(self, table_id: str, selection: Mapping[str, str | Sequence[str]], *,
              labels: bool = False, max_cells: int = 100_000) -> pd.DataFrame:
        """Fetch explicit variable codes as JSON-stat, then convert to a tidy DataFrame."""
        selected = _selection_values(selection)
        meta = self.metadata(table_id)
        available = [v.get("id", v.get("code")) for v in meta.get("variables", [])]
        _require_dimensions(selected, available)
        count = prod(len(selected[code]) for code in available)
        if count > max_cells:
            raise ValueError(f"Selected {count:,} cells, above the local limit {max_cells:,}")
        query = {
            "table": table_id, "format": "JSONSTAT",
            "variables": [{"code": code, "values": selected[code]} for code in available],
        }
        payload = self._post_json("data", query)
        df = jsonstat_to_frame(payload, labels=labels)
        df.attrs.update(agency="Statistics Denmark (StatBank)", table=table_id,
                        source_key="denmark", source_url=f"{self.base_url}/data", selection=selected)
        return df
