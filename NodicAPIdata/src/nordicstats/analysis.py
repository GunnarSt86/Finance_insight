"""Small compatibility helpers for already-harmonized analysis data."""

from __future__ import annotations

import pandas as pd


def comparable_time_series(
    iceland: pd.DataFrame,
    sweden: pd.DataFrame,
    iceland_period: str,
    sweden_period: str,
    period_to_year: bool = False,
) -> pd.DataFrame:
    """Merge two already-harmonized one-observation-per-period tables."""
    first = iceland[[iceland_period, "value"]].rename(
        columns={iceland_period: "period", "value": "Iceland"}
    ).copy()
    second = sweden[[sweden_period, "value"]].rename(
        columns={sweden_period: "period", "value": "Sweden"}
    ).copy()
    if period_to_year:
        first["period"] = pd.to_numeric(first["period"], errors="raise").astype(
            "int64"
        )
        second["period"] = pd.to_numeric(second["period"], errors="raise").astype(
            "int64"
        )
    else:
        first["period"] = first["period"].astype(str)
        second["period"] = second["period"].astype(str)
    if first["period"].duplicated().any() or second["period"].duplicated().any():
        raise ValueError(
            "Each country must have exactly ONE observation per period. "
            "Filter/aggregate categories first."
        )
    return (
        first.merge(second, on="period", how="inner", validate="one_to_one")
        .sort_values("period")
        .reset_index(drop=True)
    )
