"""PxWeb API v2 adapter: search tables, inspect metadata, and fetch data."""

from __future__ import annotations

from math import prod
import re
from typing import Any, Mapping, Sequence
from urllib.parse import quote

import pandas as pd
import requests

from .client_base import add_provenance, require_dimensions, selection_values
from .exceptions import SelectionError
from .http import DATA_TIMEOUT, DEFAULT_TIMEOUT, create_session, response_json
from .jsonstat import category_codes, jsonstat_to_frame

SWEDEN_BASE = "https://statistikdatabasen.scb.se/api/v2"
_V2_EXPRESSION = re.compile(
    r"^(?:top|bottom|range|from|to)\(.+\)$", re.IGNORECASE
)


def _is_expression(value: str) -> bool:
    """Return whether a value uses a documented PxWeb v2 selector."""
    return "*" in value or "?" in value or bool(_V2_EXPRESSION.match(value))


class SwedenPxWeb:
    """PxWeb v2 client.

    The historical class name is kept for compatibility. ``sources.PxWebV2``
    supplies other provider base URLs using the same protocol.
    """

    def __init__(
        self,
        base_url: str = SWEDEN_BASE,
        language: str = "en",
        session: requests.Session | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.language = language
        self.session = session or create_session()

    def search(self, term: str, page_size: int = 20, page: int = 1) -> pd.DataFrame:
        """Search the provider's table catalogue."""
        if page_size < 1 or page < 1:
            raise ValueError("page_size and page must both be at least 1")
        result = response_json(
            self.session.get(
                f"{self.base_url}/tables",
                params={
                    "lang": self.language,
                    "query": term,
                    "pageSize": page_size,
                    "pageNumber": page,
                },
                timeout=DEFAULT_TIMEOUT,
            )
        )
        return pd.DataFrame(result.get("tables", []))

    def _table_url(self, table_id: str, operation: str) -> str:
        encoded_id = quote(table_id, safe="")
        return f"{self.base_url}/tables/{encoded_id}/{operation}"

    def metadata(self, table_id: str) -> dict[str, Any]:
        """Return the provider's unmodified table metadata."""
        return response_json(
            self.session.get(
                self._table_url(table_id, "metadata"),
                params={"lang": self.language},
                timeout=DEFAULT_TIMEOUT,
            )
        )

    def variables(self, table_id: str) -> pd.DataFrame:
        """Summarize table dimensions and a small sample of their values."""
        metadata = self.metadata(table_id)
        rows = []
        for code in metadata.get("id", []):
            dimension = metadata["dimension"][code]
            codes = category_codes(dimension)
            labels = dimension.get("category", {}).get("label", {})
            rows.append(
                {
                    "code": code,
                    "label": dimension.get("label", code),
                    "n_values": len(codes),
                    "sample_codes": codes[:8],
                    "sample_labels": [labels.get(value, value) for value in codes[:8]],
                    "time": code in metadata.get("role", {}).get("time", []),
                }
            )
        return pd.DataFrame(rows)

    def value_codes(self, table_id: str, variable: str) -> pd.DataFrame:
        """Return exact selectable codes and labels for one dimension."""
        metadata = self.metadata(table_id)
        if variable not in metadata["dimension"]:
            raise KeyError(f"Variable {variable!r} not found")
        dimension = metadata["dimension"][variable]
        codes = category_codes(dimension)
        labels = dimension.get("category", {}).get("label", {})
        return pd.DataFrame(
            {"code": codes, "label": [labels.get(code, code) for code in codes]}
        )

    def example_selection(
        self, table_id: str, last_n: int = 5
    ) -> dict[str, list[str]]:
        """Use the first non-time code and a v2 latest-values expression."""
        if last_n < 1:
            raise SelectionError("last_n must be at least 1")
        metadata = self.metadata(table_id)
        time_dimensions = set(metadata.get("role", {}).get("time", []))
        selection: dict[str, list[str]] = {}
        for code in metadata["id"]:
            choices = category_codes(metadata["dimension"][code])
            if not choices:
                raise SelectionError(f"Variable {code} has no codes")
            selection[code] = (
                [f"top({last_n})"] if code in time_dimensions else choices[:1]
            )
        return selection

    def fetch(
        self,
        table_id: str,
        selection: Mapping[str, str | Sequence[str]],
        labels: bool = False,
        max_cells: int = 100_000,
    ) -> pd.DataFrame:
        """GET an explicit selection and return tidy data.

        V2 expressions such as ``top(5)`` cannot be estimated locally; the
        provider's own request limit remains authoritative for those selections.
        """
        clean = selection_values(selection)
        metadata = self.metadata(table_id)
        available = metadata["id"]
        require_dimensions(clean, available)

        expression_used = False
        for code in available:
            allowed = set(category_codes(metadata["dimension"][code]))
            for value in clean[code]:
                if _is_expression(value):
                    expression_used = True
                elif value not in allowed:
                    raise SelectionError(f"Unknown value for {code}: {value!r}")

        if not expression_used:
            cell_count = prod(len(clean[code]) for code in available)
            if cell_count > max_cells:
                raise SelectionError(
                    f"Selected {cell_count:,} cells (limit {max_cells:,}); narrow the query"
                )

        params = [("lang", self.language), ("outputFormat", "json-stat2")]
        params.extend(
            (f"valueCodes[{code}]", ",".join(clean[code])) for code in available
        )
        data_url = self._table_url(table_id, "data")
        response = self.session.get(data_url, params=params, timeout=DATA_TIMEOUT)
        frame = jsonstat_to_frame(response_json(response), labels=labels)
        frame.attrs.update(
            {"agency": "Statistics Sweden", "table": table_id, "selection": clean}
        )
        return add_provenance(
            frame,
            source_key="sweden",
            source_name="Statistics Sweden",
            table_id=table_id,
            api_url=data_url,
            selection=clean,
            metadata=metadata,
        )
