"""Small, opt-in end-to-end checks against official provider APIs."""

from __future__ import annotations

import os

import pandas as pd
import pytest

import nordicstats as ns

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_API_TESTS") != "1",
        reason="set RUN_LIVE_API_TESTS=1 to call official APIs",
    ),
]


@pytest.mark.parametrize(
    ("source_key", "table_id"),
    [
        (
            "iceland",
            "Ibuar/mannfjoldi/1_yfirlit/Yfirlit_mannfjolda/MAN00101.px",
        ),
        ("sweden", "TAB638"),
        ("norway", "05810"),
        ("finland", "vaerak/11ra.px"),
        ("denmark", "FOLK1C"),
    ],
)
def test_core_provider_small_fetch(source_key: str, table_id: str):
    client = ns.client_for(source_key)
    variables = client.variables(table_id)
    assert not variables.empty
    assert {"code", "label", "n_values"}.issubset(variables.columns)

    selection = client.example_selection(table_id, last_n=2)
    frame = client.fetch(table_id, selection, max_cells=100)

    assert isinstance(frame, pd.DataFrame)
    assert not frame.empty
    assert "value" in frame.columns
    assert frame.attrs["source_key"] == source_key
    assert frame.attrs["table_id"] == table_id
    assert frame.attrs["retrieved_at_utc"].endswith("+00:00")
