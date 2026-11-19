from __future__ import annotations

from unittest.mock import Mock

import pytest

import nordicstats as ns


class Response:
    def __init__(self, payload):
        self.payload = payload
        self.status_code = 200
        self.url = "https://test.example/api"
        self.text = ""

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


def test_v2_catalog_is_normalized_and_bounded():
    session = Mock()
    session.get.return_value = Response(
        {
            "tables": [
                {
                    "id": "TAB1",
                    "label": "Population by region",
                    "description": "Annual population",
                    "updated": "2026-11-01",
                    "firstPeriod": "2000",
                    "lastPeriod": "2025",
                }
            ]
        }
    )

    result = ns.catalog("sweden", query="population", limit=25, session=session)

    assert result.to_dict("records") == [
        {
            "source_key": "sweden",
            "country": "Sweden",
            "api_family": "pxweb_v2",
            "table_id": "TAB1",
            "table_path": None,
            "title": "Population by region",
            "description": "Annual population",
            "updated": "2026-11-01",
            "first_period": "2000",
            "last_period": "2025",
        }
    ]
    _, kwargs = session.get.call_args
    assert kwargs["params"]["query"] == "population"
    assert kwargs["params"]["pageSize"] == 25


def test_denmark_catalog_filters_title_locally():
    session = Mock()
    session.post.return_value = Response(
        [
            {"id": "FOLK1C", "text": "Population by age"},
            {"id": "PRIS1", "text": "Consumer prices"},
        ]
    )

    result = ns.catalog("denmark", query="population", session=session)

    assert result[["table_id", "title"]].to_dict("records") == [
        {"table_id": "FOLK1C", "title": "Population by age"}
    ]


def test_v1_catalog_points_to_browse():
    with pytest.raises(NotImplementedError, match=r"\.browse\(\)"):
        ns.catalog("iceland")


@pytest.mark.parametrize("limit", [0, 1001, 1.5, True])
def test_catalog_limit_is_safe(limit):
    with pytest.raises(ValueError, match="limit"):
        ns.catalog("sweden", limit=limit)
