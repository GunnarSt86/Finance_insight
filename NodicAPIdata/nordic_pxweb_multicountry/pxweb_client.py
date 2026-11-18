"""Small, teaching-oriented clients for PxWeb v1 (Iceland) and v2 (Sweden).

Requires: requests, pandas. No API keys. See README.md for methodology and examples.
"""
from __future__ import annotations

from itertools import product
from math import prod
from typing import Any, Mapping, Sequence

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ICELAND_BASE = "https://px.hagstofa.is/pxen/api/v1/en"
SWEDEN_BASE = "https://statistikdatabasen.scb.se/api/v2"


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "NordicPxWebLearning/0.1 (Python requests)"})
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),
        respect_retry_after_header=True,
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def _json(response: requests.Response) -> Any:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text[:700].replace("\n", " ")
        raise RuntimeError(f"API error {response.status_code} at {response.url}: {detail}") from exc
    try:
        return response.json()
    except ValueError as exc:
        raise ValueError(f"Expected JSON at {response.url}; got {response.text[:300]!r}") from exc


def _codes_for_dimension(dimension: Mapping[str, Any]) -> list[str]:
    """Get ordered category codes from a JSON-stat 1/2 dimension."""
    category = dimension.get("category", {})
    index = category.get("index", {})
    if isinstance(index, dict):
        return [str(code) for code, position in sorted(index.items(), key=lambda pair: pair[1])]
    if isinstance(index, list):
        return [str(code) for code in index]
    labels = category.get("label", {})
    if isinstance(labels, dict):
        return list(labels)
    raise ValueError("No category codes found in JSON-stat dimension")


def jsonstat_to_frame(payload: Mapping[str, Any], labels: bool = False) -> pd.DataFrame:
    """Convert JSON-stat / JSON-stat2 data to tidy, one-row-per-cell pandas data.

    labels=False retains dimension codes for reproducible joins; labels=True replaces
    dimension *values* with human-readable labels, which can vary by language.
    Missing observations become NaN. A `status` column is retained when present.
    """
    dataset = payload.get("dataset", payload)  # JSON-stat v1 wraps the dataset
    if not isinstance(dataset, dict) or "value" not in dataset or dataset["value"] is None:
        raise ValueError("Expected a JSON-stat dataset containing data values")
    ids = dataset.get("id", [])
    dimensions = dataset.get("dimension", {})
    if not ids or not isinstance(dimensions, dict):
        raise ValueError("Missing JSON-stat id/dimension metadata")

    all_codes = [_codes_for_dimension(dimensions[dim]) for dim in ids]
    expected = prod(len(codes) for codes in all_codes)
    if "size" in dataset and list(dataset["size"]) != [len(x) for x in all_codes]:
        raise ValueError("JSON-stat size does not match dimension categories")

    raw_values = dataset["value"]
    if isinstance(raw_values, dict):
        # Some implementations encode sparse data cells as an object keyed by flat offset.
        values = [raw_values.get(str(i)) for i in range(expected)]
    elif isinstance(raw_values, list):
        if len(raw_values) != expected:
            raise ValueError(f"JSON-stat has {len(raw_values)} values; expected {expected}")
        values = raw_values
    else:
        raise ValueError("Unsupported JSON-stat value shape")

    rows = product(*all_codes)  # last dimension changes fastest (JSON-stat row-major)
    frame = pd.DataFrame.from_records(rows, columns=ids)
    frame["value"] = pd.to_numeric(pd.Series(values), errors="coerce").to_numpy()

    statuses = dataset.get("status")
    if statuses:
        if isinstance(statuses, dict):
            frame["status"] = [statuses.get(str(i)) for i in range(expected)]
        elif isinstance(statuses, list):
            if len(statuses) != expected:
                raise ValueError("JSON-stat status array length mismatch")
            frame["status"] = statuses

    if labels:
        for dim in ids:
            map_labels = dimensions[dim].get("category", {}).get("label", {})
            if isinstance(map_labels, dict):
                frame[dim] = frame[dim].map(lambda code: map_labels.get(code, code))
    frame.attrs.update({
        "title": dataset.get("label"), "source": dataset.get("source"),
        "updated": dataset.get("updated"), "notes": dataset.get("note"),
    })
    return frame


def _selection_values(selection: Mapping[str, str | Sequence[str]]) -> dict[str, list[str]]:
    cleaned = {}
    for dim, raw in selection.items():
        values = [raw] if isinstance(raw, str) else list(raw)
        if not values:
            raise ValueError(f"Variable {dim!r} must have at least one value")
        cleaned[dim] = [str(v) for v in values]
    return cleaned


