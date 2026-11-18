"""Convert JSON-stat and JSON-stat2 datasets to tidy pandas data."""

from __future__ import annotations

from itertools import product
from math import prod
from typing import Any, Mapping

import pandas as pd

from .exceptions import ResponseFormatError


def category_codes(dimension: Mapping[str, Any]) -> list[str]:
    """Return category codes in the provider-declared dimension order."""
    category = dimension.get("category", {})
    index = category.get("index", {})
    if isinstance(index, dict):
        return [
            str(code)
            for code, position in sorted(index.items(), key=lambda pair: pair[1])
        ]
    if isinstance(index, list):
        return [str(code) for code in index]
    labels = category.get("label", {})
    if isinstance(labels, dict):
        return list(labels)
    raise ResponseFormatError("No category codes found in JSON-stat dimension")


def jsonstat_to_frame(
    payload: Mapping[str, Any], labels: bool = False
) -> pd.DataFrame:
    """Return a one-row-per-observation DataFrame from JSON-stat data.

    Dimension codes are kept by default because labels can change with language.
    Missing or suppressed observations remain missing and status flags are retained.
    """
    dataset = payload.get("dataset", payload)
    if not isinstance(dataset, dict) or "value" not in dataset or dataset["value"] is None:
        raise ResponseFormatError(
            "Expected a JSON-stat dataset containing data values"
        )
    dimensions = dataset.get("dimension", {})
    # JSON-stat 1.x commonly stores id/size/role inside the dimension object,
    # while JSON-stat2 stores them on the dataset. Support both layouts.
    ids = dataset.get("id") or (
        dimensions.get("id", []) if isinstance(dimensions, dict) else []
    )
    if not ids or not isinstance(dimensions, dict):
        raise ResponseFormatError("Missing JSON-stat id/dimension metadata")

    all_codes = [category_codes(dimensions[dimension]) for dimension in ids]
    expected = prod(len(codes) for codes in all_codes)
    declared_size = dataset.get("size")
    if declared_size is None and isinstance(dimensions, dict):
        declared_size = dimensions.get("size")
    if declared_size is not None and list(declared_size) != [
        len(codes) for codes in all_codes
    ]:
        raise ResponseFormatError(
            "JSON-stat size does not match dimension categories"
        )

    raw_values = dataset["value"]
    if isinstance(raw_values, dict):
        values = [raw_values.get(str(index)) for index in range(expected)]
    elif isinstance(raw_values, list):
        if len(raw_values) != expected:
            raise ResponseFormatError(
                f"JSON-stat has {len(raw_values)} values; expected {expected}"
            )
        values = raw_values
    else:
        raise ResponseFormatError("Unsupported JSON-stat value shape")

    frame = pd.DataFrame.from_records(product(*all_codes), columns=ids)
    frame["value"] = pd.to_numeric(pd.Series(values), errors="coerce").to_numpy()

    statuses = dataset.get("status")
    if statuses:
        if isinstance(statuses, dict):
            frame["status"] = [statuses.get(str(index)) for index in range(expected)]
        elif isinstance(statuses, list):
            if len(statuses) != expected:
                raise ResponseFormatError("JSON-stat status array length mismatch")
            frame["status"] = statuses

    if labels:
        for dimension in ids:
            label_map = (
                dimensions[dimension].get("category", {}).get("label", {})
            )
            if isinstance(label_map, dict):
                frame[dimension] = frame[dimension].map(
                    lambda code: label_map.get(code, code)
                )

    frame.attrs.update(
        {
            "title": dataset.get("label"),
            "source": dataset.get("source"),
            "updated": dataset.get("updated"),
            "notes": dataset.get("note"),
        }
    )
    return frame
