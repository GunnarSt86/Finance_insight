from __future__ import annotations

from unittest.mock import Mock
import pandas as pd
import pytest

from nordicstats import SOURCES, DenmarkStatbank, client_for, sources_dataframe
from nordicstats.sources import PxWebV1, PxWebV2


class Response:
    def __init__(self, json_data, status=200):
        self._data = json_data
        self.status_code = status
        self.url = "https://test.example/api"
        self.text = ""

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


def test_registry_and_factories():
    assert len(SOURCES) >= 15
    assert isinstance(client_for("finland", session=Mock()), PxWebV1)
    assert isinstance(client_for("norway", session=Mock()), PxWebV2)
    assert isinstance(client_for("denmark", session=Mock()), DenmarkStatbank)
    assert isinstance(sources_dataframe(), pd.DataFrame)
    registry = sources_dataframe().set_index("key")
    assert registry.loc["iceland", "status"] == "working"
    assert registry.loc["iceland", "verified_on"] == "2026-11-18"
    assert registry.loc["estonia", "status"] == "unverified"
    with pytest.raises(NotImplementedError):
        client_for("eurostat")


def test_v1_source_attribution():
    session = Mock()
    session.get.return_value = Response({"variables": [
        {"code": "Year", "values": ["2024"]}
    ]})
    session.post.return_value = Response({"class": "dataset", "id": ["Year"],
        "size": [1], "dimension": {"Year": {"category": {
            "index": {"2024": 0}, "label": {"2024": "2024"}}}},
        "value": [123]})
    result = client_for("finland", session=session).fetch("table.px", {"Year": ["2024"]})
    assert result["value"].iloc[0] == 123
    assert result.attrs["source_key"] == "finland"
    assert result.attrs["agency"] == "Statistics Finland (StatFin)"
    assert result.attrs["table_id"] == "table.px"
    assert result.attrs["retrieved_at_utc"].endswith("+00:00")


def test_v2_country_wrapper_metadata_and_search():
    session = Mock()
    session.get.return_value = Response({"tables": [{"id": "T1", "label": "Population"}]})
    df = client_for("latvia", session=session).search("population")
    assert df.loc[0, "id"] == "T1"
    args, kwargs = session.get.call_args
    assert args[0] == "https://api.stat.gov.lv/api/v2/tables"
    assert kwargs["params"]["lang"] == "en"


def test_denmark_request_structure_and_jsonstat():
    session = Mock()
    metadata = {"variables": [
        {"id": "TIME", "text": "Year", "values": [{"id": "2024", "text": "2024"}]},
        {"id": "SEX", "text": "Sex", "values": [{"id": "T", "text": "Total"}]},
    ]}
    result = {"dataset": {"id": ["TIME", "SEX"], "size": [1, 1],
        "dimension": {
            "TIME": {"category": {"index": {"2024": 0}, "label": {"2024": "2024"}}},
            "SEX": {"category": {"index": {"T": 0}, "label": {"T": "Total"}}},
        }, "value": [8]}}
    session.post.side_effect = [Response(metadata), Response(result)]
    client = client_for("denmark", session=session)
    frame = client.fetch("DEMO", {"TIME": ["2024"], "SEX": ["T"]})
    assert frame["value"].iloc[0] == 8
    assert frame.attrs["source_key"] == "denmark"
    assert frame.attrs["table_id"] == "DEMO"
    assert frame.attrs["selection"] == {"TIME": ["2024"], "SEX": ["T"]}
    args, kwargs = session.post.call_args
    assert args[0] == "https://api.statbank.dk/v1/data"
    assert kwargs["json"]["format"] == "JSONSTAT"
    assert kwargs["json"]["variables"] == [
        {"code": "TIME", "values": ["2024"]}, {"code": "SEX", "values": ["T"]}
    ]
