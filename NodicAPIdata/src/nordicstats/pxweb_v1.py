"""PxWeb API v1 adapter: browse folders, inspect metadata, and fetch data."""

from __future__ import annotations

from math import prod
from typing import Any, Mapping, Sequence
from urllib.parse import quote

import pandas as pd
import requests

from .client_base import add_provenance, require_dimensions, selection_values
from .exceptions import SelectionError
from .http import DATA_TIMEOUT, DEFAULT_TIMEOUT, create_session, response_json
from .jsonstat import jsonstat_to_frame

ICELAND_BASE = "https://px.hagstofa.is/pxen/api/v1/en"


class IcelandPxWeb:
    """PxWeb v1 client.

    The historical class name is kept for compatibility. ``sources.PxWebV1``
    supplies other provider base URLs using the same protocol.
    """

    def __init__(
        self,
        base_url: str = ICELAND_BASE,
        session: requests.Session | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.session = session or create_session()

    def _url(self, path: str = "") -> str:
        encoded_path = quote(path.lstrip("/"), safe="/")
        return f"{self.base_url}/{encoded_path}"

    def browse(self, directory: str = "") -> pd.DataFrame:
        """Navigate a folder whose entries are folders (``l``) or tables (``t``)."""
        content = response_json(
            self.session.get(self._url(directory), timeout=DEFAULT_TIMEOUT)
        )
        return pd.DataFrame(content)

    def metadata(self, table_path: str) -> dict[str, Any]:
        """Return the provider's unmodified table metadata."""
        return response_json(
            self.session.get(self._url(table_path), timeout=DEFAULT_TIMEOUT)
        )

    def variables(self, table_path: str) -> pd.DataFrame:
        """Summarize table dimensions and a small sample of their values."""
        data = self.metadata(table_path)
        return pd.DataFrame(
            [
                {
                    "code": variable["code"],
                    "label": variable.get("text", variable["code"]),
                    "n_values": len(variable.get("values", [])),
                    "sample_codes": variable.get("values", [])[:8],
                    "sample_labels": variable.get("valueTexts", [])[:8],
                    "time": bool(variable.get("time", False)),
                }
                for variable in data["variables"]
            ]
        )

    def value_codes(self, table_path: str, variable: str) -> pd.DataFrame:
        """Return exact selectable codes and labels for one dimension."""
        for item in self.metadata(table_path)["variables"]:
            if item["code"] == variable:
                values = item.get("values", [])
                labels = item.get("valueTexts", values)
                return pd.DataFrame({"code": values, "label": labels})
        raise KeyError(f"Variable {variable!r} not found")

    def example_selection(
        self, table_path: str, last_n: int = 5
    ) -> dict[str, list[str]]:
        """Use the first non-time code and latest time codes for a small preview."""
        if last_n < 1:
            raise SelectionError("last_n must be at least 1")
        result: dict[str, list[str]] = {}
        for variable in self.metadata(table_path)["variables"]:
            code = variable["code"]
            choices = variable.get("values", [])
            if not choices:
                raise SelectionError(f"Variable {code} has no values")
            is_time = bool(variable.get("time")) or variable.get(
                "text", ""
            ).lower() in {"year", "quarter", "month", "time"}
            selected = choices[-last_n:] if is_time else choices[:1]
            result[code] = [str(value) for value in selected]
        return result

    def fetch(
        self,
        table_path: str,
        selection: Mapping[str, str | Sequence[str]],
        labels: bool = False,
        max_cells: int = 100_000,
    ) -> pd.DataFrame:
        """POST an explicit category selection and return tidy data."""
        clean = selection_values(selection)
        metadata = self.metadata(table_path)
        variables = metadata["variables"]
        available = [variable["code"] for variable in variables]
        require_dimensions(clean, available)

        for variable in variables:
            code = variable["code"]
            allowed = {str(value) for value in variable.get("values", [])}
            invalid = set(clean[code]) - allowed
            if invalid:
                raise SelectionError(f"Unknown values for {code}: {sorted(invalid)}")

        cell_count = prod(len(clean[code]) for code in available)
        if cell_count > max_cells:
            raise SelectionError(
                f"Selected {cell_count:,} cells (limit {max_cells:,}); narrow the query"
            )

        query = {
            "query": [
                {
                    "code": code,
                    "selection": {"filter": "item", "values": clean[code]},
                }
                for code in available
            ],
            "response": {"format": "json-stat2"},
        }
        response = self.session.post(
            self._url(table_path), json=query, timeout=DATA_TIMEOUT
        )
        if response.status_code == 400 and "format" in response.text.lower():
            query["response"]["format"] = "json-stat"
            response = self.session.post(
                self._url(table_path), json=query, timeout=DATA_TIMEOUT
            )

        frame = jsonstat_to_frame(response_json(response), labels=labels)
        frame.attrs.update(
            {"agency": "Statistics Iceland", "table": table_path, "query": query}
        )
        return add_provenance(
            frame,
            source_key="iceland",
            source_name="Statistics Iceland",
            table_id=table_path,
            api_url=self._url(table_path),
            selection=clean,
            metadata=metadata,
        )
