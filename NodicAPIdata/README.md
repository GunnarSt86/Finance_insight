# Nordic Statistics API Project

A Python-first project for discovering tables in Nordic official-statistics APIs,
inspecting their metadata, and retrieving small, explicit selections as tidy
`pandas.DataFrame` objects.

The current milestone is reliable data access from notebooks. Cross-country
harmonisation, statistical analysis, and the web application come later.

## Python setup

Python 3.10 or newer is required. From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,notebook]'
python -m pytest -q
jupyter lab
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,notebook]"
```

## Notebook-facing API

```python
import nordicstats as ns

# Inspect the registry without making a network request.
display(ns.list_sources())

client = ns.client_for("iceland")
display(client.browse())

# Use a real path discovered through browse().
table = "TABLE_PATH_FROM_BROWSE"
display(client.variables(table))
display(client.value_codes(table, "VARIABLE_CODE_FROM_METADATA"))

# Every dimension must be selected with exact metadata-derived codes.
selection = {
    "VARIABLE_CODE_FROM_METADATA": ["VALUE_CODE_FROM_METADATA"],
}
df = client.fetch(table, selection)
display(df.head())
print(df.attrs)
```

Do not copy the placeholder table or value codes above into a real query. Browse
or search first, inspect metadata, and then use the codes returned by the API.
The attributes include the source, table, API URL, UTC retrieval time, selection,
and provider metadata. `DataFrame.attrs` is useful in memory but is not retained
by CSV, so save provenance separately when publishing an extract.

## Searchable table catalogues

PxWeb v2 providers and Denmark expose bounded, normalized table inventories:

```python
catalog = ns.catalog("sweden", limit=100)
population = catalog[
    catalog["title"].str.contains("population", case=False, na=False)
]
display(population)

# More efficient: ask a v2 provider to filter on the server.
population = ns.catalog("sweden", query="population", limit=100)
```

The stable columns include `source_key`, `country`, `api_family`, `table_id`,
`title`, update information, and first/last periods where supplied. Iceland and
Finland use hierarchical PxWeb v1 folders; use `client.browse()` until the
bounded recursive catalogue walker is implemented.

## Provider families

- PxWeb v1: directory browsing, table metadata, and POST data queries. Used by
  Iceland, Finland, Estonia, Greenland, the Faroe Islands, Åland, and Slovenia.
- PxWeb v2: table search, metadata, and GET data queries. Currently configured
  for Sweden, Norway, and Latvia.
- StatBank Denmark: a separate adapter for the Danish `subjects`, `tables`,
  `tableinfo`, and `data` operations.

`ns.list_sources()` reports one of four honest states:

- `working`: a small metadata and data request passed on the recorded
  `verified_on` date.
- `unverified`: configured from provider documentation but not yet tested live.
- `special`: requires provider-specific handling before normal use.
- `planned`: deliberately unavailable during this milestone.

Iceland, Sweden, Norway, Finland, and Denmark were verified end to end on
18 November 2026 using the small tables in `tests/test_live_smoke.py`. This is a
connectivity check, not evidence that every table or statistical definition is
compatible across providers.

Documented provider limits differ. Sweden currently documents 150,000 cells per
extract and 30 calls per 10 seconds; Norway documents 800,000 cells and 30 calls
per minute. The client uses a lower local default of 100,000 cells for explicit
selections where the size can be calculated.

## Tests

Offline tests never require internet access:

```bash
python -m pytest -q
```

Live tests are deliberately opt-in and issue a two-period query to each core
provider:

```bash
RUN_LIVE_API_TESTS=1 python -m pytest -q -m live
```

The verified smoke tables are Iceland `MAN00101.px`, Sweden `TAB638`, Norway
`05810`, Finland `vaerak/11ra.px`, and Denmark `FOLK1C`.

## Repository layout

```text
src/nordicstats/     installable Python package
tests/               offline tests plus explicitly marked live smoke tests
notebooks/           guided exploration notebooks
examples/            runnable Python examples
docs/                archived starter documentation and design notes
data/                generated local data (ignored by Git)
web/                 Local React/Vite Icelandic króna scale prototype
```

The original imports (`from pxweb_client import ...`, `from sources import ...`)
remain available as compatibility modules. New code should use
`import nordicstats as ns`.

## Icelandic króna scale prototype

`web/` contains a local-first concept for translating a large ISK amount into
human, public-service, and national-economic comparisons. Its reference values
are a dated snapshot of the official tables explored in
`notebooks/02_isk_scale_explorer.ipynb`; calculations run in the browser.

Start the local development version:

```bash
cd web
npm ci
npm run dev
```

Vite prints the local address, normally `http://localhost:5173`. The entered
amount is written to the URL as `?amount=...`, so a particular view can be
bookmarked or shared. To validate and preview the production build:

```bash
npm run lint
npm run build
npm run preview
```

Official statistical inputs, derived comparisons, and editable assumptions are
labelled separately in the interface. The comparison wording expresses scale;
it does not claim that a public service can literally be purchased by the day.

See [the archived starter README](docs/STARTER_README.md) and
[the multi-country notes](docs/MULTICOUNTRY.md) for the earlier implementation
notes and statistical cautions.
