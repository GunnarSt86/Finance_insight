# Nordic PxWeb Starter — Iceland + Sweden

A small, educational Python project for exploring official statistical APIs. It uses **Iceland's PxWeb v1** and **Sweden's PxWebApi v2** and returns consistent tidy pandas DataFrames.

> **Validation status (17 November 2026):** API documentation and linked tables were researched, and the code's pure-Python JSON-stat conversion is tested with local fixtures. **Live API requests could not be executed in this environment due to network/DNS restrictions.** Run the first example on your own machine. An endpoint, response format, or table selection may need adjustment if the provider differs from the documentation.

## Quick start

Python 3.10+ recommended.

```bash
cd nordic_pxweb_starter
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
python examples/01_explore_and_fetch.py
```

`examples/01_explore_and_fetch.py` writes small independent extracts to `data/`. **Those first-category preview slices are not yet directly comparable population estimates.**

## The workflow

1. **Discover**. SCB v2: `scb.search("population")`; Iceland v1: `iceland.browse("Ibuar")` (browse recursively).
2. **Inspect**. `.metadata(table)` returns original API metadata; `.variables(table)` summarizes available dimensions; `.value_codes(table, variable)` reveals valid category codes and labels.
3. **Select**. Specify one or more **codes for every variable**. Never assume codes are English labels. `example_selection()` produces a safe small preview (first code per non-time dimension, latest 5 time codes).
4. **Fetch**. `.fetch(table, selection)` returns one row per data cell and a numerical `value`, plus `status` if provided; `labels=False` preserves codes.
5. **Validate and harmonize**. Ensure both countries represent the *same concept*, period, population, geographic scope, unit and aggregation. Retain original source metadata.
6. **Analyze and display**. Use pandas for joins and growth rates, matplotlib for annotated charts, and a notebook or Streamlit for presenting results.

## API examples

```python
from pxweb_client import IcelandPxWeb, SwedenPxWeb

iceland = IcelandPxWeb()
sweden = SwedenPxWeb(language="en")

is_table = "Ibuar/mannfjoldi/1_yfirlit/Yfirlit_mannfjolda/MAN00101.px"
se_table = "TAB638"

print(iceland.browse("Ibuar/mannfjoldi/1_yfirlit/Yfirlit_mannfjolda"))
print(sweden.search("population", page_size=5))

print(iceland.variables(is_table))
print(sweden.variables(se_table))

# Discover exact codes from metadata, THEN use them:
print(iceland.value_codes(is_table, iceland.variables(is_table).iloc[0]["code"]))
print(sweden.value_codes(se_table, "Region"))

# The preview selections are valid API codes discovered from each table.
is_sample = iceland.fetch(is_table, iceland.example_selection(is_table, last_n=5))
se_sample = sweden.fetch(se_table, sweden.example_selection(se_table, last_n=5))
print(is_sample.head())
print(se_sample.head())
```

### Under the hood: the important difference

**Iceland v1**: GET metadata at `https://px.hagstofa.is/pxen/api/v1/en/{table_path}`. POST to the same path with:

```json
{
  "query": [
    {"code": "<variable-code>", "selection": {"filter": "item", "values": ["<value-code>"]}}
  ],
  "response": {"format": "json-stat2"}
}
```

(The template above only illustrates one dimension; the client specifies every dimension.)

**Sweden v2**: GET metadata at `https://statistikdatabasen.scb.se/api/v2/tables/{table_id}/metadata?lang=en`. GET data from `/tables/{table_id}/data?lang=en&outputFormat=json-stat2&valueCodes[<variable>]=<code>`. Expressions like `top(5)` and `from(2020)` can be used in v2.

Both are decoded as JSON-stat2. Iceland's implementation is expected to accept that response format because PxWeb v1 supports it in recent versions; if your local run receives an unsupported-format error, inspect the server version and use `json-stat` as a fallback (the decoder recognizes its `dataset` wrapper).  The `fetch` method requests `json-stat2` and automatically retries `json-stat` if the v1 server explicitly rejects the response format.

## Comparisons and correlations

The initial examples show you **how** to retrieve data, not a genuine population comparison. To make one, choose matching indicators such as population on equivalent reference dates, annual inflation rates, or employment rates in matching age bands.

- If using **Iceland** table `MAN00101`, note that annual population is at **1 January**. If using **Sweden** `TAB638`, population measures are at **31 December**. To compare the same reference date, Iceland's `2025` (1 Jan 2025) corresponds to Sweden's `2024` (31 Dec 2024), not Sweden's `2025`. This is a critical harmonization step.
- Do not add totals to their component categories. Check whether the metadata already includes `Total`; sum categories only when mutually exclusive and exhaustive.
- Keep `value` numeric, and retain source-specific category codes until after the join.
- Prefer year-on-year **percentage changes** for population/currency/level trends when studying comovement. Pearson correlation on levels can be inflated by shared trends. It never proves causality.
- Distinguish *rates* (already percentages) from *counts*. For rates, calculate percentage-point changes where relevant rather than growth-of-rate percentages.
- Read metadata for methodology changes and missing-value symbols (`status`).

After you have a tidy, harmonized annual series for each country, save two CSVs:

`data/iceland_matched.csv` with columns `Year,value`, and `data/sweden_matched.csv` with columns `Tid,value`. Each file must contain only one observation per year, representing the same indicator.

Then:

```bash
python examples/02_analyse_comparable_series.py
```

It will produce a matched CSV, annual changes, two descriptive correlations (level and growth), and a line chart `data/growth_comparison.png`.

## Suggested project layout

```text
nordic_pxweb_starter/
  pxweb_client.py         # reusable functions and client classes
  requirements.txt
  README.md
  examples/
    01_explore_and_fetch.py
    02_analyse_comparable_series.py
  tutorial.ipynb          # guided, interactive tutorial
  tests/
    test_client.py
  data/                   # created when running examples
```

## Documentation used

- SCB API overview: https://www.scb.se/en/services/open-data-api/pxwebapi/
- SCB v2 user guide: https://www.pxtools.net/PxWebApi/documentation/user-guide/
- SCB live Swagger: https://statistikdatabasen.scb.se/index.html
- PxWeb v2 OpenAPI specification: https://github.com/PxTools/PxApiSpecs/blob/master/PxAPI-2.yml
- Iceland open-data terms (CC BY 4.0): https://statice.is/publications/open-data-access/
- Iceland API guide: https://exchange.hagstofan.is/utgafur/leidbeiningar/talnagrunnur/um-api/
- Iceland annual population table: https://px.hagstofa.is/pxen/pxweb/en/Ibuar/Ibuar__mannfjoldi__1_yfirlit__yfirlit_mannfjolda/MAN00101.px
- Sweden population table: https://www.statistikdatabasen.scb.se/pxweb/en/ssd/START_BE_BE0101_BE0101A/BefolkningNy/

**Attribution:** Statistics Iceland data is CC BY 4.0; cite the statistical office and relevant table when using unchanged figures. Statistics Sweden's own open data uses CC0 (but some SCB-hosted tables are supplied by other agencies). Consult both offices' attribution terms before publishing derived analysis.

**No credentials required.** For larger automation, consider adding request caching, provenance logs, metadata hashes, sampling checks, and query chunking.

## Multi-country extension (2026-11-17)

See [MULTICOUNTRY.md](MULTICOUNTRY.md) for the multi-country registry, Denmark adapter, and examples.
