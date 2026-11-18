# Multi-country extension (November 2026)

This folder builds on the original Iceland/Sweden tutorial. It adds a **registry of statistical sources** (`sources.py`) and a dedicated Denmark adapter (`denmark_client.py`). The original `pxweb_client.py`, notebook, examples and tests are retained unchanged.

## List all sources (no internet required)

```bash
pip install -r requirements.txt
python sources.py
```

## Use the API clients

```python
from sources import client_for, sources_dataframe

print(sources_dataframe()[['key', 'country', 'family', 'status']])

# Same PxWeb v2 methods for Sweden, Norway, Latvia
norway = client_for('norway')
print(norway.search('population')[['id', 'label']].head())

# Same PxWeb v1 methods for Iceland, Finland, Estonia, Greenland, Faroe Islands, Åland, Slovenia
aland = client_for('aland')
print(aland.browse())

# Denmark has its own adapter but returns JSON-stat to the same pandas parser
denmark = client_for('denmark')
print(denmark.variables('FOLK1C'))
```

**Live access note:** The country and API references come from official provider documentation. This environment could not execute live API calls, so the new integration is locally tested with mocked responses rather than verified end to end. API deployments and paths may change. Switzerland has table-specific URLs, and the Nordic Statistics DB identifier has a space; both are flagged `special`. Metadata should always be retrieved before a data request.

## Why three adapters?

- `pxweb_v1`: GET browse and metadata; POST table data using a `query`/`response` JSON body.
- `pxweb_v2`: GET `/tables`, `/tables/{id}/metadata`, `/tables/{id}/data` with v2 dimension selectors.
- `statbank_dk`: POST `/tables`, `/tableinfo`, `/data` with the Danish API's variable selection body; outputs JSON-stat.

Eurostat supports JSON-stat2 but a different URL/filter system, so it needs an additional adapter. OECD speaks SDMX; Lithuania has a custom API. Those are **registered but not implemented**. This distinction avoids silently making invalid calls.

## After API access: standardize meaning, not just columns

Keep a table mapping each analytical indicator to a country-specific table ID, variable codes, unit, age bracket, seasonality, frequency, reference date, definition, license, and source URL. For example, country unemployment rates may differ depending on age group, survey vs registered unemployment, and seasonal adjustment. Do not calculate correlations until the matched series have been checked.

### Provider documentation

- Sweden: https://www.scb.se/en/services/open-data-api/pxwebapi/
- Iceland: https://statice.is/publications/open-data-access/
- Norway: https://www.ssb.no/en/api/pxwebapi
- Finland: https://stat.fi/en/services/statistical-data-services/open-data-and-interfaces/interface-use-of-databases
- Estonia: https://andmed.stat.ee/help/api-manual.pdf
- Latvia: https://stat.gov.lv/en/api-un-kodu-vardnicas/api-v2
- Greenland: https://statisticsgreenland.github.io/qmd/statistics_greenland.html
- Faroe Islands: https://hagstova.fo/en/terms-use
- Åland: https://pxweb.asub.ax/PXWeb/api/v1/en/Statistik
- Slovenia: https://pxweb.stat.si/sistat/en/Home/Help
- Denmark: https://www.dst.dk/en/Statistik/hjaelp-til-statistikbanken/api
- Nordic Statistics: https://www.nordicstatistics.org/about/
- Eurostat: https://ec.europa.eu/eurostat/en/web/user-guides/data-browser/api-data-access/api-introduction
- OECD: https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html
- Lithuania: https://guides.dataportal.gov.lt/docs/api
