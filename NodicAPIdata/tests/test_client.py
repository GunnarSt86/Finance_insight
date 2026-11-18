import pytest
from nordicstats import comparable_time_series, jsonstat_to_frame
from nordicstats.pxweb_client import _codes_for_dimension
import pandas as pd

SAMPLE = {
    "version": "2.0", "class": "dataset", "id": ["Region", "Year"], "size": [2, 2],
    "dimension": {
        "Region": {"label": "region", "category": {"index": {"IS": 0, "SE": 1}, "label": {"IS": "Iceland", "SE": "Sweden"}}},
        "Year": {"label": "year", "category": {"index": {"2024": 0, "2025": 1}, "label": {"2024": "2024", "2025": "2025"}}},
    },
    "value": [10, 11, None, 13], "status": {"2": ".."},
}


def test_jsonstat_row_major_and_missing():
    df = jsonstat_to_frame(SAMPLE)
    assert list(df.columns) == ["Region", "Year", "value", "status"]
    assert list(zip(df.Region, df.Year)) == [("IS", "2024"), ("IS", "2025"), ("SE", "2024"), ("SE", "2025")]
    assert df["value"].iloc[1] == 11
    assert pd.isna(df["value"].iloc[2])
    assert df["status"].iloc[2] == ".."


def test_labels_and_sparse_values():
    sparse = {**SAMPLE, "value": {"0": 1, "3": 4}, "status": {}}
    df = jsonstat_to_frame({"dataset": sparse}, labels=True)
    assert df.Region.tolist() == ["Iceland", "Iceland", "Sweden", "Sweden"]
    assert pd.isna(df["value"].iloc[1])


def test_list_category_index():
    assert _codes_for_dimension({"category": {"index": ["A", "B"]}}) == ["A", "B"]


def test_duplicate_times_refused():
    ice = pd.DataFrame({"Year": ["2024", "2024"], "value": [1, 2]})
    swe = pd.DataFrame({"Tid": ["2024"], "value": [10]})
    with pytest.raises(ValueError, match="ONE observation"):
        comparable_time_series(ice, swe, "Year", "Tid", period_to_year=True)


def test_alignment():
    ice = pd.DataFrame({"Year": ["2024", "2025"], "value": [1, 2]})
    swe = pd.DataFrame({"Tid": ["2025", "2026"], "value": [10, 11]})
    joint = comparable_time_series(ice, swe, "Year", "Tid", period_to_year=True)
    assert joint.to_dict("records") == [{"period": 2025, "Iceland": 2, "Sweden": 10}]


def test_iceland_post_request_offline():
    import json
    import requests
    from nordicstats import IcelandPxWeb

    meta = {"variables": [
        {"code": "Sex", "text": "Sex", "values": ["T", "M"], "valueTexts": ["Total", "Male"]},
        {"code": "Year", "text": "Year", "values": ["2024", "2025"], "valueTexts": ["2024", "2025"], "time": True},
    ]}
    payload = {"class": "dataset", "id": ["Sex", "Year"], "size": [1, 2],
               "dimension": {"Sex": {"category": {"index": ["T"], "label": {"T": "Total"}}},
                             "Year": {"category": {"index": ["2024", "2025"]}}},
               "value": [10, 11]}

    class FakeSession:
        def __init__(self):
            self.posts = []
        def get(self, url, **kwargs):
            r = requests.Response()
            r.status_code = 200
            r._content = json.dumps(meta).encode()
            r.url = url
            return r
        def post(self, url, json=None, **kwargs):
            self.posts.append((url, json))
            r = requests.Response()
            r.status_code = 200
            r._content = __import__('json').dumps(payload).encode()
            r.url = url
            return r

    s = FakeSession()
    client = IcelandPxWeb(session=s)
    frame = client.fetch("fake.px", {"Sex": "T", "Year": ["2024", "2025"]})
    assert frame["value"].tolist() == [10, 11]
    assert s.posts[0][1]["query"][0]["selection"]["values"] == ["T"]
    assert s.posts[0][1]["response"]["format"] == "json-stat2"


def test_sweden_get_request_offline():
    import json
    import requests
    from nordicstats import SwedenPxWeb

    meta = {"id": ["Region", "Tid"], "role": {"time": ["Tid"]},
            "dimension": {"Region": {"category": {"index": {"00": 0}, "label": {"00": "Sweden"}}},
                          "Tid": {"category": {"index": {"2024": 0, "2025": 1}}}}}
    payload = {"class": "dataset", "id": ["Region", "Tid"], "size": [1, 2],
               "dimension": meta["dimension"], "value": [15, 18]}

    class FakeSession:
        def __init__(self):
            self.gets = []
        def get(self, url, params=None, **kwargs):
            self.gets.append((url, params))
            r = requests.Response()
            r.status_code = 200
            r._content = json.dumps(payload if url.endswith('/data') else meta).encode()
            r.url = url
            return r

    s = FakeSession()
    client = SwedenPxWeb(session=s)
    frame = client.fetch("TABTEST", {"Region": "00", "Tid": ["2024", "2025"]})
    assert frame["value"].tolist() == [15, 18]
    assert ("valueCodes[Region]", "00") in s.gets[-1][1]
    assert ("valueCodes[Tid]", "2024,2025") in s.gets[-1][1]
