"""Teaching-oriented StatBank Denmark adapter (JSON-stat output).

This is not PxWeb: it has a different request format, but shares JSON-stat.
All data queries should use explicit metadata-derived variable codes.
"""
from __future__ import annotations

from math import prod
from typing import Mapping, Sequence

import pandas as pd
import requests

from .client_base import add_provenance, require_dimensions, selection_values
from .exceptions import SelectionError
from .http import create_session, response_json
from .jsonstat import jsonstat_to_frame


class DenmarkStatbank:
    def __init__(self, base_url="https://api.statbank.dk/v1", language="en", session=None):
        self.base_url = base_url.rstrip("/")
        self.language = language
        self.session = session or create_session()

    def _post_json(self, method: str, data: dict):
        payload = {"lang": self.language, **data}
        response = self.session.post(
            f"{self.base_url}/{method}", json=payload, timeout=60
        )
        return response_json(response)

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
             "sample_codes": [x.get("id", x) if isinstance(x, dict) else x for x in v.get("values", [])[:8]],
             "sample_labels": [x.get("text", x) if isinstance(x, dict) else x for x in v.get("values", [])[:8]],
             "time": bool(v.get("time", False))}
            for v in meta.get("variables", [])
        ])

    def value_codes(self, table_id: str, variable: str) -> pd.DataFrame:
        """Return the exact selectable codes and labels for one variable."""
        for item in self.metadata(table_id).get("variables", []):
            code = item.get("id", item.get("code"))
            if code == variable:
                values = item.get("values", [])
                return pd.DataFrame(
                    {
                        "code": [
                            value.get("id", value)
                            if isinstance(value, dict)
                            else value
                            for value in values
                        ],
                        "label": [
                            value.get("text", value)
                            if isinstance(value, dict)
                            else value
                            for value in values
                        ],
                    }
                )
        raise KeyError(f"Variable {variable!r} not found")

    def example_selection(self, table_id: str, last_n: int = 5) -> dict[str, list[str]]:
        """Build a small preview selection from current table metadata."""
        selection: dict[str, list[str]] = {}
        for item in self.metadata(table_id).get("variables", []):
            code = item.get("id", item.get("code"))
            values = [
                value.get("id", value) if isinstance(value, dict) else value
                for value in item.get("values", [])
            ]
            if not values:
                raise SelectionError(f"Variable {code} has no values")
            is_time = bool(item.get("time")) or item.get("text", "").lower() in {
                "year",
                "quarter",
                "month",
                "time",
            }
            selected = values[-last_n:] if is_time else values[:1]
            selection[str(code)] = [str(value) for value in selected]
        return selection

    def fetch(self, table_id: str, selection: Mapping[str, str | Sequence[str]], *,
              labels: bool = False, max_cells: int = 100_000) -> pd.DataFrame:
        """Fetch explicit variable codes as JSON-stat, then convert to a tidy DataFrame."""
        selected = selection_values(selection)
        meta = self.metadata(table_id)
        available = [v.get("id", v.get("code")) for v in meta.get("variables", [])]
        require_dimensions(selected, available)
        for variable in meta.get("variables", []):
            code = variable.get("id", variable.get("code"))
            allowed = {
                str(value.get("id", value) if isinstance(value, dict) else value)
                for value in variable.get("values", [])
            }
            invalid = set(selected[code]) - allowed
            if invalid:
                raise SelectionError(f"Unknown values for {code}: {sorted(invalid)}")
        count = prod(len(selected[code]) for code in available)
        if count > max_cells:
            raise SelectionError(
                f"Selected {count:,} cells, above the local limit {max_cells:,}"
            )
        query = {
            "table": table_id, "format": "JSONSTAT",
            "variables": [{"code": code, "values": selected[code]} for code in available],
        }
        payload = self._post_json("data", query)
        df = jsonstat_to_frame(payload, labels=labels)
        df.attrs.update(agency="Statistics Denmark (StatBank)", table=table_id,
                        source_key="denmark", source_url=f"{self.base_url}/data", selection=selected)
        return add_provenance(
            df,
            source_key="denmark",
            source_name="Statistics Denmark (StatBank)",
            table_id=table_id,
            api_url=f"{self.base_url}/data",
            selection=selected,
            metadata=meta,
        )