def _require_dimensions(selection: Mapping[str, Any], available: Sequence[str]) -> None:
    unknown = sorted(set(selection).difference(available))
    missing = [dim for dim in available if dim not in selection]
    if unknown or missing:
        raise ValueError(
            f"Use exact variable codes from .variables(). Unknown: {unknown}; "
            f"missing: {missing}. Explicit selection avoids accidental aggregation."
        )


class IcelandPxWeb:
    """PxWeb v1 client. Paths are case-sensitive relative to the API root."""

    def __init__(self, base_url: str = ICELAND_BASE, session: requests.Session | None = None):
        self.base_url = base_url.rstrip("/")
        self.session = session or _session()

    def _url(self, path: str = "") -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def browse(self, directory: str = "") -> pd.DataFrame:
        """Navigate the folder tree. Entries have type 'l' (folder) or 't' (table)."""
        content = _json(self.session.get(self._url(directory), timeout=30))
        return pd.DataFrame(content)

    def metadata(self, table_path: str) -> dict[str, Any]:
        return _json(self.session.get(self._url(table_path), timeout=30))

    def variables(self, table_path: str) -> pd.DataFrame:
        data = self.metadata(table_path)
        return pd.DataFrame([
            {
                "code": v["code"], "label": v.get("text", v["code"]),
                "n_values": len(v.get("values", [])),
                "sample_codes": v.get("values", [])[:8],
                "sample_labels": v.get("valueTexts", [])[:8],
                "time": bool(v.get("time", False)),
            }
            for v in data["variables"]
        ])

    def value_codes(self, table_path: str, variable: str) -> pd.DataFrame:
        for item in self.metadata(table_path)["variables"]:
            if item["code"] == variable:
                values = item.get("values", [])
                labels = item.get("valueTexts", values)
                return pd.DataFrame({"code": values, "label": labels})
        raise KeyError(f"Variable {variable!r} not found")

    def example_selection(self, table_path: str, last_n: int = 5) -> dict[str, list[str]]:
        """Use first code for non-time variables and last N for time (preview only)."""
        result = {}
        for v in self.metadata(table_path)["variables"]:
            code, choices = v["code"], v.get("values", [])
            if not choices:
                raise ValueError(f"Variable {code} has no values")
            is_time = bool(v.get("time")) or v.get("text", "").lower() in ("year", "quarter", "month")
            result[code] = [str(x) for x in (choices[-last_n:] if is_time else choices[:1])]
        return result

    def fetch(self, table_path: str, selection: Mapping[str, str | Sequence[str]],
              labels: bool = False, max_cells: int = 100_000) -> pd.DataFrame:
        """POST selected category codes; return a tidy DataFrame.

        `selection` should specify every dimension. For example:
        {"Sex": ["..."], "Age": ["..."], "Year": ["2024", "2025"]}
        Use .variables() and .value_codes() to get actual codes first.
        """
        clean = _selection_values(selection)
        meta = self.metadata(table_path)
        variables = meta["variables"]
        available = [v["code"] for v in variables]
        _require_dimensions(clean, available)
        for variable in variables:
            code = variable["code"]
            allowed = {str(v) for v in variable.get("values", [])}
            bad = set(clean[code]) - allowed
            if bad:
                raise ValueError(f"Unknown values for {code}: {sorted(bad)}")
        count = prod(len(clean[code]) for code in available)
        if count > max_cells:
            raise ValueError(f"Selected {count:,} cells (limit {max_cells:,}); narrow the query")
        query = {
            "query": [
                {"code": code, "selection": {"filter": "item", "values": clean[code]}}
                for code in available
            ],
            "response": {"format": "json-stat2"},
        }
        response = self.session.post(self._url(table_path), json=query, timeout=60)
        # Older PxWeb v1 instances may offer JSON-stat rather than JSON-stat2.
        # Retry with that format only when the server explicitly rejects the format.
        if response.status_code == 400 and "format" in response.text.lower():
            query["response"]["format"] = "json-stat"
            response = self.session.post(self._url(table_path), json=query, timeout=60)
        data = _json(response)
        frame = jsonstat_to_frame(data, labels=labels)
        frame.attrs.update({"agency": "Statistics Iceland", "table": table_path, "query": query})
        return frame


