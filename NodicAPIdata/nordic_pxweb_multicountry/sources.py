"""Multi-country source registry and common PxWeb v1/v2 factory.

Only PxWeb sources have a functioning generic client. Non-PxWeb APIs are
registered for planning and require a separate adapter. Run `python sources.py`
to print the registry. Network access is NOT required to view the registry.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from pxweb_client import IcelandPxWeb, SwedenPxWeb

Family = Literal["pxweb_v1", "pxweb_v2", "statbank_dk", "custom", "eurostat", "sdmx"]


@dataclass(frozen=True)
class Source:
    key: str
    name: str
    country: str
    family: Family
    base_url: str
    docs_url: str
    status: str = "configured"  # configured, special, planned
    note: str = ""


SOURCES: dict[str, Source] = {
    "iceland": Source("iceland", "Statistics Iceland", "Iceland", "pxweb_v1",
        "https://px.hagstofa.is/pxen/api/v1/en",
        "https://statice.is/publications/open-data-access/"),
    "sweden": Source("sweden", "Statistics Sweden (SCB)", "Sweden", "pxweb_v2",
        "https://statistikdatabasen.scb.se/api/v2",
        "https://www.scb.se/en/services/open-data-api/pxwebapi/"),
    "norway": Source("norway", "Statistics Norway (SSB)", "Norway", "pxweb_v2",
        "https://data.ssb.no/api/pxwebapi/v2",
        "https://www.ssb.no/en/api/pxwebapi",
        note="SSB documents 30 queries/minute and a limit of 800,000 data cells/extract."),
    "finland": Source("finland", "Statistics Finland (StatFin)", "Finland", "pxweb_v1",
        "https://pxdata.stat.fi/PxWeb/api/v1/en/StatFin",
        "https://stat.fi/en/services/statistical-data-services/open-data-and-interfaces/interface-use-of-databases",
        note="Many table paths and variable codes changed on 8 June 2026; always fetch metadata."),
    "estonia": Source("estonia", "Statistics Estonia", "Estonia", "pxweb_v1",
        "https://andmed.stat.ee/api/v1/en/stat",
        "https://andmed.stat.ee/help/api-manual.pdf",
        note="The agency also has a second database named statsql; this registry starts with stat."),
    "latvia": Source("latvia", "Central Statistical Bureau of Latvia", "Latvia", "pxweb_v2",
        "https://api.stat.gov.lv/api/v2",
        "https://stat.gov.lv/en/api-un-kodu-vardnicas/api-v2",
        note="10,000 cells per request; 30 queries per 10 seconds."),
    "greenland": Source("greenland", "Statistics Greenland", "Greenland", "pxweb_v1",
        "https://bank.stat.gl/api/v1/en/Greenland",
        "https://statisticsgreenland.github.io/qmd/statistics_greenland.html"),
    "faroe_islands": Source("faroe_islands", "Statistics Faroe Islands", "Faroe Islands", "pxweb_v1",
        "https://statbank.hagstova.fo/api/v1/en/H2",
        "https://hagstova.fo/en/terms-use"),
    "aland": Source("aland", "Statistics and Research Åland (ÅSUB)", "Åland", "pxweb_v1",
        "https://pxweb.asub.ax/PXWeb/api/v1/en/Statistik",
        "https://pxweb.asub.ax/PXWeb/pxweb/en/Statistik/"),
    "slovenia": Source("slovenia", "Statistical Office of Slovenia", "Slovenia", "pxweb_v1",
        "https://pxweb.stat.si/SiStatData/api/v1/en/Data",
        "https://pxweb.stat.si/sistat/en/Home/Help"),
    "switzerland": Source("switzerland", "Swiss Federal Statistical Office", "Switzerland", "pxweb_v1",
        "https://www.pxweb.bfs.admin.ch/api/v1/en",
        "https://www.pxweb.bfs.admin.ch/",
        status="special", note="Swiss tables require their individual table URL; root-level browsing is not supported."),
    "nordic_statistics": Source("nordic_statistics", "Nordic Statistics Database", "Nordic region", "pxweb_v1",
        "https://pxweb.nordicstatistics.org/api/v1/en/Nordic%20Statistics",
        "https://www.nordicstatistics.org/about/",
        status="special", note="API root advertises database ID 'Nordic Statistics'; verify full DB route before use."),
    "denmark": Source("denmark", "Statistics Denmark (StatBank)", "Denmark", "statbank_dk",
        "https://api.statbank.dk/v1",
        "https://www.dst.dk/en/Statistik/hjaelp-til-statistikbanken/api",
        note="Separate REST API, but supports JSON-stat; use DenmarkStatbank adapter."),
    "lithuania": Source("lithuania", "Lithuanian Data Portal", "Lithuania", "custom",
        "https://api.dataportal.gov.lt",
        "https://guides.dataportal.gov.lt/docs/api", status="planned"),
    "eurostat": Source("eurostat", "Eurostat", "European Union", "eurostat",
        "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data",
        "https://ec.europa.eu/eurostat/en/web/user-guides/data-browser/api-data-access/api-introduction",
        status="planned", note="Supports JSON-stat 2.0; request syntax differs from PxWeb."),
    "oecd": Source("oecd", "OECD Data Explorer", "International", "sdmx",
        "https://sdmx.oecd.org/public/rest",
        "https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html",
        status="planned", note="SDMX API; requires a separate query and parsing adapter."),
}


class PxWebV1(IcelandPxWeb):
    """Generic country-specific PxWeb API v1 using the existing v1 client."""
    def __init__(self, source: Source, session=None):
        super().__init__(base_url=source.base_url, session=session)
        self.source = source

    def fetch(self, table_path, selection, labels=False, max_cells=100_000):
        df = super().fetch(table_path, selection, labels=labels, max_cells=max_cells)
        df.attrs.update(agency=self.source.name, source_key=self.source.key,
                        source_url=self._url(table_path))
        return df


class PxWebV2(SwedenPxWeb):
    """Generic country-specific PxWeb API v2 using the existing v2 client."""
    def __init__(self, source: Source, language="en", session=None):
        super().__init__(base_url=source.base_url, language=language, session=session)
        self.source = source

    def fetch(self, table_id, selection, labels=False):
        df = super().fetch(table_id, selection, labels=labels)
        df.attrs.update(agency=self.source.name, source_key=self.source.key,
                        source_url=f"{self.base_url}/tables/{table_id}/data")
        return df


def client_for(key: str, *, language="en", session=None):
    """Create a reusable API client from a country/region name.

    Examples: client_for('norway').search('population');
              client_for('aland').browse();
              client_for('denmark').metadata('FOLK1C').
    """
    try:
        source = SOURCES[key.lower()]
    except KeyError as e:
        raise KeyError(f"Unknown source {key!r}. Choose from: {', '.join(SOURCES)}") from e
    if source.family == "pxweb_v1":
        return PxWebV1(source, session=session)
    if source.family == "pxweb_v2":
        return PxWebV2(source, language=language, session=session)
    if source.family == "statbank_dk":
        from denmark_client import DenmarkStatbank
        return DenmarkStatbank(base_url=source.base_url, language=language, session=session)
    raise NotImplementedError(
        f"{source.name} is registered but has no adapter yet ({source.family}). "
        f"Documentation: {source.docs_url}"
    )


def sources_dataframe() -> pd.DataFrame:
    return pd.DataFrame([vars(source) for source in SOURCES.values()])


if __name__ == "__main__":
    with pd.option_context("display.max_rows", None, "display.max_colwidth", 45):
        print(sources_dataframe()[["key", "family", "status", "country"]].to_string(index=False))
