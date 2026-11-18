from __future__ import annotations

import json

import pandas as pd
import pytest
import requests

from nordicstats import ResponseFormatError, SelectionError, jsonstat_to_frame
from nordicstats.client_base import add_provenance, require_dimensions, selection_values
from nordicstats.http import response_json


def test_selection_normalization_and_dimension_errors():
    assert selection_values({"Region": "00", "Year": [2024, 2025]}) == {
        "Region": ["00"],
        "Year": ["2024", "2025"],
    }
    with pytest.raises(SelectionError, match="at least one"):
        selection_values({"Region": []})
    with pytest.raises(SelectionError, match="Unknown.*missing"):
        require_dimensions({"Wrong": ["x"]}, ["Region", "Year"])


def test_jsonstat_rejects_bad_size_and_value_length():
    base = {
        "id": ["Year"],
        "dimension": {"Year": {"category": {"index": ["2024", "2025"]}}},
    }
    with pytest.raises(ResponseFormatError, match="size"):
        jsonstat_to_frame({**base, "size": [3], "value": [1, 2]})
    with pytest.raises(ResponseFormatError, match="1 values; expected 2"):
        jsonstat_to_frame({**base, "size": [2], "value": [1]})


def test_jsonstat_v1_dimension_contains_id_and_size():
    payload = {
        "dataset": {
            "dimension": {
                "Region": {
                    "category": {
                        "index": {"000": 0},
                        "label": {"000": "All Denmark"},
                    }
                },
                "ContentsCode": {
                    "category": {
                        "index": {"FOLK1C": 0},
                        "label": {"FOLK1C": "Population"},
                        "unit": {"FOLK1C": {"base": "Number", "decimals": 0}},
                    }
                },
                "Tid": {
                    "category": {
                        "index": {"2026K3": 0, "2026K4": 1},
                    }
                },
                "id": ["Region", "ContentsCode", "Tid"],
                "size": [1, 1, 2],
                "role": {"metric": ["ContentsCode"], "time": ["Tid"]},
            },
            "label": "Population by region and time",
            "source": "Statistics Denmark",
            "value": [6_031_699, 6_044_001],
        }
    }
    frame = jsonstat_to_frame(payload)
    assert frame.to_dict("records") == [
        {
            "Region": "000",
            "ContentsCode": "FOLK1C",
            "Tid": "2026K3",
            "value": 6_031_699,
        },
        {
            "Region": "000",
            "ContentsCode": "FOLK1C",
            "Tid": "2026K4",
            "value": 6_044_001,
        },
    ]
    assert frame.attrs["source"] == "Statistics Denmark"


def test_http_json_error_contains_url_and_response_excerpt():
    response = requests.Response()
    response.status_code = 200
    response.url = "https://example.test/table"
    response._content = b"<html>not json</html>"
    with pytest.raises(ResponseFormatError, match="example.test.*not json"):
        response_json(response)


def test_provenance_is_structured_and_timestamped():
    frame = pd.DataFrame({"Year": ["2025"], "value": [42]})
    result = add_provenance(
        frame,
        source_key="test",
        source_name="Test Statistics",
        table_id="T1",
        api_url="https://example.test/data",
        selection={"Year": ["2025"]},
        metadata={"unit": "people"},
    )
    assert result.attrs["source_key"] == "test"
    assert result.attrs["selection"] == {"Year": ["2025"]}
    assert result.attrs["retrieved_at_utc"].endswith("+00:00")
    assert result.attrs["metadata"]["unit"] == "people"


def test_response_json_accepts_valid_payload():
    response = requests.Response()
    response.status_code = 200
    response.url = "https://example.test/table"
    response._content = json.dumps({"ok": True}).encode()
    assert response_json(response) == {"ok": True}