class SwedenPxWeb:
    """PxWeb v2 client. Table identifiers such as TAB638 are stable ids."""

    def __init__(self, base_url: str = SWEDEN_BASE, language: str = "en",
                 session: requests.Session | None = None):
        self.base_url = base_url.rstrip("/")
        self.language = language
        self.session = session or _session()

    def search(self, term: str, page_size: int = 20, page: int = 1) -> pd.DataFrame:
        result = _json(self.session.get(
            f"{self.base_url}/tables",
            params={"lang": self.language, "query": term, "pageSize": page_size, "pageNumber": page},
            timeout=30,
        ))
        # PxWebApi v2 provides tables + page metadata.
        return pd.DataFrame(result.get("tables", []))

    def metadata(self, table_id: str) -> dict[str, Any]:
        return _json(self.session.get(
            f"{self.base_url}/tables/{table_id}/metadata",
            params={"lang": self.language}, timeout=30,
        ))

    def variables(self, table_id: str) -> pd.DataFrame:
        meta = self.metadata(table_id)
        rows = []
        for code in meta.get("id", []):
            dim = meta["dimension"][code]
            codes = _codes_for_dimension(dim)
            labels = dim.get("category", {}).get("label", {})
            rows.append({
                "code": code, "label": dim.get("label", code),
                "n_values": len(codes), "sample_codes": codes[:8],
                "sample_labels": [labels.get(c, c) for c in codes[:8]],
                "time": code in meta.get("role", {}).get("time", []),
            })
        return pd.DataFrame(rows)

    def value_codes(self, table_id: str, variable: str) -> pd.DataFrame:
        meta = self.metadata(table_id)
        if variable not in meta["dimension"]:
            raise KeyError(f"Variable {variable!r} not found")
        dim = meta["dimension"][variable]
        codes = _codes_for_dimension(dim)
        labels = dim.get("category", {}).get("label", {})
        return pd.DataFrame({"code": codes, "label": [labels.get(c, c) for c in codes]})

    def example_selection(self, table_id: str, last_n: int = 5) -> dict[str, list[str]]:
        """Preview selection: first category for each dimension; latest N for time."""
        meta = self.metadata(table_id)
        time_dimensions = set(meta.get("role", {}).get("time", []))
        selection = {}
        for code in meta["id"]:
            choices = _codes_for_dimension(meta["dimension"][code])
            if not choices:
                raise ValueError(f"Variable {code} has no codes")
            selection[code] = [f"top({last_n})"] if code in time_dimensions else choices[:1]
        return selection

    def fetch(self, table_id: str, selection: Mapping[str, str | Sequence[str]],
              labels: bool = False) -> pd.DataFrame:
        """GET selected codes. v2 expressions like 'top(5)'/'from(2020)' also work.

        All dimensions must be explicitly selected. The server enforces its cell limits.
        """
        clean = _selection_values(selection)
        meta = self.metadata(table_id)
        _require_dimensions(clean, meta["id"])
        params = [("lang", self.language), ("outputFormat", "json-stat2")]
        params.extend((f"valueCodes[{code}]", ",".join(clean[code])) for code in meta["id"])
        response = self.session.get(f"{self.base_url}/tables/{table_id}/data", params=params, timeout=60)
        data = _json(response)
        frame = jsonstat_to_frame(data, labels=labels)
        frame.attrs.update({"agency": "Statistics Sweden", "table": table_id, "selection": clean})
        return frame


def comparable_time_series(
    iceland: pd.DataFrame,
    sweden: pd.DataFrame,
    iceland_period: str,
    sweden_period: str,
    period_to_year: bool = False,
) -> pd.DataFrame:
    """Merge two already-harmonized one-observation-per-period tables.

    The caller must first select matching definitions and aggregate only where valid.
    For annual data, period_to_year=True parses periods like '2020', '2021'.
    """
    a = iceland[[iceland_period, "value"]].rename(columns={iceland_period: "period", "value": "Iceland"}).copy()
    b = sweden[[sweden_period, "value"]].rename(columns={sweden_period: "period", "value": "Sweden"}).copy()
    if period_to_year:
        a["period"] = pd.to_numeric(a["period"], errors="raise").astype("int64")
        b["period"] = pd.to_numeric(b["period"], errors="raise").astype("int64")
    else:
        a["period"] = a["period"].astype(str)
        b["period"] = b["period"].astype(str)
    if a["period"].duplicated().any() or b["period"].duplicated().any():
        raise ValueError("Each country must have exactly ONE observation per period. Filter/aggregate categories first.")
    return a.merge(b, on="period", how="inner", validate="one_to_one").sort_values("period").reset_index(drop=True)
